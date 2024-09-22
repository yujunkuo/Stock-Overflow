## Chip Strategies

##### Institutional Investors' Movements #####


# 1. Single Institutional Investor's Buy Volume is greater than or equal to <single_volume_threshold>% of the total trading volume
def single_institutional_buy_check_df(df, single_volume_threshold=10):
    return df.apply(
        _single_institutional_buy_check_row,
        single_volume_threshold=single_volume_threshold,
        axis=1,
    )


def _single_institutional_buy_check_row(row, single_volume_threshold) -> bool:
    try:
        single_volume_threshold_actual = row["成交量"] * (
            single_volume_threshold / 100
        )
        single_institutional_volume_list = [
            row["外資買賣超"],
            row["投信買賣超"],
            row["自營商買賣超"],
        ]
        return any(
            volume >= single_volume_threshold_actual
            for volume in single_institutional_volume_list
        )
    except:
        return False


# 2. Total Institutional Investors' Buy Volume is greater than or equal to <total_volume_threshold>% of the total trading volume
def total_institutional_buy_check_df(df, total_volume_threshold=10):
    return df.apply(
        _total_institutional_buy_check_row,
        total_volume_threshold=total_volume_threshold,
        axis=1,
    )


def _total_institutional_buy_check_row(row, total_volume_threshold) -> bool:
    try:
        total_volume_threshold_actual = row["成交量"] * (total_volume_threshold / 100)
        return row["三大法人買賣超"] >= total_volume_threshold_actual
    except:
        return False


# 3. Foreign Investors' Buy Volume is greater than or equal to <total_volume_threshold>% of the total trading volume
def foreign_buy_check_df(df, total_volume_threshold=10):
    return df.apply(
        _foreign_buy_check_row, total_volume_threshold=total_volume_threshold, axis=1
    )


def _foreign_buy_check_row(row, total_volume_threshold) -> bool:
    try:
        total_volume_threshold_actual = row["成交量"] * (total_volume_threshold / 100)
        return row["外資買賣超"] >= total_volume_threshold_actual
    except:
        return False


# 4. Total Institutional Investors' Buy Volume is greater than or equal to <threshold>
def total_institutional_buy_positive_check_df(df, threshold=1e2):
    return df["三大法人買賣超"] >= threshold


# 5. Foreign Investors' Buy Volume is greater than or equal to <threshold>
def foreign_buy_positive_check_df(df, threshold=1e2):
    return df["外資買賣超"] >= threshold


# 6. Investment Bank's Buy Volume is greater than or equal to <threshold>
def investment_buy_positive_check_df(df, threshold=1e2):
    return df["投信買賣超"] >= threshold


# 7. Dealer's Buy Volume is greater than or equal to <threshold>
def dealer_buy_positive_check_df(df, threshold=1e2):
    return df["自營商買賣超"] >= threshold


# 8. Customized Buy Volume strategy
def buy_positive_check_df(df):
    return (df["外資買賣超"] >= 2e2) | (df["投信買賣超"] + df["自營商買賣超"] >= 2e2)


##### Margin Trading's Movements #####


# 9. Margin Trading Increase Volume is greater than or equal to <margin_trading_threshold>% of the total trading volume
def margin_trading_check_df(df, margin_trading_threshold=1):
    return df["融資變化量"] >= (df["成交量"] * (margin_trading_threshold / 100))


# 10. Short Selling Increase Volume is greater than or equal to <short_selling_threshold>% of the total trading volume
def short_selling_check_df(df, short_selling_threshold=1):
    return df["融券變化量"] >= (df["成交量"] * (short_selling_threshold / 100))


# 11. Short Margin Ratio is greater than or equal to <short_margin_ratio_threshold>
def short_margin_ratio_check_df(df, short_margin_ratio_threshold=5):
    return df["券資比(%)"] >= short_margin_ratio_threshold
