import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, ".."))

from config import logger

import datetime
import time

import pandas as pd

import warnings
import util

from model.data_type import DataType

warnings.simplefilter(action="ignore", category=FutureWarning)

MAX_REQUEST_RETRIES = 5

# TODO: Error handling


# (Public) Get the final data of TWSE
def get_twse_final(date):
    start_time = time.time()
    price_df = _get_twse_price(date)
    fundamental_df = _get_twse_fundamental(date)
    margin_trading_df = _get_twse_margin_trading(date)
    institutional_df = _get_twse_institutional(date)
    try:
        # Merge all data
        df = pd.merge(price_df, fundamental_df, how="left", on=["代號", "名稱", "股票類型"])
        df = pd.merge(df, margin_trading_df, how="left", on=["代號", "名稱", "股票類型"])
        df = pd.merge(df, institutional_df, how="left", on=["代號", "名稱", "股票類型"])
        # Fill zero for those without institutional data
        df[util.COLUMN_KEEP_SETTING[DataType.INSTITUTIONAL]] = df[util.COLUMN_KEEP_SETTING[DataType.INSTITUTIONAL]].fillna(value=0)
        # Set index
        df = df.set_index("代號")
        end_time = time.time()
        time_spent = end_time - start_time
        logger.info(f"取得上市資料表花費時間: {datetime.timedelta(seconds=int(time_spent))}")
        return df
    except:
        logger.error("無法取得上市資料表")
        return None


# Get the price data of TWSE
def _get_twse_price(date) -> pd.DataFrame:
    for _ in range(MAX_REQUEST_RETRIES):
        try:
            price_raw_data = util.get_twse_data(DataType.PRICE, date)
            price_df = util.clean_twse_data(DataType.PRICE, price_raw_data)
            return price_df
        except:
            logger.warning(f"Attempt {_get_twse_price.__name__} failed.")
            time.sleep(3)
    return pd.DataFrame(columns=util.COLUMN_KEEP_SETTING[DataType.PRICE])


# Get the fundamental data of TWSE
def _get_twse_fundamental(date) -> pd.DataFrame:
    for _ in range(MAX_REQUEST_RETRIES):
        try:
            fundamental_raw_data = util.get_twse_data(DataType.FUNDAMENTAL, date)
            fundamental_df = util.clean_twse_data(DataType.FUNDAMENTAL, fundamental_raw_data)
            return fundamental_df
        except:
            logger.warning(f"Attempt {_get_twse_fundamental.__name__} failed.")
            time.sleep(3)
    return pd.DataFrame(columns=util.COLUMN_KEEP_SETTING[DataType.FUNDAMENTAL])


# Get the margin trading data of TWSE
def _get_twse_margin_trading(date) -> pd.DataFrame:
    for _ in range(MAX_REQUEST_RETRIES):
        try:
            margin_trading_raw_data = util.get_twse_data(DataType.MARGIN_TRADING, date)
            margin_trading_df = util.clean_twse_data(DataType.MARGIN_TRADING, margin_trading_raw_data)
            return margin_trading_df
        except:
            logger.warning(f"Attempt {_get_twse_margin_trading.__name__} failed.")
            time.sleep(3)
    return pd.DataFrame(columns=util.COLUMN_KEEP_SETTING[DataType.MARGIN_TRADING])


# Get the institutional data of TWSE
def _get_twse_institutional(date) -> pd.DataFrame:
    for _ in range(MAX_REQUEST_RETRIES):
        try:
            institutional_raw_data = util.get_twse_data(DataType.INSTITUTIONAL, date)
            institutional_df = util.clean_twse_data(DataType.INSTITUTIONAL, institutional_raw_data)
            return institutional_df
        except:
            logger.warning(f"Attempt {_get_twse_institutional.__name__} failed.")
            time.sleep(3)
    return pd.DataFrame(columns=util.COLUMN_KEEP_SETTING[DataType.INSTITUTIONAL])