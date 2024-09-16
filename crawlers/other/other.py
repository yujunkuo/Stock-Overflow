import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, ".."))

from config import logger

import datetime
import json
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from .util import get_daily_k_pretty_list, get_technical_indicator_pretty_list

MAX_REQUEST_RETRIES = 2


# (Public) Get industry category from FinMind
def get_industry_category() -> pd.DataFrame:
    for _ in range(MAX_REQUEST_RETRIES):
        try:
            parameter = {
                "dataset": "TaiwanStockInfo",
                "token": "",
            }
            r = requests.get(
                "https://api.finmindtrade.com/api/v4/data", params=parameter
            )
            data = r.json()
            df = pd.DataFrame(data["data"])
            # Remove leading and trailing spaces from column names
            df.columns = [column.strip() for column in df.columns]
            # Rename columns
            df = df.rename(
                columns={
                    "industry_category": "產業別",
                    "stock_id": "代號",
                    "stock_name": "名稱",
                    "type": "股票類型",
                }
            )
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
            df = df[["代號", "名稱", "產業別", "股票類型"]]
            df = df.set_index("代號")
            return df
        except:
            logger.warning(f"Attempt {get_industry_category.__name__} failed.")
            time.sleep(3)
    return pd.DataFrame(columns=["代號", "名稱", "產業別", "股票類型"]).set_index("代號")


# (Public) Get the latest MoM and YoY revenue growth rate
def get_mom_yoy() -> pd.DataFrame:
    for _ in range(MAX_REQUEST_RETRIES):
        try:
            headers = {
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            }
            r = requests.get("https://stock.wespai.com/p/44850", headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")
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
            df = pd.DataFrame(
                mom_yoy_list,
                columns=[
                    "代號",
                    "名稱",
                    "(月)營收月增率(%)",
                    "(月)營收年增率(%)",
                    "(月)累積營收年增率(%)",
                ],
            )
            # Convert the data type of the columns to numeric
            df = df.apply(
                lambda s: (
                    pd.to_numeric(s.astype(str).str.replace(",", ""), errors="coerce")
                    if s.name not in ["代號", "名稱"]
                    else s
                )
            )
            # Update the data type and remove leading and trailing spaces
            df["名稱"] = df["名稱"].astype(str).str.strip()
            df["代號"] = df["代號"].astype(str).str.strip()
            df = df.set_index("代號")
            df = df.sort_index()
            return df
        except:
            logger.warning(f"Attempt {get_mom_yoy.__name__} failed.")
            time.sleep(3)
    return pd.DataFrame(
        columns=[
            "代號",
            "名稱",
            "(月)營收月增率(%)",
            "(月)營收年增率(%)",
            "(月)累積營收年增率(%)",
        ]
    ).set_index("代號")


# (Public) Add technical indicators to the input DataFrame
def get_technical_indicators(input_df: pd.DataFrame) -> pd.DataFrame:
    df = input_df.copy()
    start_time_ = time.time()
    new_column_list = [
        "k9",
        "d9",
        "j9",
        "dif",
        "macd",
        "osc",
        "mean5",
        "mean10",
        "mean20",
        "mean60",
        "volume",
        "mean_5_volume",
        "mean_20_volume",
        "daily_k",
    ]
    df[new_column_list] = None
    df[
        [
            "k9",
            "d9",
            "j9",
            "dif",
            "macd",
            "osc",
            "mean5",
            "mean10",
            "mean20",
            "mean60",
            "volume",
            "mean_5_volume",
            "mean_20_volume",
            "daily_k",
        ]
    ] = df[
        [
            "k9",
            "d9",
            "j9",
            "dif",
            "macd",
            "osc",
            "mean5",
            "mean10",
            "mean20",
            "mean60",
            "volume",
            "mean_5_volume",
            "mean_20_volume",
            "daily_k",
        ]
    ].astype(
        "object"
    )
    # Check if the last date of the data is today (from TSMC)
    # test_data = _get_technical_indicators_from_stock_id("2330")
    # test_date = test_data["daily_k"][-1][0]
    # if test_date != datetime.date.today():
    #     logger.warning("取得技術指標失敗，搜尋日期與今日日期不相符")
    #     return df
    current_finish_, total_ = 0, len(df.index)
    print_flag = False
    for i, row in df.iterrows():
        try:
            technical_data = _get_technical_indicators_from_stock_id(i)
            for each in new_column_list:
                df.loc[[str(i)], each] = [technical_data[each]]
            current_finish_ += 1
            if print_flag or current_finish_ % 100 == 0:
                logger.info(
                    f"Finish technical data: {current_finish_}/{total_}, index = {i}"
                )
                print_flag = False
        except:
            current_finish_ += 1
            if current_finish_ % 100 == 0:
                print_flag = True
    end_time_ = time.time()
    spent_time_ = end_time_ - start_time_
    logger.info(f"取得技術指標花費時間: {datetime.timedelta(seconds=int(spent_time_))}")
    return df


# Get technical indicators from the stock ID
def _get_technical_indicators_from_stock_id(stock_id: str) -> dict:
    for _ in range(max(1, MAX_REQUEST_RETRIES - 1)):
        try:
            # days = 240 時 Render 記憶體會爆掉
            # days = 120 時有時會抓不到最新一天的資料 (原始網站打 API 時使用的是 days = 80)
            # r = requests.get(f"https://histock.tw/stock/chip/chartdata.aspx?no={stock_id}&days=240&m=dailyk,close,volume,mean5,mean10,mean20,mean60,mean120,mean5volume,mean20volume,k9,d9,rsi6,rsi12,dif,macd,osc")
            # r = requests.get(f"https://histock.tw/stock/chip/chartdata.aspx?no={stock_id}&days=120&m=dailyk,close,volume,mean5,mean10,mean20,mean60,mean5volume,mean20volume,k9,d9,dif,macd,osc")
            headers = {
                "User-Agent": UserAgent().random,
                "authority": "histock.tw",
                "referer": f"https://histock.tw/stock/{stock_id}",
            }
            r = requests.get(
                f"https://histock.tw/stock/chip/chartdata.aspx?no={stock_id}&days=80&m=dailyk,close,volume,mean5,mean10,mean20,mean60,mean5volume,mean20volume,k9,d9,dif,macd,osc",
                headers=headers,
            )
            technical_data = r.json()
            k9 = get_technical_indicator_pretty_list(json.loads(technical_data["K9"]))
            d9 = get_technical_indicator_pretty_list(json.loads(technical_data["D9"]))
            j9 = [
                [date_k, round(3 * value_k - 2 * value_d, 2)]
                for (date_k, value_k), (date_d, value_d) in zip(k9, d9)
            ]
            dif = get_technical_indicator_pretty_list(json.loads(technical_data["DIF"]))
            macd = get_technical_indicator_pretty_list(json.loads(technical_data["MACD"]))
            osc = get_technical_indicator_pretty_list(json.loads(technical_data["OSC"]))
            mean5 = get_technical_indicator_pretty_list(json.loads(technical_data["Mean5"]))
            mean10 = get_technical_indicator_pretty_list(json.loads(technical_data["Mean10"]))
            mean20 = get_technical_indicator_pretty_list(json.loads(technical_data["Mean20"]))
            mean60 = get_technical_indicator_pretty_list(json.loads(technical_data["Mean60"]))
            volume = get_technical_indicator_pretty_list(json.loads(technical_data["Volume"]))
            mean_5_volume = get_technical_indicator_pretty_list(
                json.loads(technical_data["Mean5Volume"])
            )
            mean_20_volume = get_technical_indicator_pretty_list(
                json.loads(technical_data["Mean20Volume"])
            )
            daily_k = get_daily_k_pretty_list(json.loads(technical_data["DailyK"]))
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
        except:
            if "請休息一下再試試" in r.text:
                logger.error("The web crawler has been blocked by the website...")
            continue
    return None
