import datetime

# Make the technical indicators pretty
def get_technical_indicator_pretty_list(technical_indicator_list: list) -> list:
    new_technical_indicator_list = list()
    for i, each in enumerate(technical_indicator_list):
        single_time = _calculate_date_from_milliseconds(each[0], len(technical_indicator_list)-i-1)
        single_indicator_value = each[1]
        new_technical_indicator_list.append([single_time, single_indicator_value])
    return new_technical_indicator_list


# Make the daily k pretty
def get_daily_k_pretty_list(daily_k_list: list) -> list:
    new_daily_k_list = list()
    for i, each in enumerate(daily_k_list):
        single_time = _calculate_date_from_milliseconds(each[0], len(daily_k_list)-i-1)
        single_k_dict = {
            "開盤": each[1],
            "最高": each[2],
            "最低": each[3],
            "收盤": each[4],
        }
        new_daily_k_list.append([single_time, single_k_dict])
    return new_daily_k_list


# Convert milliseconds to date
def _calculate_date_from_milliseconds(input_milliseconds: int, time_delta: int) -> datetime.date:
    current_year = (datetime.datetime.now() - datetime.timedelta(days=time_delta)).year
    current_year_beginning = datetime.date(current_year, 1, 1)
    time_delta_days = datetime.timedelta(
        days=datetime.timedelta(seconds=input_milliseconds / 1000 - 13 * 86400).days
        % 365
    )
    final_date = current_year_beginning + time_delta_days
    return final_date