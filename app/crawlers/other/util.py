import json
import time
import requests
import pandas as pd

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from models.data_type import DataType
from app.utils import convert_milliseconds_to_date
from config import config, logger

MAX_REQUEST_RETRIES = 2

##### Industry Category Data #####

def _request_industry_category():
    for _ in range(MAX_REQUEST_RETRIES):
        try:
            params = {
                "dataset": "TaiwanStockInfo",
                "token": "",
            }
            response = requests.get("https://api.finmindtrade.com/api/v4/data", params=params)
            df = pd.DataFrame(response.json()["data"])
            return df
        except:
            logger.warning(f"Attempt {_request_industry_category.__name__} failed.")
            time.sleep(3)
    return pd.DataFrame(columns=config.COLUMN_KEEP_SETTING[DataType.INDUSTRY_CATEGORY])


def _clean_industry_category(df):
    # Remove leading and trailing spaces from column names
    df.columns = [column.strip() for column in df.columns]
    # Rename columns
    df = df.rename(columns=config.COLUMN_RENAME_SETTING)
    # Update the data type and remove leading and trailing spaces
    df["名稱"] = df["名稱"].astype(str).str.strip()
    df["代號"] = df["代號"].astype(str).str.strip()
    # Filter out the rows with invalid stock codes
    df = df[
        (df["代號"].str.len() == 4)
        & (df["代號"].str[:2] != "00")
        & (df["代號"].str.isdigit())
    ]
    # Only keep the columns needed
    df = df[config.COLUMN_KEEP_SETTING[DataType.INDUSTRY_CATEGORY]]
    # Sort the rows
    df = df.sort_values(by=["代號"])
    # Reset index
    df = df.reset_index(drop=True)
    return df


# Get industry category data
def get_industry_category() -> pd.DataFrame:
    df = _request_industry_category()
    df = _clean_industry_category(df)
    return df


##### MoM/YoY Data #####

def _request_mom_yoy():
    for _ in range(MAX_REQUEST_RETRIES):
        try:
            headers = {
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            }
            response = requests.get("https://stock.wespai.com/p/44850", headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            data = soup.find_all("td")
            mom_yoy_list = [
                [
                    data[x].text,
                    data[x+1].select_one("a").text,
                    data[x+3].text,
                    data[x+4].text,
                    data[x+5].text,
                ]
                for x in range(0, len(data), 6)
            ]
            df = pd.DataFrame(mom_yoy_list, columns=config.COLUMN_KEEP_SETTING[DataType.MOM_YOY])
            return df
        except:
            logger.warning(f"Attempt {_request_mom_yoy.__name__} failed.")
            time.sleep(3)
    return pd.DataFrame(columns=config.COLUMN_KEEP_SETTING[DataType.MOM_YOY])


def _clean_mom_yoy(df):
    # Update the data type and remove leading and trailing spaces
    df["名稱"] = df["名稱"].astype(str).str.strip()
    df["代號"] = df["代號"].astype(str).str.strip()
    # Convert the data type of the columns to numeric
    df = df.apply(
        lambda s: (
            pd.to_numeric(s.astype(str).str.replace(",", ""), errors="coerce")
            if s.name not in ["代號", "名稱"]
            else s
        )
    )
    # Sort the rows
    df = df.sort_values(by=["代號"])
    # Reset index
    df = df.reset_index(drop=True)
    return df


# Get latest MoM and YoY revenue growth rate data
def get_mom_yoy() -> pd.DataFrame:
    df = _request_mom_yoy()
    df = _clean_mom_yoy(df)
    return df


##### Technical Indicators Data #####

def _get_j9_list(k9_list: list, d9_list: list) -> list:
    j9_list = list()
    for (date, k9_value), (_, d9_value) in zip(k9_list, d9_list):
        j9_value = round(3 * k9_value - 2 * d9_value, 2)
        j9_list.append([date, j9_value])
    return j9_list


def _format_technical_indicator_list(technical_indicator_list: list) -> list:
    for i, (indicator_time, indicator_value) in enumerate(technical_indicator_list):
        indicator_time = convert_milliseconds_to_date(indicator_time)
        technical_indicator_list[i] = [indicator_time, indicator_value]
    return technical_indicator_list


def _format_daily_k_list(daily_k_list: list) -> list:
    for i, (k_time, *k_values) in enumerate(daily_k_list):
        k_time = convert_milliseconds_to_date(k_time)
        k_value = {
            "開盤": k_values[0],
            "最高": k_values[1],
            "最低": k_values[2],
            "收盤": k_values[3],
        }
        daily_k_list[i] = [k_time, k_value]
    return daily_k_list


def _request_technical_indicators(stock_id: str):
    for _ in range(MAX_REQUEST_RETRIES):
        try:
            headers = {
                "User-Agent": UserAgent().random,
                "authority": "histock.tw",
                "referer": f"https://histock.tw/stock/{stock_id}",
            }
            # days = 240 may causes OOM; days = 120 may miss latest data; original API uses days = 80
            response = requests.get(
                f"https://histock.tw/stock/chip/chartdata.aspx?no={stock_id}&days=80&m=dailyk,close,volume,mean5,mean10,mean20,mean60,mean5volume,mean20volume,k9,d9,dif,macd,osc",
                headers=headers,
            )
            technical_indicators = response.json()
            return technical_indicators
        except:
            if "請休息一下再試試" in response.text:
                logger.error("The web crawler has been blocked by the website...")
    return None


def _clean_technical_indicators(technical_indicators):
    if not technical_indicators:
        return None
    k9 = _format_technical_indicator_list(json.loads(technical_indicators["K9"]))
    d9 = _format_technical_indicator_list(json.loads(technical_indicators["D9"]))
    j9 = _get_j9_list(k9, d9)
    dif = _format_technical_indicator_list(json.loads(technical_indicators["DIF"]))
    macd = _format_technical_indicator_list(json.loads(technical_indicators["MACD"]))
    osc = _format_technical_indicator_list(json.loads(technical_indicators["OSC"]))
    mean5 = _format_technical_indicator_list(json.loads(technical_indicators["Mean5"]))
    mean10 = _format_technical_indicator_list(json.loads(technical_indicators["Mean10"]))
    mean20 = _format_technical_indicator_list(json.loads(technical_indicators["Mean20"]))
    mean60 = _format_technical_indicator_list(json.loads(technical_indicators["Mean60"]))
    volume = _format_technical_indicator_list(json.loads(technical_indicators["Volume"]))
    mean_5_volume = _format_technical_indicator_list(json.loads(technical_indicators["Mean5Volume"]))
    mean_20_volume = _format_technical_indicator_list(json.loads(technical_indicators["Mean20Volume"]))
    daily_k = _format_daily_k_list(json.loads(technical_indicators["DailyK"]))
    return {
        "k9": k9,
        "d9": d9,
        "j9": j9,
        "dif": dif,
        "macd": macd,
        "osc": osc,
        "mean5": mean5,
        "mean10": mean10,
        "mean20": mean20,
        "mean60": mean60,
        "volume": volume,
        "mean_5_volume": mean_5_volume,
        "mean_20_volume": mean_20_volume,
        "daily_k": daily_k,
    }


def _get_technical_indicators_by_stock_id(stock_id: str) -> dict:
    technical_indicators = _request_technical_indicators(stock_id)
    technical_indicators = _clean_technical_indicators(technical_indicators)
    return technical_indicators


# Get technical indicators data
def get_technical_indicators(reference_df: pd.DataFrame) -> pd.DataFrame:
    df = reference_df[["名稱", "代號"]].copy()
    technical_columns = [
        "k9", "d9", "j9", "dif", "macd", "osc",
        "mean5", "mean10", "mean20", "mean60",
        "volume", "mean_5_volume", "mean_20_volume", "daily_k",
    ]
    df[technical_columns] = pd.NA
    print_flag = False
    for i, row in df.iterrows():
        try:
            stock_id = row["代號"]
            technical_indicators = _get_technical_indicators_by_stock_id(stock_id)
            for col in technical_columns:
                df.at[i, col] = technical_indicators.get(col)
            if (i+1) % 100 == 0 or print_flag:
                print_flag = False
                logger.info(f"Processed technical data: {i+1}/{len(df.index)}, stock_id = {stock_id}")
        except:
            if (i+1) % 100 == 0:
                print_flag = True
    return df