import requests
import pandas as pd
from io import StringIO
from model.data_type import DataType

# TODO: Stock calculate number unit: 1000 or 1?


REQUEST_SETTING = {
    DataType.PRICE: {
        "url": "https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php?l=zh-tw&o=csv&charset=UTF-8&d={date_str}&se=AL",
        "encoding": "utf-8",
        "header_num": 3,
    },
    DataType.FUNDAMENTAL: {
        "url": "https://www.tpex.org.tw/web/stock/aftertrading/peratio_analysis/pera_result.php?l=zh-tw&o=csv&charset=UTF-8&d={date_str}",
        "encoding": "utf-8",
        "header_num": 3,
    },  
    DataType.MARGIN_TRADING: {
        "url": "https://www.tpex.org.tw/web/stock/margin_trading/margin_balance/margin_bal_result.php?l=zh-tw&o=csv&charset=UTF-8&d={date_str}",
        "encoding": "utf-8",
        "header_num": 2,
    },
    DataType.INSTITUTIONAL: {
        "url": "https://www.tpex.org.tw/web/stock/3insti/daily_trade/3itrade_hedge_result.php?l=zh-tw&o=csv&d={date_str}&t=D",
        "encoding": "big-5",
        "header_num": 1,
    },
}


COLUMN_RENAME_SETTING = {
    "股票代號": "代號",
    "資買": "融資買進",
    "資賣": "融資賣出",
    "前資餘額(張)": "融資前日餘額",
    "資餘額": "融資今日餘額",
    "券買": "融券買進",
    "券賣": "融券賣出",
    "前券餘額(張)": "融券前日餘額",
    "券餘額": "融券今日餘額",
    "資券相抵(張)": "資券互抵",
    "外資及陸資(不含外資自營商)-買賣超股數": "外資買賣超股數",
    "投信-買賣超股數": "投信買賣超股數",
    "自營商-買賣超股數": "自營商買賣超股數",
    "三大法人買賣超股數合計": "三大法人買賣超股數",
}


COLUMN_KEEP_SETTING = {
    DataType.PRICE: ["代號", "名稱", "收盤", "漲跌", "開盤", "最高", "最低", "成交股數", "股票類型"],
    DataType.FUNDAMENTAL: ["代號", "名稱", "本益比", "股利年度", "殖利率(%)", "股價淨值比", "股票類型"],
    DataType.MARGIN_TRADING: ["代號", "名稱", "融資買進", "融資賣出", "融資前日餘額", "融資今日餘額", "融券買進", "融券賣出", "融券前日餘額", "融券今日餘額", "資券互抵", "融資變化量", "融券變化量", "券資比(%)", "股票類型"],
    DataType.INSTITUTIONAL: ["代號", "名稱", "外資買賣超股數", "投信買賣超股數", "自營商買賣超股數", "三大法人買賣超股數", "股票類型"],
}


def get_tpex_data(data_type, data_date):
    setting = REQUEST_SETTING[data_type]
    year, month, day = data_date.year - 1911, data_date.month, data_date.day
    date_str = f"{year}/{month:02}/{day:02}"
    url = setting["url"].format(date_str=date_str)
    response = requests.get(url)
    response.encoding = setting["encoding"]
    header_num = setting["header_num"]
    df = pd.read_csv(StringIO(response.text), header=header_num)
    return df


def clean_tpex_data(data_type, df):
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
    if data_type == DataType.MARGIN_TRADING:
        df["融資變化量"] = df["融資今日餘額"] - df["融資前日餘額"]
        df["融券變化量"] = df["融券今日餘額"] - df["融券前日餘額"]
        df["券資比(%)"] = round((df["融券今日餘額"] / df["融資今日餘額"]) * 100, 2)
    # Add the stock type column
    df["股票類型"] = "tpex"
    # Only keep the columns needed
    df = df[COLUMN_KEEP_SETTING[data_type]]  
    # Sort the rows
    df = df.sort_values(by=["代號"])
    # Reset index
    df = df.reset_index(drop=True)
    return df
    