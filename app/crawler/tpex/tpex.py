# Standard library imports
import datetime
import warnings
from typing import List, Optional

# Third-party imports
import pandas as pd

# Local imports
from config import config
from model.data_type import DataType
from app.crawler.common.base import DataAggregator
from app.crawler.common.decorator import log_execution_time
from .util import fetch_and_process_tpex_data

warnings.simplefilter(action="ignore", category=FutureWarning)


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
    def _retrieve_all_dataframes(cls, data_date: datetime.date) -> List[pd.DataFrame]:
        """Retrieve all required dataframes for a given date."""
        return [fetch_and_process_tpex_data(data_type, data_date) 
                for data_type in cls.DATA_TYPES]
    
    @classmethod
    def _combine_dataframes(cls, dfs: List[pd.DataFrame]) -> pd.DataFrame:
        """Combine multiple dataframes on common keys."""
        combined_df = dfs[0]
        for df in dfs[1:]:
            combined_df = combined_df.merge(df, how="left", on=cls.MERGE_KEYS)
        return combined_df

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
