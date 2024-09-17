from datetime import datetime
from functools import reduce

## 工具函數

# (Public) 從 df 中透過多個條件 mask_list 取交集來過濾
def df_mask_helper(df, mask_list):
    return df[reduce(lambda x, y: (x & y), mask_list)]


# 計算今天是否為工作日
def is_weekday(check_date=None):
    if not check_date:
        check_date = datetime.now().date()
    # 當前工作日計數 (Monday=0, Tuesday=1, ... ,Sunday=6)
    weekday_count = check_date.weekday()
    # 判斷是否為工作日
    is_weekday = False if weekday_count in [5, 6] else True
    return is_weekday
