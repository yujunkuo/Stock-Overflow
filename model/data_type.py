from enum import Enum

class DataType(Enum):
    PRICE = "price"
    FUNDAMENTAL = "fundamental"
    MARGIN_TRADING = "margin_trading"
    INSTITUTIONAL = "institutional"
    INDUSTRY_CATEGORY = "industry_category"
    MOM_YOY = "mom_yoy"
    