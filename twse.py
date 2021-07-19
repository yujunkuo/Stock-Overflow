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

## 取得證交所當日所有上市股票資料

# (Public) 取得最終合併後的資料表
def get_twse_final(date):
    _start_time = time.time()
    twse_price_df = _get_twse_price(date)
    twse_fundamental_df = _get_twse_fundamental(date)
    twse_margin_trading_df = _get_twse_margin_trading(date)
    twse_institutional_df = _get_twse_institutional(date)
    twse_hold_percentage_df = _get_twse_hold_percentage(date)
    try:
        df = pd.merge(twse_price_df, twse_fundamental_df, how="left", on=["代號", "名稱", "股票類型"])
        df = pd.merge(df, twse_margin_trading_df, how="left", on=["代號", "名稱", "股票類型"])
        df = pd.merge(df, twse_institutional_df, how="left", on=["代號", "名稱", "股票類型"])
        df = pd.merge(df, twse_hold_percentage_df, how="left", on=["代號", "名稱", "股票類型"])
        # 沒有三大法人買賣超的補上0
#         df[['外資買賣超股數', '投信買賣超股數', "自營商買賣超股數", "三大法人買賣超股數"]] = df[['外資買賣超股數', '投信買賣超股數', "自營商買賣超股數", "三大法人買賣超股數"]].fillna(value=0)
        # 外資沒有持股的補上0
#         df[["外資持股比率(%)"]] = df[["外資持股比率(%)"]].fillna(value=0)
        df = df.set_index("代號")
        _end_time = time.time()
        _spent_time = _end_time - _start_time
        print(f"取得上市資料表花費時間: {datetime.timedelta(seconds=int(_spent_time))}")
        return df
    except:
        print("Bug!")
        return None


# 取得當日收盤價格相關資料
def _get_twse_price(date) -> pd.DataFrame:
    try:
        year = date.year
        month = date.month
        day = date.day
        new_date = f"{year}{month:02}{day:02}"  # 生成符合 url query 的日期字串
        r = requests.post(f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={new_date}&type=ALL")
        # 整理資料，變成表格
        df = pd.read_csv(StringIO(r.text.replace("=", "")), 
            header=["證券代號" in l for l in r.text.split("\n")].index(True)-1)
        # 去除各個欄位名稱後方的多餘空格
        df.columns = [each.strip() for each in df.columns]
        # 更新名稱與代號欄位的資料型態
        df["證券名稱"] = df["證券名稱"].astype(str)
        df["證券代號"] = df["證券代號"].astype(str)
        # 去除名稱與代號的前後空格
        df["證券名稱"] = df["證券名稱"].str.strip()
        df["證券代號"] = df["證券代號"].str.strip()
        # 去除多餘欄位
        df = df.drop(["Unnamed: 16"], axis=1, inplace=False)
        # 取出上市股票（4碼）
        df = df[(df["證券代號"].str.len() == 4) & (df["證券代號"].str[:2] != "00")]
        # 合併漲跌數據
        df["漲跌"] = [str(x) + str(y) for x, y in zip(df["漲跌(+/-)"], df["漲跌價差"])]
        # 僅保留所需欄位
        df = df.drop(["成交筆數", "成交金額", "最後揭示買價", "最後揭示買量", "最後揭示賣價", "最後揭示賣量", "本益比", "漲跌(+/-)", "漲跌價差"], axis=1, inplace=False)
        # 字串轉數字，去除逗號
        df = df.apply(lambda s: pd.to_numeric(s.astype(str).str.replace(",", ""), errors='coerce') if s.name not in ["證券代號", "證券名稱"] else s)
        # 重新命名表頭
        df.columns = ["代號", "名稱", "成交股數", "開盤", "最高", "最低", "收盤", "漲跌"]
        # 重新排序表頭
        df = df[["代號", "名稱", "收盤", "漲跌", "開盤", "最高", "最低", "成交股數"]]
        # 重新照股票代號排序
        df = df.sort_values(by=["代號"])
        # 重置 index
        df = df.reset_index(drop=True)
        # 新增類別（twse）
        df["股票類型"] = "twse"
        return df
    except:
        return pd.DataFrame(columns=["代號", "名稱", "收盤", "漲跌", "開盤", "最高", "最低", "成交股數", "股票類型"])


# 取得公司基本面相關資料
def _get_twse_fundamental(date) -> pd.DataFrame:
    try:
        year = date.year
        month = date.month
        day = date.day
        new_date = f"{year}{month:02}{day:02}"  # 生成符合 url query 的日期字串
        r = requests.get(f"https://www.twse.com.tw/exchangeReport/BWIBBU_d?response=csv&date={new_date}&selectType=ALL")
        # 整理資料，變成表格
        df = pd.read_csv(StringIO(r.text.replace("=", "")), 
            header=1)
        # 去除各個欄位名稱後方的多餘空格
        df.columns = [each.strip() for each in df.columns]
        # 更新名稱與代號欄位的資料型態
        df["證券名稱"] = df["證券名稱"].astype(str)
        df["證券代號"] = df["證券代號"].astype(str)
        # 去除名稱與代號的前後空格
        df["證券名稱"] = df["證券名稱"].str.strip()
        df["證券代號"] = df["證券代號"].str.strip()
        # 去除多餘欄位
        df = df.drop(["Unnamed: 7", "財報年/季"], axis=1, inplace=False)
        # 取出上市股票（4碼）
        df = df[(df["證券代號"].str.len() == 4) & (df["證券代號"].str[:2] != "00")]
        # 字串轉數字，去除逗號
        df = df.apply(lambda s: pd.to_numeric(s.astype(str).str.replace(",", ""), errors='coerce') if s.name not in ["證券代號", "證券名稱"] else s)
        # 重新命名表頭
        df = df.rename(columns={"證券代號": "代號", "證券名稱": "名稱"})
        # 重新排序表頭
        df = df[["代號", "名稱", "本益比", "股利年度", "殖利率(%)", "股價淨值比"]]
        # 重新照股票代號排序
        df = df.sort_values(by=["代號"])
        # 重置 index
        df = df.reset_index(drop=True)
        # 新增類別（twse）
        df["股票類型"] = "twse"
        return df
    except:
        return pd.DataFrame(columns=["代號", "名稱", "本益比", "股利年度", "殖利率(%)", "股價淨值比", "股票類型"])


# 取得當日收盤融資融券相關資料
def _get_twse_margin_trading(date) -> pd.DataFrame:
    try:
        year = date.year
        month = date.month
        day = date.day
        new_date = f"{year}{month:02}{day:02}"  # 生成符合 url query 的日期字串
        r = requests.get(f"https://www.twse.com.tw/exchangeReport/MI_MARGN?response=csv&date={new_date}&selectType=ALL")
        # 整理資料，變成表格
        df = pd.read_csv(StringIO(r.text.replace("=", "")), header=7)
        # 去除各個欄位名稱後方的多餘空格
        df.columns = [each.strip() for each in df.columns]
        # 更新名稱與代號欄位的資料型態
        df["股票名稱"] = df["股票名稱"].astype(str)
        df["股票代號"] = df["股票代號"].astype(str)
        # 去除名稱與代號的前後空格
        df["股票名稱"] = df["股票名稱"].str.strip()
        df["股票代號"] = df["股票代號"].str.strip()
        # 去除多餘欄位
        df = df.drop(["現金償還", "限額", "現券償還", "限額.1", "註記", "Unnamed: 16"], axis=1, inplace=False)
        # 取出上市股票（4碼）
        df = df[(df["股票代號"].str.len() == 4) & (df["股票代號"].str[:2] != "00")]
        # 字串轉數字，去除逗號
        df = df.apply(lambda s: pd.to_numeric(s.astype(str).str.replace(",", ""), errors='coerce') if s.name not in ["股票代號", "股票名稱"] else s)
        # 重新命名表頭
        df = df.rename(columns={"股票代號": "代號", "股票名稱": "名稱", "買進": "融資買進", "賣出": "融資賣出",
                               "前日餘額": "融資前日餘額", "今日餘額": "融資今日餘額", "買進.1": "融券買進", "賣出.1": "融券賣出",
                               "前日餘額.1": "融券前日餘額", "今日餘額.1": "融券今日餘額"})
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
        # 新增類別（twse）
        df["股票類型"] = "twse"
        return df
    except:
        return pd.DataFrame(columns=["代號", "名稱", "融資買進", "融資賣出", "融資前日餘額", "融資今日餘額", 
                                     "融券買進", "融券賣出", "融券前日餘額", "融券今日餘額", "資券互抵", "融資變化量", "融券變化量", "券資比(%)", "股票類型"])


# 取得當日收盤三大法人買賣超相關資料
def _get_twse_institutional(date) -> pd.DataFrame:
    try:
        year = date.year
        month = date.month
        day = date.day
        new_date = f"{year}{month:02}{day:02}"  # 生成符合 url query 的日期字串
        r = requests.get(f"https://www.twse.com.tw/fund/T86?response=csv&date={new_date}&selectType=ALL")
        # 整理資料，變成表格
        df = pd.read_csv(StringIO(r.text.replace("=", "")), 
            header=1)
        # 去除各個欄位名稱後方的多餘空格
        df.columns = [each.strip() for each in df.columns]
        # 更新名稱與代號欄位的資料型態
        df["證券名稱"] = df["證券名稱"].astype(str)
        df["證券代號"] = df["證券代號"].astype(str)
        # 去除名稱與代號的前後空格
        df["證券名稱"] = df["證券名稱"].str.strip()
        df["證券代號"] = df["證券代號"].str.strip()
        # 去除多餘欄位
        df = df[["證券代號", "證券名稱", "外陸資買賣超股數(不含外資自營商)", "投信買賣超股數", "自營商買賣超股數", "三大法人買賣超股數"]]
        # 取出上市股票（4碼）
        df = df[(df["證券代號"].str.len() == 4) & (df["證券代號"].str[:2] != "00")]
        # 字串轉數字，去除逗號
        df = df.apply(lambda s: pd.to_numeric(s.astype(str).str.replace(",", ""), errors='coerce') if s.name not in ["證券代號", "證券名稱"] else s)
        # 重新命名表頭
        df = df.rename(columns={"證券名稱": "名稱", "證券代號": "代號", "外陸資買賣超股數(不含外資自營商)": "外資買賣超股數"})
        # 重新排序表頭
        df = df[["代號", "名稱", "外資買賣超股數", "投信買賣超股數", "自營商買賣超股數", "三大法人買賣超股數"]]
        # 重新照股票代號排序
        df = df.sort_values(by=["代號"])
        # 重置 index
        df = df.reset_index(drop=True)
        # 新增類別（twse）
        df["股票類型"] = "twse"
        return df
    except:
        return pd.DataFrame(columns=["代號", "名稱", "外資買賣超股數", "投信買賣超股數", "自營商買賣超股數", "三大法人買賣超股數", "股票類型"])


# 取得外資持股比率資料
def _get_twse_hold_percentage(date) -> pd.DataFrame:
    try:
        year = date.year
        month = date.month
        day = date.day
        new_date = f"{year}{month:02}{day:02}"  # 生成符合 url query 的日期字串
        r = requests.get(f"https://www.twse.com.tw/fund/MI_QFIIS?response=csv&date={new_date}&selectType=ALLBUT0999")
        # 整理資料，變成表格
        df = pd.read_csv(StringIO(r.text.replace("=", "")), 
            header=1)
        # 去除各個欄位名稱後方的多餘空格
        df.columns = [each.strip() for each in df.columns]
        # 更新名稱與代號欄位的資料型態
        df["證券名稱"] = df["證券名稱"].astype(str)
        df["證券代號"] = df["證券代號"].astype(str)
        # 去除名稱與代號的前後空格
        df["證券名稱"] = df["證券名稱"].str.strip()
        df["證券代號"] = df["證券代號"].str.strip()
        # 去除多餘欄位
        df = df[["證券代號", "證券名稱", "全體外資及陸資持股比率"]]
        # 取出上市股票（4碼）
        df = df[(df["證券代號"].str.len() == 4) & (df["證券代號"].str[:2] != "00")]
        # 字串轉數字，去除逗號
        df = df.apply(lambda s: pd.to_numeric(s.astype(str).str.replace(",", ""), errors='coerce') if s.name not in ["證券代號", "證券名稱"] else s)
        # 重新命名表頭
        df = df.rename(columns={"證券名稱": "名稱", "證券代號": "代號", "全體外資及陸資持股比率": "外資持股比率(%)"})
        # 重新排序表頭
        df = df[["代號", "名稱", "外資持股比率(%)"]]
        # 重新照股票代號排序
        df = df.sort_values(by=["代號"])
        # 重置 index
        df = df.reset_index(drop=True)
        # 新增類別（twse）
        df["股票類型"] = "twse"
        return df
    except:
        return pd.DataFrame(columns=["代號", "名稱", "外資持股比率(%)", "股票類型"])