"""
Technical Analysis Rules

This module provides technical analysis rules for stock screening.
"""

# Standard library imports
import time
import datetime

# Third-party imports
import twstock
import pandas as pd
# from ta.trend import PSARIndicator

# Local imports
from app.core import logger
from app.rule.common.utils import get_last_n_days_data
from app.rule.common.base import OneIndicatorRule, TwoIndicatorsRule, ThreeIndicatorsRule


# ===== Technical Rules =====

class IndicatorMaxRule(OneIndicatorRule):
    """Rule to check if today's indicator is the maximum in the last N days."""
    
    def __init__(self, indicator="收盤", days=3, name=None, description=None):
        super().__init__(indicator, days, name, description)
    
    def apply(self, df: pd.DataFrame) -> pd.Series:
        def check_row(row):
            try:
                data = get_last_n_days_data(row, self.indicator, self.days)
                return data[0] == max(data)
            except:
                return False
        return df.apply(check_row, axis=1)
    

class IndicatorMinRule(OneIndicatorRule):
    """Rule to check if today's indicator is the minimum in the last N days."""
    
    def __init__(self, indicator="收盤", days=3, name=None, description=None):
        super().__init__(indicator, days, name, description)
    
    def apply(self, df: pd.DataFrame) -> pd.Series:
        def check_row(row):
            try:
                data = get_last_n_days_data(row, self.indicator, self.days)
                return data[0] == min(data)
            except:
                return False
        return df.apply(check_row, axis=1)
    

class IndicatorNotMaxRule(OneIndicatorRule):
    """Rule to check if today's indicator is not the maximum in the last N days."""
    
    def __init__(self, indicator="收盤", days=3, name=None, description=None):
        super().__init__(indicator, days, name, description)    
    
    def apply(self, df: pd.DataFrame) -> pd.Series:
        def check_row(row):
            try:
                data = get_last_n_days_data(row, self.indicator, self.days)
                return data[0] != max(data)
            except:
                return False
        return df.apply(check_row, axis=1)
    

class IndicatorNotMinRule(OneIndicatorRule):
    """Rule to check if today's indicator is not the minimum in the last N days."""
    
    def __init__(self, indicator="收盤", days=3, name=None, description=None):
        super().__init__(indicator, days, name, description)    
    
    def apply(self, df: pd.DataFrame) -> pd.Series:
        def check_row(row):
            try:
                data = get_last_n_days_data(row, self.indicator, self.days)
                return data[0] != min(data)
            except:
                return False
        return df.apply(check_row, axis=1)


class IndicatorAboveThresholdRule(OneIndicatorRule):
    """Rule to check if an indicator has been consistently above a threshold for the last N days."""
    
    def __init__(self, indicator="volume", threshold=1e3, days=3, name=None, description=None):
        super().__init__(indicator, days, name, description)
        self.threshold = threshold
    
    def apply(self, df: pd.DataFrame) -> pd.Series:
        def check_row(row):
            try:
                data = get_last_n_days_data(row, self.indicator, self.days)
                return all(d >= self.threshold for d in data)
            except:
                return False
        return df.apply(check_row, axis=1)


class IndicatorBelowThresholdRule(OneIndicatorRule):
    """Rule to check if an indicator has been consistently below a threshold for the last N days."""
    
    def __init__(self, indicator="volume", threshold=1e3, days=3, name=None, description=None):
        super().__init__(indicator, days, name, description)
        self.threshold = threshold
    
    def apply(self, df: pd.DataFrame) -> pd.Series:
        def check_row(row):
            try:
                data = get_last_n_days_data(row, self.indicator, self.days)
                return all(d <= self.threshold for d in data)
            except:
                return False
        return df.apply(check_row, axis=1)
    

class IndicatorComparisonRule(TwoIndicatorsRule):
    """Rule to check if today's indicator_1 is consistently more/less than [threshold * today's indicator_2] for the last N days."""
    
    def __init__(self, indicator_1="收盤", indicator_2="mean5", direction="more", threshold=1, days=3, name=None, description=None):
        super().__init__(indicator_1, indicator_2, days, name, description)
        self.direction = direction
        self.threshold = threshold
    
    def apply(self, df: pd.DataFrame) -> pd.Series:
        def check_row(row):
            try:
                data_1 = get_last_n_days_data(row, self.indicator_1, self.days)
                data_2 = get_last_n_days_data(row, self.indicator_2, self.days)
                if self.direction == "more":
                    return all(d1 >= (self.threshold * d2) for d1, d2 in zip(data_1, data_2))
                else:
                    return all(d1 <= (self.threshold * d2) for d1, d2 in zip(data_1, data_2))
            except:
                return False
        return df.apply(check_row, axis=1)


class IndicatorComparisonToYesterdayRule(TwoIndicatorsRule):
    """Rule to check if today's indicator_1 is consistently more/less than [threshold * yesterday's indicator_2] for the last N days."""
    
    def __init__(self, indicator_1="k9", indicator_2="k9", direction="more", threshold=1, days=3, name=None, description=None):
        super().__init__(indicator_1, indicator_2, days, name, description)
        self.direction = direction
        self.threshold = threshold
    
    def apply(self, df: pd.DataFrame) -> pd.Series:
        def check_row(row):
            try:
                data_1 = get_last_n_days_data(row, self.indicator_1, self.days)
                data_2 = get_last_n_days_data(row, self.indicator_2, self.days + 1)
                if self.direction == "more":
                    return all(d1 >= (self.threshold * d2) for d1, d2 in zip(data_1, data_2[1:]))
                else:
                    return all(d1 <= (self.threshold * d2) for d1, d2 in zip(data_1, data_2[1:]))
            except:
                return False
        return df.apply(check_row, axis=1)


class IndicatorDifferenceToThresholdRule(TwoIndicatorsRule):
    """Rule to check if the absolute difference between today's indicator_1 and indicator_2 is consistently more/less than a threshold for the last N days."""
    
    def __init__(self, indicator_1="k9", indicator_2="d9", direction="more", threshold=10, days=3, name=None, description=None):
        super().__init__(indicator_1, indicator_2, days, name, description)
        self.direction = direction
        self.threshold = threshold
    
    def apply(self, df: pd.DataFrame) -> pd.Series:
        def check_row(row):
            try:
                data_1 = get_last_n_days_data(row, self.indicator_1, self.days)
                data_2 = get_last_n_days_data(row, self.indicator_2, self.days)
                if self.direction == "more":
                    return all(abs(d1 - d2) >= self.threshold for d1, d2 in zip(data_1, data_2))
                else:
                    return all(abs(d1 - d2) <= self.threshold for d1, d2 in zip(data_1, data_2))
            except:
                return False
        return df.apply(check_row, axis=1)


class IndicatorDifferenceToYesterdayRule(ThreeIndicatorsRule):
    """Rule to check if the absolute difference between today's indicator_1 and indicator_2 is consistently more/less than [threshold * yesterday's indicator_3] for the last N days."""
    def __init__(self, indicator_1="最高", indicator_2="收盤", indicator_3="收盤", direction="less", threshold=0.1, days=3, name=None, description=None):
        super().__init__(indicator_1, indicator_2, indicator_3, days, name, description)
        self.direction = direction
        self.threshold = threshold
    
    def apply(self, df: pd.DataFrame) -> pd.Series:
        def check_row(row):
            try:
                data_1 = get_last_n_days_data(row, self.indicator_1, self.days)
                data_2 = get_last_n_days_data(row, self.indicator_2, self.days)
                data_3 = get_last_n_days_data(row, self.indicator_3, self.days + 1)
                if self.direction == "more":
                    return all(abs(d1 - d2) >= self.threshold * d3 for d1, d2, d3 in zip(data_1, data_2, data_3[1:]))
                else:
                    return all(abs(d1 - d2) <= self.threshold * d3 for d1, d2, d3 in zip(data_1, data_2, data_3[1:]))
            except:
                return False
        return df.apply(check_row, axis=1)


class IndicatorGoldenCrossRule(TwoIndicatorsRule):
    def __init__(self, indicator_1="k9", indicator_2="d9", days=3, name=None, description=None):
        super().__init__(indicator_1, indicator_2, days, name, description)
    
    def apply(self, df: pd.DataFrame) -> pd.Series:
        def check_row(row):
            try:
                data_1 = get_last_n_days_data(row, self.indicator_1, self.days)
                data_2 = get_last_n_days_data(row, self.indicator_2, self.days)
                return data_1[0] >= data_2[0] and any(d1 <= d2 for d1, d2 in zip(data_1[1:], data_2[1:]))
            except:
                return False
        return df.apply(check_row, axis=1)


# TODO: 去除重複的 class，改成傳入 more/less，並驗證傳入的內容一定在 (more, less) 內
# TODO: 實作 is_skyrocket
# # 12. (Public) [twstock] 檢查該股票是否具備飆股特徵 (自定義長短線特徵)
# def is_skyrocket(
#     stock_id, n_days=10, k_change=0.20, consecutive_red_no_upper_shadow_days=2
# ):
#     try:
#         time.sleep(5)
#         stock = twstock.Stock(stock_id)
#         six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)
#         historical_data = stock.fetch_from(six_months_ago.year, six_months_ago.month)[:-5]
#         # 檢查飆股兩個面向特徵
#         long_term_flag, short_term_flag = False, False
#         # 檢查是否有在任意 n_days 內漲幅達 k_change
#         for i in range(len(historical_data) - n_days):
#             start, end = historical_data[i].close, historical_data[i + n_days].close
#             if (end - start) / start >= k_change:
#                 long_term_flag = True
#                 break
#         # 檢查是否有在任意 consecutive_red_no_upper_shadow_days 內每天都漲幅大於 9% 且收在最高
#         for i in range(len(historical_data) - consecutive_red_no_upper_shadow_days + 1):
#             if all(
#                 (d.close == d.high) and (d.close / (d.close - d.change) > 1.09)
#                 for d in historical_data[i : i + consecutive_red_no_upper_shadow_days]
#             ):
#                 short_term_flag = True
#                 break
#         logger.info(f"{stock_id}: [long_term = {long_term_flag} / short_term = {short_term_flag} / data_length = {len(historical_data)}]")
#         return long_term_flag and short_term_flag
#     except:
#         logger.info(f"{stock_id}: [取得歷史資料失敗]")
#         return False


# # 13. (Public) [twstock] 檢查該股票 SAR 是否大於收盤價
# def is_sar_above_close(stock_id):
#     try:
#         time.sleep(5)
#         stock = twstock.Stock(stock_id)
#         six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)
#         historical_data = stock.fetch_from(six_months_ago.year, six_months_ago.month)
#         data = pd.DataFrame({
#             "high": [record.high for record in historical_data],
#             "low": [record.low for record in historical_data],
#             "close": [record.close for record in historical_data],
#         })
#         sar = PSARIndicator(high=data["high"], low=data["low"], close=data["close"], step=0.02, max_step=0.2)
#         sar_list = sar.psar().to_list()
#         logger.info(f"{stock_id}: [close_price = {historical_data[-1].close} / SAR_indicator = {round(sar_list[-1], 2)} / data_length = {len(historical_data)}]")
#         return sar_list[-1] > historical_data[-1].close
#     except:
#         logger.info(f"{stock_id}: [取得歷史資料失敗]")
#         return False