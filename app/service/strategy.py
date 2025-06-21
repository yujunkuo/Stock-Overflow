# Third-party imports
import pandas as pd

# Local imports
from app.rule.core import chip, technical


# Get the strategy 1
def get_strategy_1(market_data_df: pd.DataFrame) -> tuple:
    # Fundamental strategy filters
    fundamental_mask = [
        # 營收成長至少其中一項 > 0%
        (market_data_df["(月)營收月增率(%)"] > 0) |\
        (market_data_df["(月)營收年增率(%)"] > 0) |\
        (market_data_df["(月)累積營收年增率(%)"] > 0),
    ]

    # Technical strategy filters
    technical_mask = [
        # 收盤價 > 20
        technical.technical_indicator_constant_check_df(
            market_data_df,
            indicator="收盤",
            direction="more",
            threshold=20,
            days=1,
        ),
        # MA1 > MA5
        technical.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="收盤",
            indicator_2="mean5",
            direction="more",
            threshold=1,
            days=1,
        ),
        # MA5 > MA20
        technical.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="mean5",
            indicator_2="mean20",
            direction="more",
            threshold=1,
            days=1,
        ),
        # MA20 > MA60
        technical.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="mean20",
            indicator_2="mean60",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 收盤價 > 1.01 * 開盤價 (今天收紅 K & 實體 K 棒漲幅大於 1%)
        technical.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="收盤",
            indicator_2="開盤",
            direction="more",
            threshold=1.01,
            days=1,
        ),
        # # K 棒底底高
        # (technical.technical_indicator_greater_or_less_two_day_check_df(market_data_df, indicator_1="開盤", indicator_2="開盤", direction="more", threshold=1, days=1) |\
        # technical.technical_indicator_greater_or_less_two_day_check_df(market_data_df, indicator_1="開盤", indicator_2="收盤", direction="more", threshold=1, days=1)),
        # # 今天開盤價 > 昨天收盤價
        # technical.technical_indicator_greater_or_less_two_day_check_df(market_data_df, indicator_1="開盤", indicator_2="收盤", direction="more", threshold=1, days=1),
        # 今天收盤 > 昨天最高
        technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="收盤",
            indicator_2="最高",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 今天 K9 > 昨天 K9
        technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="k9",
            indicator_2="k9",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 今天 D9 < 90
        technical.technical_indicator_constant_check_df(
            market_data_df, 
            indicator="d9", 
            direction="less", 
            threshold=90, 
            days=1,
        ),
        # # 今天 OSC > 昨天 OSC
        # technical.technical_indicator_greater_or_less_two_day_check_df(market_data_df, indicator_1="osc", indicator_2="osc", direction="more", threshold=1, days=1),
        # |D9 - K9| < 22
        technical.technical_indicator_difference_one_day_check_df(
            market_data_df,
            indicator_1="k9",
            indicator_2="d9",
            difference_threshold=22,
            days=1,
        ),
        # # K9 between 49 ~ 87
        # technical.technical_indicator_constant_check_df(market_data_df, indicator="k9", direction="more", threshold=49, days=1),
        # technical.technical_indicator_constant_check_df(market_data_df, indicator="k9", direction="less", threshold=87, days=1),
        # J9 < 100
        technical.technical_indicator_constant_check_df(
            market_data_df, indicator="j9", direction="less", threshold=100, days=1
        ),
        # # (今天 k9-d9) >= (昨天 k9-d9)
        # technical.technical_indicator_difference_greater_two_day_check_df(market_data_df, indicator_1="k9", indicator_2="d9", days=1),
        # # MA5 趨勢向上
        # technical.technical_indicator_greater_or_less_two_day_check_df(market_data_df, indicator_1="mean5", indicator_2="mean5", direction="more", threshold=1, days=1),
        # 今天收盤 > 1.03 * 昨天收盤 (漲幅 3% 以上)
        technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="收盤",
            indicator_2="收盤",
            direction="more",
            threshold=1.03,
            days=1,
        ),
        # 不能連續兩天漲幅都超過 5%
        ~technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="收盤",
            indicator_2="收盤",
            direction="more",
            threshold=1.05,
            days=2,
        ),
        # # 今天收盤 < 1.1 * Mean5 or Mean10 or Mean20 (均線乖離不能過大)
        # technical.technical_indicator_greater_or_less_one_day_check_df(market_data_df, indicator_1="收盤", indicator_2="mean5", direction="less", threshold=1.1, days=1) |\
        # technical.technical_indicator_greater_or_less_one_day_check_df(market_data_df, indicator_1="收盤", indicator_2="mean10", direction="less", threshold=1.1, days=1) |\
        # technical.technical_indicator_greater_or_less_one_day_check_df(market_data_df, indicator_1="收盤", indicator_2="mean20", direction="less", threshold=1.1, days=1),
        # # 今天最高價不是四個月內最高 (只抓得到四個月的資料)
        # technical.today_price_is_not_max_check_df(market_data_df, price_type="最高", days=80),
        # 上影線長度不能超過昨天收盤價的 3% (0.03) / 0% (0.000001) 以上
        technical.technical_indicator_difference_two_day_check_df(
            market_data_df,
            indicator_1="最高",
            indicator_2="收盤",
            direction="less",
            threshold=0.03,
            indicator_3="收盤",
            days=1,
        ),
        # # OSC > 0 (出現強勁漲幅的機會較高)
        # technical.technical_indicator_constant_check_df(market_data_df, indicator="osc", direction="more", threshold=0, days=1),
        # # DIF > 0
        # technical.technical_indicator_constant_check_df(market_data_df, indicator="dif", direction="more", threshold=0, days=1),
        # # [(DIF / 收盤價) < 0.03] 或 [DIF 不是四個月內的最高]
        # technical.technical_indicator_greater_or_less_one_day_check_df(
        #     market_data_df,
        #     indicator_1="dif",
        #     indicator_2="收盤",
        #     direction="less",
        #     threshold=0.03,
        #     days=1,
        # )
        # | technical.today_price_is_not_max_check_df(
        #     market_data_df, price_type="dif", days=80
        # ),
    ]

    # Chip strategy filters
    chip_mask = [
        # 成交量 > 2000 張
        technical.volume_greater_check_df(
            market_data_df,
            shares_threshold=2000,
            days=1,
        ),
        # 今天成交量 > 昨天成交量
        technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="volume",
            indicator_2="volume",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 今天成交量 > 5日均量
        technical.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="volume",
            indicator_2="mean5volume",
            direction="more",
            threshold=1,
            days=1,
        ),
        # # 5日均量 > 20日均量
        # technical.technical_indicator_greater_or_less_one_day_check_df(market_data_df, indicator_1="mean5volume", indicator_2="mean20volume", direction="more", threshold=1, days=1),
        # 5日均量 > 1000 張
        technical.technical_indicator_constant_check_df(
            market_data_df,
            indicator="mean5volume",
            direction="more",
            threshold=1000,
            days=1,
        ),
        # 20日均量 > 1000 張
        technical.technical_indicator_constant_check_df(
            market_data_df,
            indicator="mean20volume",
            direction="more",
            threshold=1000,
            days=1,
        ),
        # 「今天的5日均量」要大於「昨天的5日均量」
        technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="mean5volume",
            indicator_2="mean5volume",
            direction="more",
            threshold=1,
            days=1,
        ),
        # # 單一法人至少買超成交量的 10%
        # chip.single_institutional_buy_check_df(market_data_df, single_volume_threshold=10),
        # # 法人合計至少買超成交量的 1%
        # chip.total_institutional_buy_check_df(market_data_df, total_volume_threshold=1),
        # 外資買超 >= 0 張
        chip.foreign_buy_positive_check_df(market_data_df, threshold=0),
        # # 投信買超 >= 50 張
        # chip.investment_buy_positive_check_df(market_data_df, threshold=50),
        # # 自定義法人買超篩選
        # chip.buy_positive_check_df(market_data_df),
        # # 法人合計買超 >= 0 張
        # chip.total_institutional_buy_positive_check_df(market_data_df, threshold=0),
    ]
    return fundamental_mask, technical_mask, chip_mask


# Get the strategy 2
def get_strategy_2(market_data_df: pd.DataFrame) -> tuple:
    fundamental_mask = [
        # 營收成長至少其中一項 > 0%
        (market_data_df["(月)營收月增率(%)"] > 0) |\
        (market_data_df["(月)營收年增率(%)"] > 0) |\
        (market_data_df["(月)累積營收年增率(%)"] > 0),
    ]
    technical_mask = [
        # 收盤價 > 20
        technical.technical_indicator_constant_check_df(
            market_data_df,
            indicator="收盤",
            direction="more",
            threshold=20,
            days=1,
        ),
        # MA1 > MA5
        technical.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="收盤",
            indicator_2="mean5",
            direction="more",
            threshold=1,
            days=1,
        ),
        # MA1 > MA20
        technical.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="收盤",
            indicator_2="mean20",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 今天 MA60 > 昨天 MA60
        technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="mean60",
            indicator_2="mean60",
            direction="more",
            threshold=1,
            days=1,
        ),
        # K9 > D9
        technical.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="k9",
            indicator_2="d9",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 今天 J9 > 昨天 J9
        technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="j9",
            indicator_2="j9",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 今天 OSC > 昨天 OSC
        technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="osc",
            indicator_2="osc",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 今天 J9 < 100
        technical.technical_indicator_constant_check_df(
            market_data_df, indicator="j9", direction="less", threshold=100, days=1
        ),
    ]
    chip_mask = [
        # 成交量 > 1500 張
        technical.volume_greater_check_df(
            market_data_df,
            shares_threshold=1500,
            days=1,
        ),
        # 今天成交量 > 昨天成交量
        technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="volume",
            indicator_2="volume",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 今天成交量 > 5日均量
        technical.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="volume",
            indicator_2="mean5volume",
            direction="more",
            threshold=1,
            days=1,
        ),
    ]
    return fundamental_mask, technical_mask, chip_mask


# Get the strategy 3
def get_strategy_3(market_data_df: pd.DataFrame) -> tuple:
    # Fundamental strategy filters
    fundamental_mask = []
    # Technical strategy filters
    technical_mask = [
        # 收盤價 > 20
        technical.technical_indicator_constant_check_df(
            market_data_df,
            indicator="收盤",
            direction="more",
            threshold=20,
            days=1,
        ),
        # 今天收盤 > 1.01 * 昨天收盤 (漲幅 1% 以上)
        technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="收盤",
            indicator_2="收盤",
            direction="more",
            threshold=1.01,
            days=1,
        ),
        # 今天收紅 K
        technical.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="收盤",
            indicator_2="開盤",
            direction="more",
            threshold=1,
            days=1,
        ),
        # MA1 > MA60
        technical.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="收盤",
            indicator_2="mean60",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 今天 MA60 > 昨天 MA60
        technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="mean60",
            indicator_2="mean60",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 五天內最低價曾經跌到 MA20 以下
        ~technical.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="最低",
            indicator_2="mean20",
            direction="more",
            threshold=1,
            days=5,
        ),
        # 昨天下跌
        ~technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="收盤",
            indicator_2="收盤",
            direction="more",
            threshold=1,
            days=2,
        ),
        # 今天 K9 > 昨天 K9
        technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="k9",
            indicator_2="k9",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 今天 K9 > 20
        technical.technical_indicator_constant_check_df(
            market_data_df,
            indicator="k9",
            direction="more",
            threshold=20,
            days=1,
        ),
    ]
    # Chip strategy filters
    chip_mask = [
        # 今天成交量 < 昨天成交量
        technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="volume",
            indicator_2="volume",
            direction="less",
            threshold=1,
            days=1,
        ),
        # 外資買超 >= 0 張
        chip.foreign_buy_positive_check_df(market_data_df, threshold=0),
    ]
    return fundamental_mask, technical_mask, chip_mask
