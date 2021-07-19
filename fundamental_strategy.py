import requests
from bs4 import BeautifulSoup
import datetime
import time
import random
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO
import json
from functools import reduce

## 基本面策略

# 1. (Public) 本益比小於等於 N
def per_check_df(df, per_threshold=15):
    return df["本益比"] <= per_threshold


# 2. (Public) 殖利率大於等於 N
def dividend_yield_check_df(df, dividend_yield_threshold=1.5):
    return df["殖利率(%)"] >= dividend_yield_threshold


# 3. (Public) 股價淨值比小於等於 N
def pbr_check_df(df, pbr_threshold=2):
    return df["股價淨值比"] <= pbr_threshold


# 4. (Public) 月營收年增率(YoY) 大於等於 N%
def yoy_check_df(df, yoy_threshold=10):
    return df["(月)營收年增率(%)"] >= yoy_threshold


# 5. (Public) 月營收月增率(MoM) 大於等於 N%
def mom_check_df(df, mom_threshold=10):
    return df["(月)營收月增率(%)"] >= mom_threshold


# 6. (Public) 月累積營收年增率(Acc-YoY) 大於等於 N%
def acc_yoy_check_df(df, acc_yoy_threshold=10):
    return df["(月)累積營收年增率(%)"] >= acc_yoy_threshold