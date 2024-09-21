from datetime import datetime
from functools import reduce

# Convert timestamp in milliseconds to date
def convert_milliseconds_to_date(timestamp_ms: int):
    return datetime.fromtimestamp(timestamp_ms / 1000).date()


# Filter dataframe with multiple conditions in mask_list
def df_mask_helper(df, mask_list):
    return df[reduce(lambda x, y: (x & y), mask_list)]


# Check if the input date is a weekday
def is_weekday(check_date=None):
    if not check_date:
        check_date = datetime.now().date()
    # 當前工作日計數 (Monday=0, Tuesday=1, ... ,Sunday=6)
    weekday_count = check_date.weekday()
    # 判斷是否為工作日
    is_weekday = False if weekday_count in [5, 6] else True
    return is_weekday
