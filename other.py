import requests
from bs4 import BeautifulSoup
import datetime
import time
import random
import pandas as pd
import numpy as np
from io import StringIO
import json
from functools import reduce

## 取得其他股票相關指標

# (Public) 透過 FinMind 取得股票產業別
def get_industry_category() -> pd.DataFrame:
    parameter = {
        "dataset": "TaiwanStockInfo",
        "token": "", # 參考登入，獲取金鑰
    }
    r = requests.get("https://api.finmindtrade.com/api/v4/data", params=parameter)
    data = r.json()
    df = pd.DataFrame(data["data"])
    # 去除各個欄位名稱後方的多餘空格
    df.columns = [each.strip() for each in df.columns]
    # 重新命名欄位
    df = df.rename(columns={"industry_category": "產業別", "stock_id": "代號", "stock_name": "名稱", "type": "股票類型"})
    # 更新名稱與代號欄位的資料型態
    df["名稱"] = df["名稱"].astype(str)
    df["代號"] = df["代號"].astype(str)
    # 去除名稱與代號的前後空格
    df["名稱"] = df["名稱"].str.strip()
    df["代號"] = df["代號"].str.strip()
    # 取出股票（4碼）
    df = df[(df["代號"].str.len() == 4) & (df["代號"].str[:2] != "00") & (df["代號"].str.isdigit())]
    # 只保留所需欄位
    df = df[["代號", "名稱", "產業別", "股票類型"]]
    df = df.set_index("代號")
    return df


# (Public) 取得上市上櫃 MoM 與 YoY
def get_mom_yoy() -> pd.DataFrame:
    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    }
    r = requests.get("https://stock.wespai.com/p/44850", headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    data = soup.find_all("td")
    mom_yoy_list = [[data[x].text, data[x+1].select_one("a").text, data[x+3].text, data[x+4].text, data[x+5].text] for x in range(0, len(data), 6)]
    df = pd.DataFrame(mom_yoy_list, columns=["代號", "名稱", "(月)營收月增率(%)", "(月)營收年增率(%)", "(月)累積營收年增率(%)"])
    # 字串轉數字，去除逗號
    df = df.apply(lambda s: pd.to_numeric(s.astype(str).str.replace(",", ""), errors='coerce') if s.name not in ["代號", "名稱"] else s)
    # 更新名稱與代號欄位的資料型態
    df["名稱"] = df["名稱"].astype(str)
    df["代號"] = df["代號"].astype(str)
    # 去除名稱與代號的前後空格
    df["名稱"] = df["名稱"].str.strip()
    df["代號"] = df["代號"].str.strip()
    df = df.set_index("代號")
    df = df.sort_index()
    return df


# (Public) 將「技術指標」添加至輸入的 DataFrame 當中
def get_technical_indicators(input_df: pd.DataFrame) -> pd.DataFrame:
    df = input_df.copy()
    start_time_ = time.time()
    new_column_list = ["k9", "d9", "dif", "macd", "osc", "mean5", "mean10", "mean20", "mean60", "volume", "mean_5_volume", "mean_20_volume", "daily_k"]
    df[new_column_list] = None
    df[["k9", "d9", "dif", "macd", "osc", "mean5", "mean10", "mean20", "mean60", "volume", "mean_5_volume", "mean_20_volume", "daily_k"]] = df[["k9", "d9", "dif", "macd", "osc", "mean5", "mean10", "mean20", "mean60", "volume", "mean_5_volume", "mean_20_volume", "daily_k"]].astype('object')
    # 先從台積電判斷日期是否為今天（必須要是最新資料才回傳）
    test_data = _get_technical_indicators_from_stock_id("2330")
    test_date = test_data["daily_k"][-1][0]
    if test_date != datetime.date.today():
        return df
    total_ = len(df.index)
    current_finish_ = 0
    for i, row in df.iterrows():
        try:
            technical_data = _get_technical_indicators_from_stock_id(i)
            for each in new_column_list:
                df.loc[[str(i)], each] = [technical_data[each]]
            current_finish_ += 1
            if current_finish_ % 25 == 0:
                print(f"Finish technical data: {current_finish_}/{total_}, index = {i}")
#               time.sleep(random.randint(1, 3))
        except:
            current_finish_ += 1
            print(f"Finish technical data: {current_finish_}/{total_}, Fail!")
#           time.sleep(random.randint(1, 3))
    end_time_ = time.time()
    spent_time_ = end_time_ - start_time_
    print(f"取得技術指標花費時間: {datetime.timedelta(seconds=int(spent_time_))}")
    return df


# 取得單一股票的技術指標資訊
def _get_technical_indicators_from_stock_id(stock_id: str) -> dict:
    try:
        # days = 360 時 Heroku 記憶體會爆掉 / days = 200 時 Render 記憶體會爆掉
        # (new) 嘗試 days = 240，也就是爬取一整年的資料
        # r = requests.get(f"https://histock.tw/stock/chip/chartdata.aspx?no={stock_id}&days=120&m=dailyk,close,volume,mean5,mean10,mean20,mean60,mean120,mean5volume,mean20volume,k9,d9,rsi6,rsi12,dif,macd,osc")
        r = requests.get(f"https://histock.tw/stock/chip/chartdata.aspx?no={stock_id}&days=240&m=dailyk,close,volume,mean5,mean10,mean20,mean60,mean5volume,mean20volume,k9,d9,dif,macd,osc")
        technical_data = r.json()
        k9 = _make_technical_pretty_list(json.loads(technical_data["K9"]))
        d9 = _make_technical_pretty_list(json.loads(technical_data["D9"]))
        dif = _make_technical_pretty_list(json.loads(technical_data["DIF"]))
        macd = _make_technical_pretty_list(json.loads(technical_data["MACD"]))
        osc = _make_technical_pretty_list(json.loads(technical_data["OSC"]))
        mean5 = _make_technical_pretty_list(json.loads(technical_data["Mean5"]))
        mean10 = _make_technical_pretty_list(json.loads(technical_data["Mean10"]))
        mean20 = _make_technical_pretty_list(json.loads(technical_data["Mean20"]))
        mean60 = _make_technical_pretty_list(json.loads(technical_data["Mean60"]))
        volume = _make_technical_pretty_list(json.loads(technical_data["Volume"]))
        mean_5_volume = _make_technical_pretty_list(json.loads(technical_data["Mean5Volume"]))
        mean_20_volume = _make_technical_pretty_list(json.loads(technical_data["Mean20Volume"]))
        daily_k = _make_daily_k_pretty_list(json.loads(technical_data["DailyK"]))
        return {"k9": k9, "d9": d9, "dif": dif, "macd": macd, "osc": osc,
                "mean5": mean5, "mean10": mean10, "mean20": mean20, "mean60": mean60,
                "volume": volume, "mean_5_volume": mean_5_volume, "mean_20_volume": mean_20_volume,
                "daily_k": daily_k}
    except:
        return None


# 資料清洗 (一般技術指標)
def _make_technical_pretty_list(indicator_list: list) -> list:
    return [[_calculate_date_from_milliseconds(t), i] for t, i in indicator_list]


# 資料清洗 (K線)
def _make_daily_k_pretty_list(daily_k_list: list) -> list:
    new_daily_k_list = list()
    for each in daily_k_list:
        single_time = _calculate_date_from_milliseconds(each[0])
        single_k_dict = {
            "開盤": each[1],
            "最高": each[2],
            "最低": each[3],
            "收盤": each[4],
        }
        new_daily_k_list.append([single_time, single_k_dict])
    return new_daily_k_list


# 將輸入的 milliseconds 轉換為當前日期
def _calculate_date_from_milliseconds(input_milliseconds: int) -> datetime.date:
    current_year = datetime.datetime.now().year
    current_year_beginning = datetime.date(current_year, 1, 1)
    time_delta_days = datetime.timedelta(days=datetime.timedelta(seconds=input_milliseconds/1000 - 13*86400).days % 365)
    final_date = current_year_beginning + time_delta_days
    return final_date