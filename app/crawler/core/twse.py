# Standard library imports
import datetime
import warnings
from dataclasses import dataclass
from io import StringIO
from typing import Dict, List, Callable, Optional

# Third-party imports
import pandas as pd
import requests

# Local imports
from app.crawler.common.base import ApiEndpointConfig, DataFetcher, DataProcessor, DataAggregator
from app.crawler.common.decorator import retry_on_failure, log_execution_time
from config import config, logger
from model.data_type import DataType

warnings.simplefilter(action="ignore", category=FutureWarning)


@dataclass
class TWSEApiEndpointConfig(ApiEndpointConfig):
    """Configuration for TWSE API endpoints."""
    header_row: Optional[int] = None
    special_header_detection: Optional[Callable[[str], int]] = None


class TWSEDataFetcher(DataFetcher):
    """Class to handle API requests to TWSE."""
    
    # Class-level configuration
    API_ENDPOINTS: Dict[DataType, TWSEApiEndpointConfig] = {
        DataType.PRICE: TWSEApiEndpointConfig(
            url="https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={date_str}&type=ALL",
            special_header_detection=lambda text: ["證券代號" in line for line in text.split("\n")].index(True) - 1
        ),
        DataType.FUNDAMENTAL: TWSEApiEndpointConfig(
            url="https://www.twse.com.tw/exchangeReport/BWIBBU_d?response=csv&date={date_str}&selectType=ALL",
            header_row=1
        ),
        DataType.MARGIN_TRADING: TWSEApiEndpointConfig(
            url="https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN?response=csv&date={date_str}&selectType=ALL",
            header_row=7
        ),
        DataType.INSTITUTIONAL: TWSEApiEndpointConfig(
            url="https://www.twse.com.tw/rwd/zh/fund/T86?response=csv&date={date_str}&selectType=ALL",
            header_row=1
        ),
    }
    
    @staticmethod
    def _format_date_for_api(data_date: datetime.date) -> str:
        """Format date for TWSE API request."""
        year, month, day = data_date.year, data_date.month, data_date.day
        return f"{year}{month:02}{day:02}"
    
    @staticmethod
    def _determine_header_row(response_text: str, endpoint_config: TWSEApiEndpointConfig) -> int:
        """Determine the correct header row for the response."""
        if endpoint_config.special_header_detection:
            return endpoint_config.special_header_detection(response_text)
        return endpoint_config.header_row
    
    @classmethod
    @retry_on_failure(
        max_retries=3,
        fallback=lambda cls, data_type, data_date: (
            logger.warning(f"{cls.__name__} fetch failed for data type: {data_type.value}") or
            pd.DataFrame(columns=config.COLUMN_KEEP_SETTING[data_type])
        )
    )
    def fetch_data(cls, data_type: DataType, data_date: datetime.date) -> pd.DataFrame:
        """Fetch data from TWSE API with retry mechanism."""
        endpoint_config = cls.API_ENDPOINTS.get(data_type)
        date_str = cls._format_date_for_api(data_date)
        url = endpoint_config.url.format(date_str=date_str)

        response = requests.get(url)
        response.raise_for_status()

        header_row = cls._determine_header_row(response.text, endpoint_config)
        
        return pd.read_csv(StringIO(response.text.replace("=", "")), header=header_row)


class TWSEDataProcessor(DataProcessor):
    """Class to handle TWSE data processing operations."""
    
    # Class-level configuration
    NON_NUMERIC_COLUMNS = ["代號", "名稱", "漲跌(+/-)"]
    STOCK_TYPE = "twse"

    @staticmethod
    def _process_price_data(df: pd.DataFrame) -> pd.DataFrame:
        """Process price specific data."""
        df["漲跌(+/-)"] = df["漲跌(+/-)"].map({"+": 1, "-": -1}).fillna(0)
        df["漲跌"] = df["漲跌(+/-)"] * df["漲跌價差"]
        df["成交量"] = (df["成交量"] / 1000).round()
        return df

    @classmethod
    def process_data(cls, data_type: DataType, df: pd.DataFrame) -> pd.DataFrame:
        """Process TWSE data for a specific type."""
        if df.empty:
            return df
        
        # Standardize column names and values
        df = cls._standardize_columns(df)
        
        # Convert columns to numeric where applicable
        df = cls._convert_to_numeric(df)
        
        # Apply type-specific processing
        processing_methods = {
            DataType.PRICE: cls._process_price_data,
            DataType.MARGIN_TRADING: cls._process_margin_trading_data,
            DataType.INSTITUTIONAL: cls._process_institutional_data
        }
        
        if data_type in processing_methods:
            df = processing_methods.get(data_type)(df)
            
        # Add stock type
        df["股票類型"] = cls.STOCK_TYPE
        
        # Keep only columns defined in config settings for this data type
        df = df[df.columns.intersection(config.COLUMN_KEEP_SETTING[data_type])]
        
        # Sort and reset index
        return df.sort_values(by=["代號"]).reset_index(drop=True)


class TWSEDataAggregator(DataAggregator):
    """Class to handle TWSE data aggregating for different data types."""
    
    # Class-level configuration
    MERGE_KEYS = ["代號", "名稱", "股票類型"]
    DATA_TYPES = [
        DataType.PRICE,
        DataType.FUNDAMENTAL,
        DataType.MARGIN_TRADING,
        DataType.INSTITUTIONAL,
    ]
    
    @classmethod
    def _fetch_and_process_data(cls, data_type: DataType, data_date: datetime.date) -> pd.DataFrame:
        """Fetch and process TWSE data for a specific type and date."""
        df = TWSEDataFetcher.fetch_data(data_type, data_date)
        return TWSEDataProcessor.process_data(data_type, df)

    @classmethod
    def _retrieve_all_dataframes(cls, data_date: datetime.date) -> List[pd.DataFrame]:
        """Retrieve all required dataframes for a given date."""
        return [cls._fetch_and_process_data(data_type, data_date) 
                for data_type in cls.DATA_TYPES]

    @classmethod
    def _fill_missing_values(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Fill missing values for all data types after merging."""
        # Fill missing values for institutional data
        institutional_columns = df.columns.intersection(config.COLUMN_KEEP_SETTING[DataType.INSTITUTIONAL])
        df[institutional_columns] = df[institutional_columns].fillna(value=0)
        return df
    
    @classmethod
    @log_execution_time(log_message="取得上市資料表花費時間")
    def aggregate_data(cls, data_date: datetime.date) -> Optional[pd.DataFrame]:
        """Aggregate all TWSE data for a given date."""
        # Retrieve dataframes for all data types
        dfs = cls._retrieve_all_dataframes(data_date)
        
        # Combine dataframes
        df = cls._combine_dataframes(dfs)
        
        # Fill missing values for all data types
        df = cls._fill_missing_values(df)
            
        # Set index
        df = df.set_index("代號")
        
        return df


def get_twse_data(data_date: datetime.date) -> Optional[pd.DataFrame]:
    """Get final aggregated TWSE data for a given date."""
    return TWSEDataAggregator.aggregate_data(data_date)