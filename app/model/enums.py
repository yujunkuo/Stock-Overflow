# Standard library imports
from enum import Enum

class DataType(Enum):
    # TPEX and TWSE API
    PRICE = "price"
    FUNDAMENTAL = "fundamental"
    MARGIN_TRADING = "margin_trading"
    INSTITUTIONAL = "institutional"
    # Other API
    INDUSTRY_CATEGORY = "industry_category"
    MOM_YOY = "mom_yoy"


class ComparisonType(Enum):
    LESS_THAN = "less_than"
    GREATER_THAN = "greater_than" 
    BETWEEN = "between"