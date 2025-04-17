# Standard library imports
import datetime
from dataclasses import dataclass
from io import StringIO
from typing import Dict, Callable, Optional

# Third-party imports
import pandas as pd
import requests

# Local imports
from app.crawler.common.base import DataFetcher, DataProcessor, ApiEndpointConfig
from app.crawler.common.decorator import retry_on_failure
from config import config, logger
from model.data_type import DataType


@dataclass
class TWSEApiEndpointConfig(ApiEndpointConfig):
    """Configuration for TWSE API endpoints."""
    special_header_detection: Optional[Callable[[str], int]] = None


class TWSEDataFetcher(DataFetcher):
    """Class to handle API requests to TWSE."""
    
    # Class-level configuration
    API_ENDPOINTS: Dict[DataType, TWSEApiEndpointConfig] = {
        DataType.PRICE: TWSEApiEndpointConfig(
            url="https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={date_str}&type=ALL",
            header_row=None,
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
    def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names and values."""
        df.columns = df.columns.str.strip()
        df = df.rename(columns=config.COLUMN_RENAME_SETTING)
        
        df["名稱"] = df["名稱"].astype(str).str.strip()
        df["代號"] = df["代號"].astype(str).str.strip()
        
        # Exclude non-regular stocks such as ETFs
        df = df[df["代號"].str.match(r"^[1-9]\d{3}$")]
        
        return df

    @classmethod
    def _convert_to_numeric(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Convert columns to numeric where applicable."""
        def convert_col(series):
            if series.name in cls.NON_NUMERIC_COLUMNS:
                return series
            
            # Convert strings to numeric, replacing commas
            return pd.to_numeric(
                series.astype(str).str.replace(",", ""),
                errors="coerce"
            )
            
        return df.apply(convert_col)

    @staticmethod
    def _process_price_data(df: pd.DataFrame) -> pd.DataFrame:
        """Process price specific data."""
        df["漲跌(+/-)"] = df["漲跌(+/-)"].map({"+": 1, "-": -1}).fillna(0)
        df["漲跌"] = df["漲跌(+/-)"] * df["漲跌價差"]
        df["成交量"] = (df["成交量"] / 1000).round()
        return df

    @staticmethod
    def _process_margin_trading_data(df: pd.DataFrame) -> pd.DataFrame:
        """Process margin trading specific data."""
        df["融資變化量"] = df["融資買進"] - df["融資賣出"] - df["現金償還"]
        df["融券變化量"] = df["融券賣出"] - df["融券買進"] - df["現券償還"]

        df["券資比(%)"] = (df["融券餘額"] / df["融資餘額"].replace(0, pd.NA)).fillna(0) * 100
        df["券資比(%)"] = df["券資比(%)"].round(2)
        
        return df

    @staticmethod
    def _process_institutional_data(df: pd.DataFrame) -> pd.DataFrame:
        """Process institutional specific data."""
        columns = ["外資買賣超", "投信買賣超", "自營商買賣超", "三大法人買賣超"]
        df[columns] = (df[columns] / 1000).round()
        
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


def fetch_and_process_twse_data(data_type: DataType, data_date: datetime.date) -> pd.DataFrame:
    """Fetch and process TWSE data."""
    df = TWSEDataFetcher.fetch_data(data_type, data_date)
    return TWSEDataProcessor.process_data(data_type, df)