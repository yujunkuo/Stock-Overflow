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

## 工具函數

# (Public) 從 df 中透過多個條件 mask_list 取交集來過濾
def df_mask_helper(df, mask_list):
    return df[reduce(lambda x, y: (x & y), mask_list)]