# Standard library imports
import datetime
import warnings
from typing import List, Optional

# Third-party imports
import pandas as pd

# Local imports
from model.data_type import DataType
from app.crawler.common.base import DataAggregator
from app.crawler.common.decorator import log_execution_time
from .util import (
    fetch_and_process_industry_category,
    fetch_and_process_mom_yoy,
    fetch_and_process_technical_indicators,
)

warnings.simplefilter(action="ignore", category=FutureWarning)


class OtherDataAggregator(DataAggregator):
    """Class to handle other data aggregating for different data types."""
    
    # Class-level configuration
    MERGE_KEYS = ["代號", "名稱"]
    
    @classmethod
    def _retrieve_all_dataframes(cls, data_date: datetime.date) -> List[pd.DataFrame]:
        """Retrieve all required dataframes for a given date."""
        # Get industry category data
        industry_category_df = fetch_and_process_industry_category(DataType.INDUSTRY_CATEGORY)
        
        # Get MoM/YoY data
        mom_yoy_df = fetch_and_process_mom_yoy(DataType.MOM_YOY)
        
        # Get technical indicators data
        technical_indicators_df = fetch_and_process_technical_indicators(industry_category_df, data_date)
        
        return [industry_category_df, mom_yoy_df, technical_indicators_df]
    
    @classmethod
    @log_execution_time(log_message="取得其他資料表花費時間")
    def aggregate_data(cls, data_date: datetime.date) -> Optional[pd.DataFrame]:
        """Aggregate all other data for a given date."""
        # Retrieve dataframes for all data types
        dfs = cls._retrieve_all_dataframes(data_date)
            
        # Combine dataframes
        df = cls._combine_dataframes(dfs)
            
        # Set index
        df = df.set_index("代號")
        
        return df


def get_other_data(data_date: datetime.date) -> Optional[pd.DataFrame]:
    """Get final aggregated other data for a given date."""
    return OtherDataAggregator.aggregate_data(data_date)
