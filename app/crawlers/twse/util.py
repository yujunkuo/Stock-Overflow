import time
import requests
import pandas as pd

from io import StringIO
from model.data_type import DataType
from config.config import logger, COLUMN_RENAME_SETTING, COLUMN_KEEP_SETTING

# TODO: Stock calculate number unit: 1000 or 1?
# TODO: When to fillna?

MAX_REQUEST_RETRIES = 3

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
        "url": "https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN?response=csv&date={date_str}&selectType=ALL",
        "header_num": 7,
    },
    DataType.INSTITUTIONAL: {
        "url": "https://www.twse.com.tw/rwd/zh/fund/T86?response=csv&date={date_str}&selectType=ALL",
        "header_num": 1,
    },
}


def _request_data(data_type, data_date):
    for _ in range(MAX_REQUEST_RETRIES):
        try:
            setting = REQUEST_SETTING[data_type]
            year, month, day = data_date.year, data_date.month, data_date.day
            date_str = f"{year}{month:02}{day:02}"
            url = setting["url"].format(date_str=date_str)
            response = requests.get(url)
            header_num = setting["header_num"]
            if data_type == DataType.PRICE:
                header_num = ["證券代號" in line for line in response.text.split("\n")].index(True) - 1
            df = pd.read_csv(StringIO(response.text.replace("=", "")), header=header_num)
            return df
        except:
            logger.warning(f"Attempt {_request_data.__name__} for {data_type.value} failed.")
            time.sleep(3)
    return pd.DataFrame(columns=COLUMN_KEEP_SETTING[data_type])


def _clean_data(data_type, df):
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
            if s.name not in ["代號", "名稱", "漲跌(+/-)"]
            else s
        )
    )
    # Add additional columns
    if data_type == DataType.PRICE:
        df["漲跌(+/-)"] = df["漲跌(+/-)"].map({"+": 1, "-": -1, " ": 0, "X": 0})
        df["漲跌"] = df["漲跌(+/-)"] * df["漲跌價差"]
    if data_type == DataType.MARGIN_TRADING:
        df["融資變化量"] = df["融資買進"] - df["融資賣出"] - df["現金償還"]
        df["融券變化量"] = df["融券賣出"] - df["融券買進"] - df["現券償還"]
        df["券資比(%)"] = round((df["融券餘額"] / df["融資餘額"]) * 100, 2).fillna(0)
    # Add the stock type column
    df["股票類型"] = "twse"
    # Only keep the columns needed
    df = df[COLUMN_KEEP_SETTING[data_type]]  
    # Sort the rows
    df = df.sort_values(by=["代號"])
    # Reset index
    df = df.reset_index(drop=True)
    return df


# Get the TWSE data
def get_data(data_type, data_date):
    df = _request_data(data_type, data_date)
    df = _clean_data(data_type, df)
    return df
 