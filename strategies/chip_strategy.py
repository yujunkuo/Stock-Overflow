## 籌碼面策略

##### 大戶動向 #####

# 1. (Public) 三大法人至少一個買超量大於等於今日總成交量的 N%
def single_institutional_buy_check_df(df, single_volume_threshold=10):
    return df.apply(_single_institutional_buy_check_row, single_volume_threshold=single_volume_threshold, axis=1)

def _single_institutional_buy_check_row(row, single_volume_threshold) -> bool:
    try:
        single_volume_threshold_actual = row["成交股數"] * (single_volume_threshold / 100)
        single_institutional_volume_list = [row["外資買賣超股數"], row["投信買賣超股數"], row["自營商買賣超股數"]]
        return any(volume >= single_volume_threshold_actual for volume in single_institutional_volume_list)
    except:
        return False


# 2. (Public) 三大法人合計總買超量大於等於今日總成交量的 N%
def total_institutional_buy_check_df(df, total_volume_threshold=10):
    return df.apply(_total_institutional_buy_check_row, total_volume_threshold=total_volume_threshold, axis=1)

def _total_institutional_buy_check_row(row, total_volume_threshold) -> bool:
    try:
        total_volume_threshold_actual = row["成交股數"] * (total_volume_threshold / 100)
        return row["三大法人買賣超股數"] >= total_volume_threshold_actual
    except:
        return False


# 3. (Public) 外資買超量大於等於今日總成交量的 N%
def foreign_buy_check_df(df, total_volume_threshold=10):
    return df.apply(_foreign_buy_check_row, total_volume_threshold=total_volume_threshold, axis=1)

def _foreign_buy_check_row(row, total_volume_threshold) -> bool:
    try:
        total_volume_threshold_actual = row["成交股數"] * (total_volume_threshold / 100)
        return row["外資買賣超股數"] >= total_volume_threshold_actual
    except:
        return False


# 4. (Public) 外資持股比大於等於 N%
def foreign_hold_percentage_check_df(df, hold_percentage_threshold=30):
    return df["外資持股比率(%)"] >= hold_percentage_threshold


# 5. (Public) 三大法人合計總買超量大於 N 股
def total_institutional_buy_positive_check_df(df, threshold=1e5):
    return df["三大法人買賣超股數"] > threshold

# 6. (Public) 外資買賣超股數大於 N 股 (Default=100張)
def foreign_buy_positive_check_df(df, threshold=1e5):
    return df["外資買賣超股數"] > threshold

# 7. (Public) 投信買賣超股數大於 N 股 (Default=100張)
def investment_buy_positive_check_df(df, threshold=1e5):
    return df["投信買賣超股數"] > threshold

# 8. (Public) 自營商買賣超股數大於 N 股 (Default=100張)
def dealer_buy_positive_check_df(df, threshold=1e5):
    return df["自營商買賣超股數"] > threshold

# 9. (Public) 自定義法人買超股數篩選
def buy_positive_check_df(df):
    return (df["外資買賣超股數"] >= 2e5) | (df["投信買賣超股數"] + df["自營商買賣超股數"] >= 2e5)

##### 散戶動向 #####

# 9. (Public) 融資增加張數大於等於總成交量的 N%
def margin_trading_check_df(df, margin_trading_threshold=1):
    return df["融資變化量"] >= (df["成交股數"] * (margin_trading_threshold / 100))


# 10. (Public) 融券減少張數大於等於總成交量的 N%
def short_selling_check_df(df, short_selling_threshold=1):
    return -(df["融券變化量"]) >= (df["成交股數"] * (short_selling_threshold / 100))


# 11. (Public) 券資比大於等於 N%
def short_margin_ratio_check_df(df, short_margin_ratio_threshold=5):
    return df["券資比(%)"] >= short_margin_ratio_threshold