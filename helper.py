import requests
from bs4 import BeautifulSoup
import datetime
import time
import random
import pandas as pd
import numpy as np
from io import StringIO
import json
from functools import reduce

## 工具函數

# (Public) 從 df 中透過多個條件 mask_list 取交集來過濾
def df_mask_helper(df, mask_list):
    return df[reduce(lambda x, y: (x & y), mask_list)]


# 計算當前時間是否介於兩時間之間
def check_time_between(begin_time, end_time, check_time=datetime.datetime.now().time()):
    if begin_time < end_time:
        return check_time >= begin_time and check_time < end_time
    else: # 跨過午夜
        return check_time >= begin_time or check_time < end_time
    
    