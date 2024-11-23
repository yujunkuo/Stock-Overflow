import datetime
import pandas as pd

from config import logger
from flask import current_app
from linebot.models import TextSendMessage
from .strategies import technical, chip
from .utils import is_weekday, df_mask_helper
from .crawlers import get_twse_data, get_tpex_data, get_other_data


# Update and broadcast the recommendation list
def update_and_broadcast(app, target_date=None, need_broadcast=False):
    with app.app_context():
        if not target_date:
            target_date = datetime.date.today()
        logger.info(f"資料日期 {str(target_date)}")
        if not is_weekday(target_date):
            logger.info("假日不進行更新與推播")
        else:
            market_data_df = _update_market_data(target_date)
            if market_data_df.shape[0] == 0:
                logger.info("休市不進行更新與推播")
            else:
                logger.info("開始更新推薦清單")
                watch_list_df_1 = _update_watch_list(market_data_df, _get_strategy_1)
                watch_list_df_2 = _update_watch_list(market_data_df, _get_strategy_2, is_skyrocket=False)
                watch_list_dfs = [watch_list_df_1, watch_list_df_2]
                logger.info("推薦清單更新完成")
                logger.info("開始進行好友推播")
                _broadcast_watch_list(target_date, watch_list_dfs, need_broadcast)
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
def _update_watch_list(market_data_df, strategy_func, is_skyrocket=True) -> pd.DataFrame:
    # Print the market data size
    logger.info(f"股市資料表大小 {market_data_df.shape}")
    # Get the strategy
    fundamental_mask, technical_mask, chip_mask = strategy_func(market_data_df)
    # Combine all the filters
    watch_list_df = df_mask_helper(market_data_df, fundamental_mask + technical_mask + chip_mask)
    watch_list_df = watch_list_df.sort_values(by=["產業別"], ascending=False)
    if is_skyrocket:
        watch_list_df = watch_list_df[watch_list_df.index.to_series().apply(technical.is_skyrocket)]
    return watch_list_df


# Get the strategy 1
def _get_strategy_1(market_data_df) -> tuple:
    # Fundamental strategy filters
    fundamental_mask = [
        # # 月營收年增率 > 20%
        # market_data_df["(月)營收年增率(%)"] > 20,
        # # 累積營收年增率 > 10%
        # market_data_df["(月)累積營收年增率(%)"] > 10,
    ]

    # Technical strategy filters
    technical_mask = [
        # 收盤價 > 20
        technical.technical_indicator_constant_check_df(
            market_data_df,
            indicator="收盤",
            direction="more",
            threshold=20,
            days=1,
        ),
        # MA1 > MA5
        technical.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="收盤",
            indicator_2="mean5",
            direction="more",
            threshold=1,
            days=1,
        ),
        # MA5 > MA10
        technical.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="mean5",
            indicator_2="mean10",
            direction="more",
            threshold=1,
            days=1,
        ),
        # MA10 > MA20
        technical.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="mean10",
            indicator_2="mean20",
            direction="more",
            threshold=1,
            days=1,
        ),
        # MA20 > MA60
        technical.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="mean20",
            indicator_2="mean60",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 收盤價 > 1.01 * 開盤價 (今天收紅 K & 實體 K 棒漲幅大於 1%)
        technical.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="收盤",
            indicator_2="開盤",
            direction="more",
            threshold=1.01,
            days=1,
        ),
        # # K 棒底底高
        # (technical.technical_indicator_greater_or_less_two_day_check_df(market_data_df, indicator_1="開盤", indicator_2="開盤", direction="more", threshold=1, days=1) |\
        # technical.technical_indicator_greater_or_less_two_day_check_df(market_data_df, indicator_1="開盤", indicator_2="收盤", direction="more", threshold=1, days=1)),
        # # 今天開盤價 > 昨天收盤價
        # technical.technical_indicator_greater_or_less_two_day_check_df(market_data_df, indicator_1="開盤", indicator_2="收盤", direction="more", threshold=1, days=1),
        # 今天收盤 > 昨天最高
        technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="收盤",
            indicator_2="最高",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 今天 K9 > 昨天 K9
        technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="k9",
            indicator_2="k9",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 今天 D9 < 90
        technical.technical_indicator_constant_check_df(
            market_data_df, 
            indicator="d9", 
            direction="less", 
            threshold=90, 
            days=1,
        ),
        # # 今天 OSC > 昨天 OSC
        # technical.technical_indicator_greater_or_less_two_day_check_df(market_data_df, indicator_1="osc", indicator_2="osc", direction="more", threshold=1, days=1),
        # |D9 - K9| < 22
        technical.technical_indicator_difference_one_day_check_df(
            market_data_df,
            indicator_1="k9",
            indicator_2="d9",
            difference_threshold=22,
            days=1,
        ),
        # # K9 between 49 ~ 87
        # technical.technical_indicator_constant_check_df(market_data_df, indicator="k9", direction="more", threshold=49, days=1),
        # technical.technical_indicator_constant_check_df(market_data_df, indicator="k9", direction="less", threshold=87, days=1),
        # J9 < 100
        technical.technical_indicator_constant_check_df(
            market_data_df, indicator="j9", direction="less", threshold=100, days=1
        ),
        # # (今天 k9-d9) >= (昨天 k9-d9)
        # technical.technical_indicator_difference_greater_two_day_check_df(market_data_df, indicator_1="k9", indicator_2="d9", days=1),
        # # MA5 趨勢向上
        # technical.technical_indicator_greater_or_less_two_day_check_df(market_data_df, indicator_1="mean5", indicator_2="mean5", direction="more", threshold=1, days=1),
        # 今天收盤 > 1.03 * 昨天收盤 (漲幅 3% 以上)
        technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="收盤",
            indicator_2="收盤",
            direction="more",
            threshold=1.03,
            days=1,
        ),
        # 不能連續兩天漲幅都超過 5%
        ~technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="收盤",
            indicator_2="收盤",
            direction="more",
            threshold=1.05,
            days=2,
        ),
        # # 今天收盤 < 1.1 * Mean5 or Mean10 or Mean20 (均線乖離不能過大)
        # technical.technical_indicator_greater_or_less_one_day_check_df(market_data_df, indicator_1="收盤", indicator_2="mean5", direction="less", threshold=1.1, days=1) |\
        # technical.technical_indicator_greater_or_less_one_day_check_df(market_data_df, indicator_1="收盤", indicator_2="mean10", direction="less", threshold=1.1, days=1) |\
        # technical.technical_indicator_greater_or_less_one_day_check_df(market_data_df, indicator_1="收盤", indicator_2="mean20", direction="less", threshold=1.1, days=1),
        # # 今天最高價不是四個月內最高 (只抓得到四個月的資料)
        # technical.today_price_is_not_max_check_df(market_data_df, price_type="最高", days=80),
        # 上影線長度不能超過昨天收盤價的 3% (0.03) / 0% (0.000001) 以上
        technical.technical_indicator_difference_two_day_check_df(
            market_data_df,
            indicator_1="最高",
            indicator_2="收盤",
            direction="less",
            threshold=0.03,
            indicator_3="收盤",
            days=1,
        ),
        # # OSC > 0 (出現強勁漲幅的機會較高)
        # technical.technical_indicator_constant_check_df(market_data_df, indicator="osc", direction="more", threshold=0, days=1),
        # # DIF > 0
        # technical.technical_indicator_constant_check_df(market_data_df, indicator="dif", direction="more", threshold=0, days=1),
        # # [(DIF / 收盤價) < 0.03] 或 [DIF 不是四個月內的最高]
        # technical.technical_indicator_greater_or_less_one_day_check_df(
        #     market_data_df,
        #     indicator_1="dif",
        #     indicator_2="收盤",
        #     direction="less",
        #     threshold=0.03,
        #     days=1,
        # )
        # | technical.today_price_is_not_max_check_df(
        #     market_data_df, price_type="dif", days=80
        # ),
    ]

    # Chip strategy filters
    chip_mask = [
        # 成交量 > 2000 張
        technical.volume_greater_check_df(
            market_data_df,
            shares_threshold=2000,
            days=1,
        ),
        # 今天成交量 > 昨天成交量
        technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="volume",
            indicator_2="volume",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 今天成交量 > 5日均量
        technical.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="volume",
            indicator_2="mean_5_volume",
            direction="more",
            threshold=1,
            days=1,
        ),
        # # 5日均量 > 20日均量
        # technical.technical_indicator_greater_or_less_one_day_check_df(market_data_df, indicator_1="mean_5_volume", indicator_2="mean_20_volume", direction="more", threshold=1, days=1),
        # 5日均量 > 1000 張
        technical.technical_indicator_constant_check_df(
            market_data_df,
            indicator="mean_5_volume",
            direction="more",
            threshold=1000,
            days=1,
        ),
        # 20日均量 > 1000 張
        technical.technical_indicator_constant_check_df(
            market_data_df,
            indicator="mean_20_volume",
            direction="more",
            threshold=1000,
            days=1,
        ),
        # 「今天的5日均量」要大於「昨天的5日均量」
        technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="mean_5_volume",
            indicator_2="mean_5_volume",
            direction="more",
            threshold=1,
            days=1,
        ),
        # # 單一法人至少買超成交量的 10%
        # chip.single_institutional_buy_check_df(market_data_df, single_volume_threshold=10),
        # # 法人合計至少買超成交量的 1%
        # chip.total_institutional_buy_check_df(market_data_df, total_volume_threshold=1),
        # 外資買超 >= 0 張
        chip.foreign_buy_positive_check_df(market_data_df, threshold=0),
        # # 投信買超 >= 50 張
        # chip.investment_buy_positive_check_df(market_data_df, threshold=50),
        # # 自定義法人買超篩選
        # chip.buy_positive_check_df(market_data_df),
        # # 法人合計買超 >= 0 張
        # chip.total_institutional_buy_positive_check_df(market_data_df, threshold=0),
    ]
    return fundamental_mask, technical_mask, chip_mask


# Get the strategy 2
def _get_strategy_2(market_data_df) -> tuple:
    fundamental_mask = []
    technical_mask = [
        # 收盤價 > 20
        technical.technical_indicator_constant_check_df(
            market_data_df,
            indicator="收盤",
            direction="more",
            threshold=20,
            days=1,
        ),
        # MA1 > MA5
        technical.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="收盤",
            indicator_2="mean5",
            direction="more",
            threshold=1,
            days=1,
        ),
        # MA1 > MA20
        technical.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="收盤",
            indicator_2="mean20",
            direction="more",
            threshold=1,
            days=1,
        ),
        # K9 > D9
        technical.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="k9",
            indicator_2="d9",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 今天 J9 > 昨天 J9
        technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="j9",
            indicator_2="j9",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 今天 OSC > 昨天 OSC
        technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="osc",
            indicator_2="osc",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 今天 J9 < 100
        technical.technical_indicator_constant_check_df(
            market_data_df, indicator="j9", direction="less", threshold=100, days=1
        ),
    ]
    chip_mask = [
        # 成交量 > 1500 張
        technical.volume_greater_check_df(
            market_data_df,
            shares_threshold=1500,
            days=1,
        ),
        # 今天成交量 > 昨天成交量
        technical.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="volume",
            indicator_2="volume",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 今天成交量 > 5日均量
        technical.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="volume",
            indicator_2="mean_5_volume",
            direction="more",
            threshold=1,
            days=1,
        ),
    ]
    return fundamental_mask, technical_mask, chip_mask


# Broadcast the watch list
def _broadcast_watch_list(target_date, watch_list_dfs, need_broadcast):
    # Construct the final recommendation text message
    final_recommendation_text = ""
    for i, watch_list_df in enumerate(watch_list_dfs):
        if len(watch_list_df) == 0:
            final_recommendation_text += f"🔎 [策略{i+1}]  無推薦股票\n"
            logger.info(f"[策略{i+1}] 無推薦股票")
        else:
            final_recommendation_text += f"🔎 [策略{i+1}]  股票有 {len(watch_list_df)} 檔\n" + "\n###########\n\n"
            logger.info(f"[策略{i+1}] 股票有 {len(watch_list_df)} 檔")
            for stock_id, v in watch_list_df.iterrows():
                final_recommendation_text += f"{stock_id} {v['名稱']}  {v['產業別']}\n"
                logger.info(f"{stock_id} {v['名稱']}  {v['產業別']}")
        # Append the separator
        final_recommendation_text += "\n###########\n\n"
    # Append the source information
    final_recommendation_text += f"資料來源: 台股 {str(target_date)}"
    # Append the version information
    final_recommendation_text += f"\nJohnKuo © {current_app.config['YEAR']} ({current_app.config['VERSION']})"
    # Broadcast the final recommendation text message if needed
    if need_broadcast:
        line_bot_api = current_app.config["LINE_BOT_API"]
        line_bot_api.broadcast(TextSendMessage(text=final_recommendation_text))
