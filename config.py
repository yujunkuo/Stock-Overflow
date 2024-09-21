import logging
from model.data_type import DataType

# TODO: We need more complicated configuration settings

# Logging configuration

logging.basicConfig(
    format="[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S %z",
    level=logging.INFO,
)

logger = logging.getLogger()


# Data column settings

COLUMN_RENAME_SETTING = {
    # TPEX Settings
    "股票代號": "代號",
    "資餘額": "融資餘額",
    "資買": "融資買進",
    "資賣": "融資賣出",
    "現償": "現金償還",
    "券餘額": "融券餘額",
    "券賣": "融券賣出",
    "券買": "融券買進",
    "券償": "現券償還",
    "外資及陸資(不含外資自營商)-買賣超股數": "外資買賣超股數",
    "投信-買賣超股數": "投信買賣超股數",
    "自營商-買賣超股數": "自營商買賣超股數",
    "三大法人買賣超股數合計": "三大法人買賣超股數",
    # TWSE Settings
    "證券代號": "代號",
    "證券名稱": "名稱",
    "開盤價": "開盤",
    "收盤價": "收盤",
    "最高價": "最高",
    "最低價": "最低",
    "今日餘額": "融資餘額",
    "買進": "融資買進",
    "賣出": "融資賣出",
    "今日餘額.1": "融券餘額",
    "賣出.1": "融券賣出",
    "買進.1": "融券買進",
    "外陸資買賣超股數(不含外資自營商)": "外資買賣超股數",
}


COLUMN_KEEP_SETTING = {
    DataType.PRICE: ["代號", "名稱", "開盤", "收盤", "最高", "最低", "漲跌", "成交股數", "股票類型"],
    DataType.FUNDAMENTAL: ["代號", "名稱", "本益比", "股價淨值比", "殖利率(%)", "股票類型"],
    DataType.MARGIN_TRADING: ["代號", "名稱", "融資餘額", "融資變化量", "融券餘額", "融券變化量", "券資比(%)", "股票類型"],
    DataType.INSTITUTIONAL: ["代號", "名稱", "外資買賣超股數", "投信買賣超股數", "自營商買賣超股數", "三大法人買賣超股數", "股票類型"],
}