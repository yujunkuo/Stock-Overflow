import datetime
from functools import reduce

## 工具函數

# (Public) 從 df 中透過多個條件 mask_list 取交集來過濾
def df_mask_helper(df, mask_list):
    return df[reduce(lambda x, y: (x & y), mask_list)]


# 計算當前時間是否介於兩時間之間
def check_time_between(begin_time, end_time):
    # 當前時間
    check_time = datetime.datetime.now().time()
    # 判斷區間
    if begin_time < end_time:
        return check_time >= begin_time and check_time < end_time
    else: # 跨過午夜
        return check_time >= begin_time or check_time < end_time


# 計算今天是否為工作日
def check_weekday():
    # 當前日期
    check_date = datetime.datetime.now().date()
    # 當前工作日計數 (Monday=0, Tuesday=1, ... ,Sunday=6)
    weekday_count = check_date.weekday()
    # 判斷是否為工作日
    is_weekday = False if weekday_count in [5, 6] else True
    return is_weekday
    