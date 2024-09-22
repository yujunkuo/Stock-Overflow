## Fundamental Strategies


# 1. PE Ratio is less than or equal to <per_threshold>
def per_check_df(df, per_threshold=15):
    return df["本益比"] <= per_threshold


# 2. PB Ratio is less than or equal to <pbr_threshold>
def pbr_check_df(df, pbr_threshold=2):
    return df["股價淨值比"] <= pbr_threshold


# 3. Dividend Yield is greater than or equal to <dividend_yield_threshold>
def dividend_yield_check_df(df, dividend_yield_threshold=1.5):
    return df["殖利率(%)"] >= dividend_yield_threshold


# 4. MoM Revenue Growth Rate is greater than or equal to <mom_threshold>
def mom_check_df(df, mom_threshold=10):
    return df["(月)營收月增率(%)"] >= mom_threshold


# 5. YoY Revenue Growth Rate is greater than or equal to <yoy_threshold>
def yoy_check_df(df, yoy_threshold=10):
    return df["(月)營收年增率(%)"] >= yoy_threshold


# 6. Acc-YoY Revenue Growth Rate is greater than or equal to <acc_yoy_threshold>
def acc_yoy_check_df(df, acc_yoy_threshold=10):
    return df["(月)累積營收年增率(%)"] >= acc_yoy_threshold
