import time
import datetime
import warnings
import pandas as pd

from .util import get_data
from config import config, logger
from models.data_type import DataType

warnings.simplefilter(action="ignore", category=FutureWarning)

# TODO: Error handling

# (Public) Get the final data of TWSE
def get_twse_data(data_date):
    start_time = time.time()
    price_df = get_data(DataType.PRICE, data_date)
    fundamental_df = get_data(DataType.FUNDAMENTAL, data_date)
    margin_trading_df = get_data(DataType.MARGIN_TRADING, data_date)
    institutional_df = get_data(DataType.INSTITUTIONAL, data_date)
    try:
        # Merge all data
        df = pd.merge(price_df, fundamental_df, how="left", on=["代號", "名稱", "股票類型"])
        df = pd.merge(df, margin_trading_df, how="left", on=["代號", "名稱", "股票類型"])
        df = pd.merge(df, institutional_df, how="left", on=["代號", "名稱", "股票類型"])
        # Fill zero for those without institutional data
        df[config.COLUMN_KEEP_SETTING[DataType.INSTITUTIONAL]] = df[config.COLUMN_KEEP_SETTING[DataType.INSTITUTIONAL]].fillna(value=0)
        # Set index
        df = df.set_index("代號")
        end_time = time.time()
        time_spent = end_time - start_time
        logger.info(f"取得上市資料表花費時間: {datetime.timedelta(seconds=int(time_spent))}")
        return df
    except:
        logger.error("無法取得上市資料表")
        return None
