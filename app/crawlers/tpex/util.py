import time
import requests
import pandas as pd

from io import StringIO
from models.data_type import DataType
from config import config, logger

MAX_REQUEST_RETRIES = 3

REQUEST_SETTING = {
    DataType.PRICE: {
        "url": "https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php?l=zh-tw&o=csv&charset=UTF-8&d={date_str}&se=AL",
        "headers": {
            "Host": "www.tpex.org.tw",
        },
        "encoding": "big5",
        "header_num": 3,
    },
    DataType.FUNDAMENTAL: {
        "url": "https://www.tpex.org.tw/web/stock/aftertrading/peratio_analysis/pera_result.php?l=zh-tw&o=csv&charset=UTF-8&d={date_str}",
        "headers": {
            "Host": "www.tpex.org.tw",
        },
        "encoding": "big5",
        "header_num": 3,
    },  
    DataType.MARGIN_TRADING: {
        "url": "https://www.tpex.org.tw/web/stock/margin_trading/margin_balance/margin_bal_result.php?l=zh-tw&o=csv&charset=UTF-8&d={date_str}",
        "headers": {
            "Host": "www.tpex.org.tw",
        },
        "encoding": "big5",
        "header_num": 2,
    },
    DataType.INSTITUTIONAL: {
        "url": "https://www.tpex.org.tw/web/stock/3insti/daily_trade/3itrade_hedge_result.php?l=zh-tw&o=csv&d={date_str}&t=D",
        "headers": {
            "Host": "www.tpex.org.tw",
        },
        "encoding": "big5",
        "header_num": 1,
    },
}


def _request_data(data_type, data_date):
    for _ in range(MAX_REQUEST_RETRIES):
        try:
            setting = REQUEST_SETTING[data_type]
            year, month, day = data_date.year - 1911, data_date.month, data_date.day
            date_str = f"{year}/{month:02}/{day:02}"
            url = setting["url"].format(date_str=date_str)
            response = requests.get(url, headers=setting["headers"])
            response.encoding = setting["encoding"]
            header_num = setting["header_num"]
            df = pd.read_csv(StringIO(response.text), header=header_num)
            return df
        except:
            logger.warning(f"Attempt {_request_data.__name__} for {data_type.value} failed.")
            time.sleep(3)
    return pd.DataFrame(columns=config.COLUMN_KEEP_SETTING[data_type])


def _clean_data(data_type, df):
    # If the DataFrame is empty, return it directly
    if df.empty:
        return df
    # Remove leading and trailing spaces from column names
    df.columns = [column.strip() for column in df.columns]
    # Unify the column names of the stock code
    df = df.rename(columns=config.COLUMN_RENAME_SETTING)
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
        df["成交量"] = round(df["成交量"] / 1000)
    if data_type == DataType.MARGIN_TRADING:
        df["融資變化量"] = df["融資買進"] - df["融資賣出"] - df["現金償還"]
        df["融券變化量"] = df["融券賣出"] - df["融券買進"] - df["現券償還"]
        df["券資比(%)"] = round((df["融券餘額"] / df["融資餘額"]) * 100, 2).fillna(0)
    if data_type == DataType.INSTITUTIONAL:
        df["外資買賣超"] = round(df["外資買賣超"] / 1000)
        df["投信買賣超"] = round(df["投信買賣超"] / 1000)
        df["自營商買賣超"] = round(df["自營商買賣超"] / 1000)
        df["三大法人買賣超"] = round(df["三大法人買賣超"] / 1000)
    # Add the stock type column
    df["股票類型"] = "tpex"
    # Only keep the columns needed
    df = df[config.COLUMN_KEEP_SETTING[data_type]]  
    # Sort the rows
    df = df.sort_values(by=["代號"])
    # Reset index
    df = df.reset_index(drop=True)
    return df


# Get the TPEX data
def get_data(data_type, data_date):
    df = _request_data(data_type, data_date)
    df = _clean_data(data_type, df)
    return df
