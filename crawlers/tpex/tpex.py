import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, ".."))

import time
import datetime

import warnings
import pandas as pd

from config import logger, COLUMN_KEEP_SETTING
from model.data_type import DataType
from .util import get_tpex_data, clean_tpex_data

warnings.simplefilter(action="ignore", category=FutureWarning)

MAX_REQUEST_RETRIES = 5


# (Public) Get the final data of TPEX
def get_tpex_final(date):
    start_time = time.time()
    price_df = _get_tpex_price(date)
    fundamental_df = _get_tpex_fundamental(date)
    margin_trading_df = _get_tpex_margin_trading(date)
    institutional_df = _get_tpex_institutional(date)
    try:
        # Merge all data
        df = pd.merge(price_df, fundamental_df, how="left", on=["代號", "名稱", "股票類型"])
        df = pd.merge(df, margin_trading_df, how="left", on=["代號", "名稱", "股票類型"])
        df = pd.merge(df, institutional_df, how="left", on=["代號", "名稱", "股票類型"])
        # Fill zero for those without institutional data
        df[COLUMN_KEEP_SETTING[DataType.INSTITUTIONAL]] = df[COLUMN_KEEP_SETTING[DataType.INSTITUTIONAL]].fillna(value=0)
        # Set index
        df = df.set_index("代號")
        end_time = time.time()
        time_spent = end_time - start_time
        logger.info(f"取得上櫃資料表花費時間: {datetime.timedelta(seconds=int(time_spent))}")
        return df
    except:
        logger.error("無法取得上櫃資料表")
        return None


# Get the price data of TPEX
def _get_tpex_price(date) -> pd.DataFrame:
    for _ in range(MAX_REQUEST_RETRIES):
        try:
            price_raw_data = get_tpex_data(DataType.PRICE, date)
            price_df = clean_tpex_data(DataType.PRICE, price_raw_data)
            return price_df
        except:
            logger.warning(f"Attempt {_get_tpex_price.__name__} failed.")
            time.sleep(3)
    return pd.DataFrame(columns=COLUMN_KEEP_SETTING[DataType.PRICE])


# Get the fundamental data of TPEX
def _get_tpex_fundamental(date) -> pd.DataFrame:
    for _ in range(MAX_REQUEST_RETRIES):
        try:
            fundamental_raw_data = get_tpex_data(DataType.FUNDAMENTAL, date)
            fundamental_df = clean_tpex_data(DataType.FUNDAMENTAL, fundamental_raw_data)
            return fundamental_df
        except:
            logger.warning(f"Attempt {_get_tpex_fundamental.__name__} failed.")
            time.sleep(3)
    return pd.DataFrame(columns=COLUMN_KEEP_SETTING[DataType.FUNDAMENTAL])


# Get the margin trading data of TPEX
def _get_tpex_margin_trading(date) -> pd.DataFrame:
    for _ in range(MAX_REQUEST_RETRIES):
        try:
            margin_trading_raw_data = get_tpex_data(DataType.MARGIN_TRADING, date)
            margin_trading_df = clean_tpex_data(DataType.MARGIN_TRADING, margin_trading_raw_data)
            return margin_trading_df
        except:
            logger.warning(f"Attempt {_get_tpex_margin_trading.__name__} failed.")
            time.sleep(3)
    return pd.DataFrame(columns=COLUMN_KEEP_SETTING[DataType.MARGIN_TRADING])


# Get the institutional data of TPEX
def _get_tpex_institutional(date) -> pd.DataFrame:
    for _ in range(MAX_REQUEST_RETRIES):
        try:
            institutional_raw_data = get_tpex_data(DataType.INSTITUTIONAL, date)
            institutional_df = clean_tpex_data(DataType.INSTITUTIONAL, institutional_raw_data)
            return institutional_df
        except:
            logger.warning(f"Attempt {_get_tpex_institutional.__name__} failed.")
            time.sleep(3)
    return pd.DataFrame(columns=COLUMN_KEEP_SETTING[DataType.INSTITUTIONAL])

# TODO: Is import path right?