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

## 取得櫃買中心當日所有上櫃股票資料

MAX_REQUEST_RETRIES = 5

# (Public) 取得最終合併後的資料表
def get_tpex_final(date):
    _start_time = time.time()
    tpex_price_df = _get_tpex_price(date)
    tpex_fundamental_df = _get_tpex_fundamental(date)
    tpex_margin_trading_df = _get_tpex_margin_trading(date)
    tpex_institutional = _get_tpex_institutional(date)
    tpex_hold_percentage_df = _get_tpex_hold_percentage(date)
    try:
        df = pd.merge(tpex_price_df, tpex_fundamental_df, how="left", on=["代號", "名稱", "股票類型"])
        df = pd.merge(df, tpex_margin_trading_df, how="left", on=["代號", "名稱", "股票類型"])
        df = pd.merge(df, tpex_institutional, how="left", on=["代號", "名稱", "股票類型"])
        df = pd.merge(df, tpex_hold_percentage_df, how="left", on=["代號", "名稱", "股票類型"])
        # 沒有三大法人買賣超的補上0
    #         df[['外資買賣超股數', '投信買賣超股數', "自營商買賣超股數", "三大法人買賣超股數"]] = df[['外資買賣超股數', '投信買賣超股數', "自營商買賣超股數", "三大法人買賣超股數"]].fillna(value=0)
        # 外資沒有持股的補上0
    #         df[["外資持股比率(%)"]] = df[["外資持股比率(%)"]].fillna(value=0)
        df = df.set_index("代號")
        _end_time = time.time()
        _spent_time = _end_time - _start_time
        print(f"取得上櫃資料表花費時間: {datetime.timedelta(seconds=int(_spent_time))}")
        return df
    except:
        print("Bug!")
        return None


# 取得當日收盤價格相關資料
def _get_tpex_price(date) -> pd.DataFrame:
    for _ in range(MAX_REQUEST_RETRIES):
        try:
            year = date.year - 1911  # 轉換成民國
            month = date.month
            day = date.day
            new_date = f"{year}/{month:02}/{day:02}"  # 生成符合 url query 的日期字串
            r = requests.get(f"https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php?l=zh-tw&o=csv&d={new_date}&se=AL&s=0,asc,0")
            # 整理資料，變成表格
            r.encoding = "Big5"
            df = pd.read_csv(StringIO(r.text), header=3)
            # 去除各個欄位名稱後方的多餘空格
            df.columns = [each.strip() for each in df.columns]
            # 更新名稱與代號欄位的資料型態
            df["名稱"] = df["名稱"].astype(str)
            df["代號"] = df["代號"].astype(str)
            # 去除名稱與代號的前後空格
            df["名稱"] = df["名稱"].str.strip()
            df["代號"] = df["代號"].str.strip()
            # 僅保留所需欄位
            df = df.drop(df.columns[8:], axis=1, inplace=False)
            # 取出上櫃股票（4碼）
            df = df[(df["代號"].str.len() == 4) & (df["代號"].str[:2] != "00")]
            # 字串轉數字，去除逗號
            df = df.apply(lambda s: pd.to_numeric(s.astype(str).str.replace(",", ""), errors='coerce') if s.name not in ["代號", "名稱"] else s)
            # 重新排序表頭
            df = df[["代號", "名稱", "收盤", "漲跌", "開盤", "最高", "最低", "成交股數"]]
            # 重新照股票代號排序
            df = df.sort_values(by=["代號"])
            # 重置 index
            df = df.reset_index(drop=True)
            # 新增類別（tpex）
            df["股票類型"] = "tpex"
            return df
        except:
            print(f"Attempt {_get_tpex_price.__name__} failed.")
            time.sleep(3)
    return pd.DataFrame(columns=['代號', '名稱', '收盤', '漲跌', '開盤', '最高', '最低', '成交股數', '股票類型'])


# 取得公司基本面相關資料
def _get_tpex_fundamental(date) -> pd.DataFrame:
    for _ in range(MAX_REQUEST_RETRIES):
        try:
            year = date.year - 1911  # 轉換成民國
            month = date.month
            day = date.day
            new_date = f"{year}/{month:02}/{day:02}"  # 生成符合 url query 的日期字串
            r = requests.get(f"https://www.tpex.org.tw/web/stock/aftertrading/peratio_analysis/pera_result.php?l=zh-tw&o=csv&charset=UTF-8&d={new_date}&c=&s=0,asc")
            # 整理資料，變成表格
            r.encoding = "Big5"
            df = pd.read_csv(StringIO(r.text), header=3)
            # 去除各個欄位名稱後方的多餘空格
            df.columns = [each.strip() for each in df.columns]
            # 更新名稱與代號欄位的資料型態
            df["名稱"] = df["名稱"].astype(str)
            df["股票代號"] = df["股票代號"].astype(str)
            # 去除名稱與代號的前後空格
            df["名稱"] = df["名稱"].str.strip()
            df["股票代號"] = df["股票代號"].str.strip()
            # 去除多餘欄位
            df = df.drop(["每股股利",], axis=1, inplace=False)
            # 取出上櫃股票（4碼）
            df = df[(df["股票代號"].str.len() == 4) & (df["股票代號"].str[:2] != "00")]
            # 字串轉數字，去除逗號
            df = df.apply(lambda s: pd.to_numeric(s.astype(str).str.replace(",", ""), errors='coerce') if s.name not in ["股票代號", "名稱"] else s)
            # 將不同表格的「股票代號」欄位名稱都統一為「代號」
            df = df.rename(columns={"股票代號": "代號"})
            # 重新排序表頭
            df = df[["代號", "名稱", "本益比", "股利年度", "殖利率(%)", "股價淨值比"]]
            # 重新照股票代號排序
            df = df.sort_values(by=["代號"])
            # 重置 index
            df = df.reset_index(drop=True)
            # 新增類別（tpex）
            df["股票類型"] = "tpex"
            return df
        except:
            print(f"Attempt {_get_tpex_fundamental.__name__} failed.")
            time.sleep(3)
    return pd.DataFrame(columns=['代號', '名稱', '本益比', '股利年度', '殖利率(%)', '股價淨值比', '股票類型'])


# 取得當日收盤融資融券相關資料
def _get_tpex_margin_trading(date) -> pd.DataFrame:
    for _ in range(MAX_REQUEST_RETRIES):
        try:
            year = date.year - 1911  # 轉換成民國
            month = date.month
            day = date.day
            new_date = f"{year}/{month:02}/{day:02}"  # 生成符合 url query 的日期字串
            r = requests.get(f"https://www.tpex.org.tw/web/stock/margin_trading/margin_balance/margin_bal_result.php?l=zh-tw&o=csv&charset=UTF-8&d={new_date}&s=0,asc")
            # 整理資料，變成表格
            r.encoding = "Big5"
            df = pd.read_csv(StringIO(r.text), header=2)
            # 去除各個欄位名稱後方的多餘空格
            df.columns = [each.strip() for each in df.columns]
            # 更新名稱與代號欄位的資料型態
            df["名稱"] = df["名稱"].astype(str)
            df["代號"] = df["代號"].astype(str)
            # 去除名稱與代號的前後空格
            df["名稱"] = df["名稱"].str.strip()
            df["代號"] = df["代號"].str.strip()
            # 去除多餘欄位
            df = df.drop(["現償", "資屬證金", "資使用率(%)", "資限額", "券償", "券屬證金", "券使用率(%)", "券限額", "備註"], axis=1, inplace=False)
            # 取出上櫃股票（4碼）
            df = df[(df["代號"].str.len() == 4) & (df["代號"].str[:2] != "00")]
            # 字串轉數字，去除逗號
            df = df.apply(lambda s: pd.to_numeric(s.astype(str).str.replace(",", ""), errors='coerce') if s.name not in ["代號", "名稱"] else s)
            # 重新命名表頭
            df = df.rename(columns={"資買": "融資買進", "資賣": "融資賣出",
                                "前資餘額(張)": "融資前日餘額", "資餘額": "融資今日餘額", "券買": "融券買進", "券賣": "融券賣出",
                                "前券餘額(張)": "融券前日餘額", "券餘額": "融券今日餘額", "資券相抵(張)": "資券互抵"})
            # 計算指標
            df["融資變化量"] = df["融資今日餘額"] - df["融資前日餘額"]
            df["融券變化量"] = df["融券今日餘額"] - df["融券前日餘額"]
            df["券資比(%)"] = round((df["融券今日餘額"] / df["融資今日餘額"]) * 100, 2)  # 注意分母是否為0
            # 重新排序表頭
            df = df[["代號", "名稱", "融資買進", "融資賣出", "融資前日餘額", "融資今日餘額", 
                                        "融券買進", "融券賣出", "融券前日餘額", "融券今日餘額", "資券互抵", "融資變化量", "融券變化量", "券資比(%)"]]
            # 重新照股票代號排序
            df = df.sort_values(by=["代號"])
            # 重置 index
            df = df.reset_index(drop=True)
            # 新增類別（tpex）
            df["股票類型"] = "tpex"
            return df
        except:
            print(f"Attempt {_get_tpex_margin_trading.__name__} failed.")
            time.sleep(3)
    return pd.DataFrame(columns=["代號", "名稱", "融資買進", "融資賣出", "融資前日餘額", "融資今日餘額", 
                                        "融券買進", "融券賣出", "融券前日餘額", "融券今日餘額", "資券互抵", "融資變化量", "融券變化量", "券資比(%)", "股票類型"])


# 取得當日收盤三大法人買賣超相關資料
def _get_tpex_institutional(date) -> pd.DataFrame:
    for _ in range(MAX_REQUEST_RETRIES):
        try:
            year = date.year - 1911  # 轉換成民國
            month = date.month
            day = date.day
            new_date = f"{year}/{month:02}/{day:02}"  # 生成符合 url query 的日期字串
            r = requests.get(f"https://www.tpex.org.tw/web/stock/3insti/daily_trade/3itrade_hedge_result.php?l=zh-tw&o=csv&se=AL&t=D&d={new_date}&s=0,asc")
            # 整理資料，變成表格
            r.encoding = "Big5"
            df = pd.read_csv(StringIO(r.text), header=1)
            # 去除各個欄位名稱後方的多餘空格
            df.columns = [each.strip() for each in df.columns]
            # 更新名稱與代號欄位的資料型態
            df["名稱"] = df["名稱"].astype(str)
            df["代號"] = df["代號"].astype(str)
            # 去除名稱與代號的前後空格
            df["名稱"] = df["名稱"].str.strip()
            df["代號"] = df["代號"].str.strip()
            # 去除多餘欄位
            df = df[["代號", "名稱", "外資及陸資(不含外資自營商)-買賣超股數", "投信-買賣超股數", "自營商-買賣超股數", "三大法人買賣超股數合計"]]
            # 取出上櫃股票（4碼）
            df = df[(df["代號"].str.len() == 4) & (df["代號"].str[:2] != "00")]
            # 字串轉數字，去除逗號
            df = df.apply(lambda s: pd.to_numeric(s.astype(str).str.replace(",", ""), errors='coerce') if s.name not in ["代號", "名稱"] else s)
            # 重新命名表頭
            df = df.rename(columns={"外資及陸資(不含外資自營商)-買賣超股數": "外資買賣超股數", "投信-買賣超股數": "投信買賣超股數", 
                                    "自營商-買賣超股數": "自營商買賣超股數", "三大法人買賣超股數合計": "三大法人買賣超股數"})
            # 重新排序表頭
            df = df[["代號", "名稱", "外資買賣超股數", "投信買賣超股數", "自營商買賣超股數", "三大法人買賣超股數"]]
            # 重新照股票代號排序
            df = df.sort_values(by=["代號"])
            # 重置 index
            df = df.reset_index(drop=True)
            # 新增類別（tpex）
            df["股票類型"] = "tpex"
            return df
        except:
            print(f"Attempt {_get_tpex_institutional.__name__} failed.")
            time.sleep(3)
    return pd.DataFrame(columns=['代號', '名稱', '外資買賣超股數', '投信買賣超股數', '自營商買賣超股數', '三大法人買賣超股數', '股票類型'])


# 取得外資持股比率資料
def _get_tpex_hold_percentage(date) -> pd.DataFrame:
    for _ in range(MAX_REQUEST_RETRIES):
        try:
            year = date.year
            month = date.month
            day = date.day
            # 生成符合 url query 的日期字串
            data = {"years": f"{year}", "months": f"{month:02}", "days": f"{day:02}", "bcode": "", "step": "2"}
            r = requests.post("https://mops.twse.com.tw/server-java/t13sa150_otc", data=data)
            # 解決編碼亂碼問題（在網頁的 console 執行 document.characterSet 查看編碼）
            # Console 可以看很多資訊（function, Encoding, Url...）
            r.encoding = "Big5"
            soup = BeautifulSoup(r.text, "html.parser")
            data = soup.find_all("td")
            hold_percentage_list = [[data[x].text, data[x+1].text, data[x+6].text] for x in range(0, len(data), 11)]
            df = pd.DataFrame(hold_percentage_list, columns=["代號", "名稱", "外資持股比率(%)"])
            # 去除各個欄位名稱後方的多餘空格
            df.columns = [each.strip() for each in df.columns]
            # 更新名稱與代號欄位的資料型態
            df["名稱"] = df["名稱"].astype(str)
            df["代號"] = df["代號"].astype(str)
            # 去除名稱與代號的前後空格
            df["名稱"] = df["名稱"].str.strip()
            df["代號"] = df["代號"].str.strip()
            # 取出上櫃股票（4碼）
            df = df[(df["代號"].str.len() == 4) & (df["代號"].str[:2] != "00") & (df["代號"].str.isdigit())]
            # 字串轉數字，去除逗號
            df = df.apply(lambda s: pd.to_numeric(s.astype(str).str.replace(",", ""), errors='coerce') if s.name not in ["代號", "名稱"] else s)
            # 重新排序表頭
            df = df[["代號", "名稱", "外資持股比率(%)"]]
            # 重新照股票代號排序
            df = df.sort_values(by=["代號"])
            # 重置 index
            df = df.reset_index(drop=True)
            # 新增類別（tpex）
            df["股票類型"] = "tpex"
            return df
        except:
            print(f"Attempt {_get_tpex_hold_percentage.__name__} failed.")
            time.sleep(3)
    return pd.DataFrame(columns=["代號", "名稱", "外資持股比率(%)", "股票類型"])