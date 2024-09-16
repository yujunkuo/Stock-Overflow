import requests
import pandas as pd
from io import StringIO
from model.data_type import DataType

# TODO: Stock calculate number unit: 1000 or 1?
# TODO: TWSE encoding


REQUEST_SETTING = {
    DataType.PRICE: {
        "url": "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={date_str}&type=ALL",
        "header_num": None,
    },
    DataType.FUNDAMENTAL: {
        "url": "https://www.twse.com.tw/exchangeReport/BWIBBU_d?response=csv&date={date_str}&selectType=ALL",
        "header_num": 1,
    },  
    DataType.MARGIN_TRADING: {
        "url": "https://www.twse.com.tw/rwd/zh/marginTrading/TWT93U?response=csv&date={date_str}&selectType=ALL",
        "header_num": 2,
    },
    DataType.INSTITUTIONAL: {
        "url": "https://www.twse.com.tw/rwd/zh/fund/T86?response=csv&date={date_str}&selectType=ALL",
        "header_num": 1,
    },
}


COLUMN_RENAME_SETTING = {
    "證券代號": "代號",
    "證券名稱": "名稱",
    "開盤價": "開盤",
    "最高價": "最高",
    "最低價": "最低",
    "收盤價": "收盤",
    "買進": "融資買進",
    "賣出": "融資賣出",
    "前日餘額": "融資前日餘額",
    "今日餘額": "融資今日餘額",
    "當日還券": "融券買進",
    "當日賣出": "融券賣出",
    "前日餘額.1": "融券前日餘額",
    "當日餘額": "融券今日餘額",
    "外陸資買賣超股數(不含外資自營商)": "外資買賣超股數",
}


COLUMN_KEEP_SETTING = {
    DataType.PRICE: ["代號", "名稱", "收盤", "漲跌", "開盤", "最高", "最低", "成交股數", "股票類型"],
    DataType.FUNDAMENTAL: ["代號", "名稱", "本益比", "股利年度", "殖利率(%)", "股價淨值比", "股票類型"],
    DataType.MARGIN_TRADING: ["代號", "名稱", "融資買進", "融資賣出", "融資前日餘額", "融資今日餘額", "融券買進", "融券賣出", "融券前日餘額", "融券今日餘額", "資券互抵", "融資變化量", "融券變化量", "券資比(%)", "股票類型"],
    DataType.INSTITUTIONAL: ["代號", "名稱", "外資買賣超股數", "投信買賣超股數", "自營商買賣超股數", "三大法人買賣超股數", "股票類型"],
}


def get_twse_data(data_type, data_date):
    setting = REQUEST_SETTING[data_type]
    year, month, day = data_date.year, data_date.month, data_date.day
    date_str = f"{year}{month:02}{day:02}"
    url = setting["url"].format(date_str=date_str)
    response = requests.get(url)
    header_num = setting["header_num"]
    if data_type == DataType.PRICE:
        header_num = ["證券代號" in l for l in response.text.split("\n")].index(True) - 1
    df = pd.read_csv(StringIO(response.text.replace("=", "")), header=header_num)
    return df


def clean_twse_data(data_type, df):
    # Remove leading and trailing spaces from column names
    df.columns = [column.strip() for column in df.columns]
    # Unify the column names of the stock code
    df = df.rename(columns=COLUMN_RENAME_SETTING)
    # Update the data type and remove leading and trailing spaces
    df["名稱"] = df["名稱"].astype(str).str.strip()
    df["代號"] = df["代號"].astype(str).str.strip()
    # Filter out the rows with invalid stock codes
    df = df[(df["代號"].str.len() == 4) & (df["代號"].str[:2] != "00")]
    # Convert the data type of the columns to numeric
    df = df.apply(
        lambda s: (
            pd.to_numeric(s.astype(str).str.replace(",", ""), errors="coerce")
            if s.name not in ["代號", "名稱"]
            else s
        )
    )
    # Add additional columns
    if data_type == DataType.PRICE:
        df["漲跌(+/-)"] = df["漲跌(+/-)"].map({"+": 1, "-": -1})
        df["漲跌"] = df["漲跌(+/-)"] * df["漲跌價差"]
    if data_type == DataType.MARGIN_TRADING:
        df["融資變化量"] = df["融資今日餘額"] - df["融資前日餘額"]
        df["融券變化量"] = df["融券今日餘額"] - df["融券前日餘額"]
        df["券資比(%)"] = round((df["融券今日餘額"] / df["融資今日餘額"]) * 100, 2)
    # Add the stock type column
    df["股票類型"] = "twse"
    # Only keep the columns needed
    df = df[COLUMN_KEEP_SETTING[data_type]]  
    # Sort the rows
    df = df.sort_values(by=["代號"])
    # Reset index
    df = df.reset_index(drop=True)
    return df
    