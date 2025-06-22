import os

from models.data_type import DataType
from linebot import LineBotApi, WebhookHandler

# TODO: We need more complicated configuration settings
# TODO: add typing and comment language unification

class BasicConfig:
    """Base config class for shared configuration."""
    
    # Version year
    YEAR = "2025"

    # Version number
    VERSION = "v5.4"

    # Line Bot settings
    LINE_BOT_API = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN", "default_channel_access_token"))
    WEBHOOK_HANDLER = WebhookHandler(os.getenv("CHANNEL_SECRET", "default_channel_secret"))

    # API Access Token
    API_ACCESS_TOKEN = os.getenv("API_ACCESS_TOKEN", "default_api_access_token")

    # Data Settings
    COLUMN_RENAME_SETTING = {
        # TPEX Settings
        "股票代號": "代號",
        "公司名稱": "名稱",
        "成交股數": "成交量",
        "資餘額": "融資餘額",
        "資買": "融資買進",
        "資賣": "融資賣出",
        "現償": "現金償還",
        "券餘額": "融券餘額",
        "券賣": "融券賣出",
        "券買": "融券買進",
        "券償": "現券償還",
        "外資及陸資(不含外資自營商)-買賣超股數": "外資買賣超",
        "投信-買賣超股數": "投信買賣超",
        "自營商-買賣超股數": "自營商買賣超",
        "三大法人買賣超股數合計": "三大法人買賣超",
        # TWSE Settings
        "證券代號": "代號",
        "證券名稱": "名稱",
        "開盤價": "開盤",
        "收盤價": "收盤",
        "最高價": "最高",
        "最低價": "最低",
        "成交股數": "成交量",
        "今日餘額": "融資餘額",
        "買進": "融資買進",
        "賣出": "融資賣出",
        "今日餘額.1": "融券餘額",
        "賣出.1": "融券賣出",
        "買進.1": "融券買進",
        "外陸資買賣超股數(不含外資自營商)": "外資買賣超",
        "投信買賣超股數": "投信買賣超",
        "自營商買賣超股數": "自營商買賣超",
        "三大法人買賣超股數": "三大法人買賣超",
        # Industry Category Settings
        "stock_id": "代號",
        "stock_name": "名稱",
        "industry_category": "產業別",
        "type": "股票類型",
    }

    # Data Settings
    COLUMN_KEEP_SETTING = {
        DataType.PRICE: ["代號", "名稱", "開盤", "收盤", "最高", "最低", "漲跌", "成交量", "股票類型"],
        DataType.FUNDAMENTAL: ["代號", "名稱", "本益比", "股價淨值比", "殖利率(%)", "股票類型"],
        DataType.MARGIN_TRADING: ["代號", "名稱", "融資餘額", "融資變化量", "融券餘額", "融券變化量", "券資比(%)", "股票類型"],
        DataType.INSTITUTIONAL: ["代號", "名稱", "外資買賣超", "投信買賣超", "自營商買賣超", "三大法人買賣超", "股票類型"],
        DataType.INDUSTRY_CATEGORY: ["代號", "名稱", "產業別", "股票類型"],
        DataType.MOM_YOY: ["代號", "名稱", "(月)營收月增率(%)", "(月)營收年增率(%)", "(月)累積營收年增率(%)"],
    }
