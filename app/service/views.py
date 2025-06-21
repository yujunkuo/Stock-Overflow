# Standard library imports
import datetime
from functools import reduce, partial
from typing import List, Any, Optional

# Third-party imports
import pandas as pd

# Local imports
from app.core import logger
from app.crawler import get_economic_events, get_other_data, get_tpex_data, get_twse_data
from app.rule.core import technical
from app.service.strategy import get_strategy_1, get_strategy_3
from app.service.notification import broadcast_watch_list


def _df_mask_helper(df: pd.DataFrame, mask_list: List[Any]) -> pd.DataFrame:
    """Filter dataframe with multiple conditions in mask_list"""
    return df[reduce(lambda x, y: (x & y), mask_list)]


def _is_weekday(check_date: Optional[datetime.date] = None) -> bool:
    """Check if the input date is a weekday"""
    check_date = check_date if check_date else datetime.date.today()
    # Weekday count: Monday=0, Tuesday=1, ..., Sunday=6
    weekday_count = check_date.weekday()
    return True if weekday_count < 5 else False


def update_and_broadcast(app, target_date=None, need_broadcast=False):
    """Update and broadcast the recommendation list"""
    with app.app_context():
        if not target_date:
            target_date = datetime.date.today()
        logger.info(f"資料日期 {str(target_date)}")
        if not _is_weekday(target_date):
            logger.info("假日不進行更新與推播")
        else:
            market_data_df = _update_market_data(target_date)
            if market_data_df.shape[0] == 0:
                logger.info("休市不進行更新與推播")
            else:
                logger.info("開始更新推薦清單")
                watch_list_df_1 = _update_watch_list(market_data_df, get_strategy_1, other_funcs=[technical.is_skyrocket])
                # watch_list_df_2 = _update_watch_list(market_data_df, get_strategy_2, other_funcs=[technical.is_sar_above_close, partial(technical.is_skyrocket, consecutive_red_no_upper_shadow_days=0)])
                watch_list_df_3 = _update_watch_list(market_data_df, get_strategy_3, other_funcs=[partial(technical.is_skyrocket, consecutive_red_no_upper_shadow_days=0)])
                # combined_watch_list_df = pd.concat([watch_list_df_1, watch_list_df_2]).drop_duplicates(subset=["代號"]).reset_index(drop=True)
                watch_list_dfs = [watch_list_df_1, watch_list_df_3]
                logger.info("推薦清單更新完成")
                logger.info("開始讀取經濟事件")
                start_date = (target_date + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                end_date = (target_date + datetime.timedelta(days=3)).strftime("%Y-%m-%d")
                economic_events = get_economic_events(start_date, end_date)
                logger.info("經濟事件讀取完成")
                logger.info("開始進行好友推播")
                broadcast_watch_list(target_date, watch_list_dfs, economic_events, need_broadcast)
                logger.info("好友推播執行完成")


# Update the market data
def _update_market_data(target_date) -> pd.DataFrame:
    # Get the TWSE/TPEX data, and merge them
    twse_df = get_twse_data(target_date)
    tpex_df = get_tpex_data(target_date)
    market_data_df = pd.concat([twse_df, tpex_df])
    # If the market data is empty, return it directly
    if market_data_df.shape[0] == 0:
        return market_data_df
    # Get the other data
    other_df = get_other_data(target_date)
    # Merge the other data with the market data
    market_data_df = pd.merge(
        other_df,
        market_data_df,
        how="left",
        on=["代號", "名稱", "股票類型"],
    )
    # Drop the duplicated rows
    market_data_df = market_data_df[~market_data_df.index.duplicated(keep="first")]
    # Sort the index
    market_data_df = market_data_df.sort_index()
    # Print TSMC data to check the correctness
    logger.info(f"核對 [2330 台積電] {target_date} 交易資訊")
    tsmc = market_data_df.loc["2330"]
    for column, value in tsmc.items():
        if type(value) == list and len(value) > 0:
            logger.info(f"{column}: {value[-1]} (history length={len(value)})")
        else:
            logger.info(f"{column}: {value}")
    return market_data_df


# Update the watch list
def _update_watch_list(market_data_df, strategy_func, other_funcs=None) -> pd.DataFrame:
    # Print the market data size
    logger.info(f"股市資料表大小 {market_data_df.shape}")
    # Get the strategy
    fundamental_mask, technical_mask, chip_mask = strategy_func(market_data_df)
    # Combine all the filters
    watch_list_df = _df_mask_helper(market_data_df, fundamental_mask + technical_mask + chip_mask)
    watch_list_df = watch_list_df.sort_values(by=["產業別"], ascending=False)
    if other_funcs:
        for func in other_funcs:
            watch_list_df = watch_list_df[watch_list_df.index.to_series().apply(func)]
    return watch_list_df
