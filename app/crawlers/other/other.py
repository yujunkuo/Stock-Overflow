import time
import datetime
import pandas as pd

from config import logger
from .util import (
    get_industry_category,
    get_mom_yoy,
    get_technical_indicators
)


# (Public) Get other data: industry category, MoM/YoY, and technical indicators
def get_other_data(data_date):
    start_time = time.time()
    industry_category_df = get_industry_category()
    mom_yoy_df = get_mom_yoy()
    technical_indicators_df = get_technical_indicators(industry_category_df, data_date)
    try:
        # Merge all data
        df = pd.merge(industry_category_df, mom_yoy_df, how="left", on=["代號", "名稱"])
        df = pd.merge(df, technical_indicators_df, how="left", on=["代號", "名稱"])
        # Set index
        df = df.set_index("代號")
        end_time = time.time()
        time_spent = end_time - start_time
        logger.info(f"取得其他資料表花費時間: {datetime.timedelta(seconds=int(time_spent))}")
        return df
    except:
        logger.error("無法取得其他資料表")
        return None
