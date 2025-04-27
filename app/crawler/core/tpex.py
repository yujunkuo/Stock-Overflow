# Standard library imports
import datetime
import warnings
from dataclasses import dataclass
from io import StringIO
from typing import Dict, List, Optional

# Third-party imports
import pandas as pd
import requests

# Local imports
from app.crawler.common.base import ApiEndpointConfig, DataFetcher, DataProcessor, DataAggregator
from app.crawler.common.decorators import retry_on_failure, log_execution_time
from config import config, logger
from model.data_type import DataType

warnings.simplefilter(action="ignore", category=FutureWarning)


@dataclass
class TPEXApiEndpointConfig(ApiEndpointConfig):
    """Configuration for TPEX API endpoints."""
    headers: Dict[str, str]
    encoding: str
    header_row: Optional[int]


class TPEXDataFetcher(DataFetcher):
    """Class to handle API requests to TPEX."""
    
    # Class-level configuration
    API_ENDPOINTS: Dict[DataType, TPEXApiEndpointConfig] = {
        DataType.PRICE: TPEXApiEndpointConfig(
            url="https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php?l=zh-tw&o=csv&charset=UTF-8&d={date_str}&se=AL",
            headers={"Host": "www.tpex.org.tw"},
            encoding="big5",
            header_row=3
        ),
        DataType.FUNDAMENTAL: TPEXApiEndpointConfig(
            url="https://www.tpex.org.tw/web/stock/aftertrading/peratio_analysis/pera_result.php?l=zh-tw&o=csv&charset=UTF-8&d={date_str}",
            headers={"Host": "www.tpex.org.tw"},
            encoding="big5",
            header_row=3
        ),
        DataType.MARGIN_TRADING: TPEXApiEndpointConfig(
            url="https://www.tpex.org.tw/web/stock/margin_trading/margin_balance/margin_bal_result.php?l=zh-tw&o=csv&charset=UTF-8&d={date_str}",
            headers={"Host": "www.tpex.org.tw"},
            encoding="big5",
            header_row=2
        ),
        DataType.INSTITUTIONAL: TPEXApiEndpointConfig(
            url="https://www.tpex.org.tw/web/stock/3insti/daily_trade/3itrade_hedge_result.php?l=zh-tw&o=csv&d={date_str}&t=D",
            headers={"Host": "www.tpex.org.tw"},
            encoding="big5",
            header_row=1
        ),
    }
    
    @staticmethod
    def _format_date_for_api(data_date: datetime.date) -> str:
        """Format date for TPEX API request."""
        year, month, day = data_date.year - 1911, data_date.month, data_date.day
        return f"{year}/{month:02}/{day:02}"
    
    @classmethod
    @retry_on_failure(
        max_retries=3,
        fallback=lambda cls, data_type, data_date: (
            logger.warning(f"{cls.__name__} fetch failed for data type: {data_type.value}") or
            pd.DataFrame(columns=config.COLUMN_KEEP_SETTING[data_type])
        )
    )
    def fetch_data(cls, data_type: DataType, data_date: datetime.date) -> pd.DataFrame:
        """Fetch data from TPEX API with retry mechanism."""
        endpoint_config = cls.API_ENDPOINTS.get(data_type)
        date_str = cls._format_date_for_api(data_date)
        url = endpoint_config.url.format(date_str=date_str)

        response = requests.get(url, headers=endpoint_config.headers)
        response.encoding = endpoint_config.encoding
        response.raise_for_status()

        return pd.read_csv(StringIO(response.text), header=endpoint_config.header_row)


class TPEXDataProcessor(DataProcessor):
    """Class to handle TPEX data processing operations."""
    
    # Class-level configuration
    STOCK_TYPE = "tpex"

    @classmethod
    def process_data(cls, data_type: DataType, df: pd.DataFrame) -> pd.DataFrame:
        """Process TPEX data for a specific type."""
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


class TPEXDataAggregator(DataAggregator):
    """Class to handle TPEX data aggregating for different data types."""
    
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
        """Fetch and process TPEX data for a specific type and date."""
        df = TPEXDataFetcher.fetch_data(data_type, data_date)
        return TPEXDataProcessor.process_data(data_type, df)
    
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
    @log_execution_time(log_message="取得上櫃資料表花費時間")
    def aggregate_data(cls, data_date: datetime.date) -> Optional[pd.DataFrame]:
        """Aggregate all TPEX data for a given date."""
        # Retrieve dataframes for all data types
        dfs = cls._retrieve_all_dataframes(data_date)
        
        # Combine dataframes
        df = cls._combine_dataframes(dfs)
        
        # Fill missing values for all data types
        df = cls._fill_missing_values(df)
            
        # Set index
        df = df.set_index("代號")
        
        return df


def get_tpex_data(data_date: datetime.date) -> Optional[pd.DataFrame]:
    """Get final aggregated TPEX data for a given date."""
    return TPEXDataAggregator.aggregate_data(data_date)