from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
import datetime
import pandas as pd
from model.data_type import DataType


@dataclass
class ApiEndpointConfig:
    """Base configuration for API endpoints."""
    url: str
    header_row: Optional[int]


class DataFetcher(ABC):
    """Abstract base class for data fetching operations."""
    
    @abstractmethod
    def _format_date_for_api(self, data_date: datetime.date) -> str:
        """Format date for API request."""
        pass
    
    @abstractmethod
    def fetch_data(self, data_type: DataType, data_date: datetime.date) -> pd.DataFrame:
        """Fetch data from API."""
        pass


class DataProcessor(ABC):
    """Abstract base class for data processing operations."""
    
    NON_NUMERIC_COLUMNS = ["代號", "名稱"]
    
    @abstractmethod
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names and values."""
        pass
    
    @classmethod
    def _convert_to_numeric(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Convert columns to numeric where applicable."""
        def convert_col(series):
            if series.name in cls.NON_NUMERIC_COLUMNS:
                return series
            
            return pd.to_numeric(
                series.astype(str).str.replace(",", ""),
                errors="coerce"
            )
            
        return df.apply(convert_col)
    
    @staticmethod
    def _process_price_data(df: pd.DataFrame) -> pd.DataFrame:
        """Process price specific data."""
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
    
    @abstractmethod
    def process_data(self, data_type: DataType, df: pd.DataFrame) -> pd.DataFrame:
        """Process data for a specific type."""
        pass


class DataAggregator(ABC):
    """Abstract base class for data aggregation operations."""
    
    MERGE_KEYS = ["代號", "名稱", "股票類型"]
    DATA_TYPES = [
        DataType.PRICE,
        DataType.FUNDAMENTAL,
        DataType.MARGIN_TRADING,
        DataType.INSTITUTIONAL,
    ]
    
    @abstractmethod
    def _retrieve_all_dataframes(self, data_date: datetime.date) -> List[pd.DataFrame]:
        """Retrieve all required dataframes for a given date."""
        pass
    
    @classmethod
    def _combine_dataframes(cls, dfs: List[pd.DataFrame]) -> pd.DataFrame:
        """Combine multiple dataframes on common keys."""
        combined_df = dfs[0]
        for df in dfs[1:]:
            combined_df = combined_df.merge(df, how="left", on=cls.MERGE_KEYS)
        return combined_df
    
    @abstractmethod
    def _fill_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill missing values for all data types after merging."""
        pass
    
    @abstractmethod
    def aggregate_data(self, data_date: datetime.date) -> Optional[pd.DataFrame]:
        """Aggregate all data for a given date."""
        pass 