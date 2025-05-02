def get_last_n_days_data(row, indicator, days):
    if indicator in ["開盤", "收盤", "最高", "最低"]:
        return [day[1][indicator] for day in row["daily_k"][-1 : (-1-days) : -1]]
    else:
        return [day[1] for day in row[indicator][-1 : (-1-days) : -1]]