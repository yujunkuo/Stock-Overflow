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

## 取得其他股票相關指標

MAX_REQUEST_RETRIES = 2


# (Public) 透過 FinMind 取得股票產業別
def get_industry_category() -> pd.DataFrame:
    for _ in range(MAX_REQUEST_RETRIES):
        try:
            parameter = {
                "dataset": "TaiwanStockInfo",
                "token": "",  # 參考登入，獲取金鑰
            }
            r = requests.get(
                "https://api.finmindtrade.com/api/v4/data", params=parameter
            )
            data = r.json()
            df = pd.DataFrame(data["data"])
            # 去除各個欄位名稱後方的多餘空格
            df.columns = [each.strip() for each in df.columns]
            # 重新命名欄位
            df = df.rename(
                columns={
                    "industry_category": "產業別",
                    "stock_id": "代號",
                    "stock_name": "名稱",
                    "type": "股票類型",
                }
            )
            # 更新名稱與代號欄位的資料型態
            df["名稱"] = df["名稱"].astype(str)
            df["代號"] = df["代號"].astype(str)
            # 去除名稱與代號的前後空格
            df["名稱"] = df["名稱"].str.strip()
            df["代號"] = df["代號"].str.strip()
            # 取出股票（4碼）
            df = df[
                (df["代號"].str.len() == 4)
                & (df["代號"].str[:2] != "00")
                & (df["代號"].str.isdigit())
            ]
            # 只保留所需欄位
            df = df[["代號", "名稱", "產業別", "股票類型"]]
            df = df.set_index("代號")
            return df
        except:
            logger.warning(f"Attempt {get_industry_category.__name__} failed.")
            time.sleep(3)
    return pd.DataFrame(columns=["代號", "名稱", "產業別", "股票類型"]).set_index(
        "代號"
    )


# (Public) 取得上市上櫃 MoM 與 YoY
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
                    data[x + 1].select_one("a").text,
                    data[x + 3].text,
                    data[x + 4].text,
                    data[x + 5].text,
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
            # 字串轉數字，去除逗號
            df = df.apply(
                lambda s: (
                    pd.to_numeric(s.astype(str).str.replace(",", ""), errors="coerce")
                    if s.name not in ["代號", "名稱"]
                    else s
                )
            )
            # 更新名稱與代號欄位的資料型態
            df["名稱"] = df["名稱"].astype(str)
            df["代號"] = df["代號"].astype(str)
            # 去除名稱與代號的前後空格
            df["名稱"] = df["名稱"].str.strip()
            df["代號"] = df["代號"].str.strip()
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


# (Public) 將「技術指標」添加至輸入的 DataFrame 當中
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
    # 先從台積電判斷日期是否為今天（必須要是最新資料才回傳）
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


# 取得單一股票的技術指標資訊
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
            k9 = _make_technical_pretty_list(json.loads(technical_data["K9"]))
            d9 = _make_technical_pretty_list(json.loads(technical_data["D9"]))
            j9 = [
                [date_k, round(3 * value_k - 2 * value_d, 2)]
                for (date_k, value_k), (date_d, value_d) in zip(k9, d9)
            ]
            dif = _make_technical_pretty_list(json.loads(technical_data["DIF"]))
            macd = _make_technical_pretty_list(json.loads(technical_data["MACD"]))
            osc = _make_technical_pretty_list(json.loads(technical_data["OSC"]))
            mean5 = _make_technical_pretty_list(json.loads(technical_data["Mean5"]))
            mean10 = _make_technical_pretty_list(json.loads(technical_data["Mean10"]))
            mean20 = _make_technical_pretty_list(json.loads(technical_data["Mean20"]))
            mean60 = _make_technical_pretty_list(json.loads(technical_data["Mean60"]))
            volume = _make_technical_pretty_list(json.loads(technical_data["Volume"]))
            mean_5_volume = _make_technical_pretty_list(
                json.loads(technical_data["Mean5Volume"])
            )
            mean_20_volume = _make_technical_pretty_list(
                json.loads(technical_data["Mean20Volume"])
            )
            daily_k = _make_daily_k_pretty_list(json.loads(technical_data["DailyK"]))
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


# 資料清洗 (一般技術指標)
def _make_technical_pretty_list(indicator_list: list) -> list:
    return [
        [_calculate_date_from_milliseconds(t, len(indicator_list) - i - 1), v]
        for i, (t, v) in enumerate(indicator_list)
    ]


# 資料清洗 (K線)
def _make_daily_k_pretty_list(daily_k_list: list) -> list:
    new_daily_k_list = list()
    for i, each in enumerate(daily_k_list):
        single_time = _calculate_date_from_milliseconds(
            each[0], len(daily_k_list) - i - 1
        )
        single_k_dict = {
            "開盤": each[1],
            "最高": each[2],
            "最低": each[3],
            "收盤": each[4],
        }
        new_daily_k_list.append([single_time, single_k_dict])
    return new_daily_k_list


# 將輸入的 milliseconds 轉換為當前日期
def _calculate_date_from_milliseconds(
    input_milliseconds: int, time_delta: int
) -> datetime.date:
    current_year = (datetime.datetime.now() - datetime.timedelta(days=time_delta)).year
    current_year_beginning = datetime.date(current_year, 1, 1)
    time_delta_days = datetime.timedelta(
        days=datetime.timedelta(seconds=input_milliseconds / 1000 - 13 * 86400).days
        % 365
    )
    final_date = current_year_beginning + time_delta_days
    return final_date
