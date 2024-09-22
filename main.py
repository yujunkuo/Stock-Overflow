from __future__ import unicode_literals

import datetime
import gc
import os
import threading

import pandas as pd
import psutil

from dotenv import load_dotenv
from flask import Flask, Response, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextSendMessage

from utils import helper
from config import logger
from strategies import fundamental_strategy, technical_strategy, chip_strategy

from crawlers import get_twse_data, get_tpex_data, get_other_data


#################### Global Variables ####################

# Year of the version
YEAR = "2024"

# Version number
VERSION = "v4.3"

# API Interface
app = Flask(__name__)

# Load environment variables
load_dotenv()

# Set up Line Bot information
line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))

# Set up API access token
api_access_token = os.getenv("API_ACCESS_TOKEN")


####################################################

# TODO: URL Routing path optimization: /, /test, /wakeup, /update
# TODO: Update README.md
# TODO: Server avaliability optimization
# TODO: Unit test
# TODO: Use target_date to replace now or today

# Line Bot Testing route
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# Default route
@app.route("/", methods=["GET"])
def home():
    return Response(status=200)


# Wakeup route - for server health check and memory clean
@app.route("/wakeup", methods=["GET"])
def wakeup():
    gc.collect()
    process = psutil.Process()
    memory_usage = process.memory_info().rss / 1024**2
    logger.info(f"目前記憶體使用量 {memory_usage:.2f} MB")
    return Response(status=200)


# Update route - for updating and broadcasting
@app.route("/update", methods=["GET"])
def update():
    # Check if API-Access-Token header is provided
    if "API-Access-Token" not in request.headers:
        return Response("Missing API-Access-Token", status=401)
    # Check if the provided token is correct
    elif request.headers["API-Access-Token"] != api_access_token:
        return Response("Invalid API-Access-Token", status=401)
    else:
        logger.info("開始進行推薦")
        # Assign update and broadcast
        update_and_broadcast_thread = threading.Thread(target=update_and_broadcast)
        update_and_broadcast_thread.start()
        return Response(status=200)
    
    
# Test route - for testing usage
@app.route("/test", methods=["GET"])
def test():
    # Check if API-Access-Token header is provided
    if "API-Access-Token" not in request.headers:
        return Response("Missing API-Access-Token", status=401)
    # Check if the provided token is correct
    elif request.headers["API-Access-Token"] != api_access_token:
        return Response("Invalid API-Access-Token", status=401)
    else:
        logger.info("開始進行測試")
        # Assign update and broadcast
        target_date_str = request.headers["Target-Date"]  # with format "YYYY-MM-DD"
        target_date = datetime.datetime.strptime(target_date_str, "%Y-%m-%d").date()
        update_and_broadcast_thread = threading.Thread(target=update_and_broadcast, args=(target_date, False))
        update_and_broadcast_thread.start()
        return Response(status=200)


####################################################

# Update and broadcast the recommendation list
def update_and_broadcast(target_date=None, need_broadcast=True):
    if not target_date:
        target_date = datetime.date.today()
    logger.info(f"資料日期 {str(target_date)}")
    if not helper.is_weekday(target_date):
        logger.info("假日不進行更新與推播")
    else:
        market_data_df = update_market_data(target_date)
        if market_data_df.shape[0] == 0:
            logger.info("休市不進行更新與推播")
        else:
            logger.info("開始更新推薦清單")
            watch_list_df = update_watch_list(market_data_df)
            logger.info("推薦清單更新完成")
            logger.info("開始進行好友推播")
            broadcast_watch_list(target_date, watch_list_df, need_broadcast)
            logger.info("好友推播執行完成")


# Update the market data
def update_market_data(target_date) -> pd.DataFrame:
    # Get the TWSE/TPEX data, and merge them
    twse_df = get_twse_data(target_date)
    tpex_df = get_tpex_data(target_date)
    market_data_df = pd.concat([twse_df, tpex_df])
    # If the market data is empty, return it directly
    if market_data_df.shape[0] == 0:
        return market_data_df
    # Get the other data
    other_df = get_other_data()
    # Merge the other data with the market data
    market_data_df = pd.merge(
        other_df,
        market_data_df,
        how="left",
        on=["代號", "名稱"],
    )
    # Drop the duplicated rows
    market_data_df = market_data_df[~market_data_df.index.duplicated(keep="first")]
    # Sort the index
    market_data_df = market_data_df.sort_index()
    # Print TSMC data to check the correctness
    logger.info("核對 [2330 台積電] 今日交易資訊")
    tsmc = market_data_df.loc["2330"]
    for column, value in tsmc.items():
        if type(value) == list and len(value) > 0:
            logger.info(f"{column}: {value[-1]} (history length={len(value)})")
        else:
            logger.info(f"{column}: {value}")
    return market_data_df


# Update the watch list
def update_watch_list(market_data_df):
    # Print the market data size
    logger.info(f"股市資料表大小 {market_data_df.shape}")

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
        technical_strategy.technical_indicator_constant_check_df(
            market_data_df,
            indicator="收盤",
            direction="more",
            threshold=20,
            days=1,
        ),
        # MA1 > MA5
        technical_strategy.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="收盤",
            indicator_2="mean5",
            direction="more",
            threshold=1,
            days=1,
        ),
        # MA5 > MA10
        technical_strategy.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="mean5",
            indicator_2="mean10",
            direction="more",
            threshold=1,
            days=1,
        ),
        # MA10 > MA20
        technical_strategy.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="mean10",
            indicator_2="mean20",
            direction="more",
            threshold=1,
            days=1,
        ),
        # MA20 > MA60
        technical_strategy.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="mean20",
            indicator_2="mean60",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 收盤價 > 1.01 * 開盤價 (今天收紅 K & 實體 K 棒漲幅大於 1%)
        technical_strategy.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="收盤",
            indicator_2="開盤",
            direction="more",
            threshold=1.01,
            days=1,
        ),
        # # K 棒底底高
        # (technical_strategy.technical_indicator_greater_or_less_two_day_check_df(market_data_df, indicator_1="開盤", indicator_2="開盤", direction="more", threshold=1, days=1) |\
        # technical_strategy.technical_indicator_greater_or_less_two_day_check_df(market_data_df, indicator_1="開盤", indicator_2="收盤", direction="more", threshold=1, days=1)),
        # # 今天開盤價 > 昨天收盤價
        # technical_strategy.technical_indicator_greater_or_less_two_day_check_df(market_data_df, indicator_1="開盤", indicator_2="收盤", direction="more", threshold=1, days=1),
        # 今天收盤 > 昨天最高
        technical_strategy.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="收盤",
            indicator_2="最高",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 今天 K9 > 昨天 K9
        technical_strategy.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="k9",
            indicator_2="k9",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 今天 D9 < 90
        technical_strategy.technical_indicator_constant_check_df(
            market_data_df, 
            indicator="d9", 
            direction="less", 
            threshold=90, 
            days=1
        ),
        # # 今天 OSC > 昨天 OSC
        # technical_strategy.technical_indicator_greater_or_less_two_day_check_df(market_data_df, indicator_1="osc", indicator_2="osc", direction="more", threshold=1, days=1),
        # |D9 - K9| < 22
        technical_strategy.technical_indicator_difference_one_day_check_df(
            market_data_df,
            indicator_1="k9",
            indicator_2="d9",
            difference_threshold=22,
            days=1,
        ),
        # # K9 between 49 ~ 87
        # technical_strategy.technical_indicator_constant_check_df(market_data_df, indicator="k9", direction="more", threshold=49, days=1),
        # technical_strategy.technical_indicator_constant_check_df(market_data_df, indicator="k9", direction="less", threshold=87, days=1),
        # J9 < 100
        technical_strategy.technical_indicator_constant_check_df(
            market_data_df, indicator="j9", direction="less", threshold=100, days=1
        ),
        # # (今天 k9-d9) >= (昨天 k9-d9)
        # technical_strategy.technical_indicator_difference_greater_two_day_check_df(market_data_df, indicator_1="k9", indicator_2="d9", days=1),
        # # MA5 趨勢向上
        # technical_strategy.technical_indicator_greater_or_less_two_day_check_df(market_data_df, indicator_1="mean5", indicator_2="mean5", direction="more", threshold=1, days=1),
        # 今天收盤 > 1.03 * 昨天收盤 (漲幅 3% 以上)
        technical_strategy.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="收盤",
            indicator_2="收盤",
            direction="more",
            threshold=1.03,
            days=1,
        ),
        # 不能連續兩天漲幅都超過 5%
        ~technical_strategy.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="收盤",
            indicator_2="收盤",
            direction="more",
            threshold=1.05,
            days=2,
        ),
        # # 今天收盤 < 1.1 * Mean5 or Mean10 or Mean20 (均線乖離不能過大)
        # technical_strategy.technical_indicator_greater_or_less_one_day_check_df(market_data_df, indicator_1="收盤", indicator_2="mean5", direction="less", threshold=1.1, days=1) |\
        # technical_strategy.technical_indicator_greater_or_less_one_day_check_df(market_data_df, indicator_1="收盤", indicator_2="mean10", direction="less", threshold=1.1, days=1) |\
        # technical_strategy.technical_indicator_greater_or_less_one_day_check_df(market_data_df, indicator_1="收盤", indicator_2="mean20", direction="less", threshold=1.1, days=1),
        # # 今天最高價不是四個月內最高 (只抓得到四個月的資料)
        # technical_strategy.today_price_is_not_max_check_df(market_data_df, price_type="最高", days=80),
        # 上影線長度不能超過昨天收盤價的 3% (0.03) / 0% (0.000001) 以上
        technical_strategy.technical_indicator_difference_two_day_check_df(
            market_data_df,
            indicator_1="最高",
            indicator_2="收盤",
            direction="less",
            threshold=0.03,
            indicator_3="收盤",
            days=1,
        ),
        # # OSC > 0 (出現強勁漲幅的機會較高)
        # technical_strategy.technical_indicator_constant_check_df(market_data_df, indicator="osc", direction="more", threshold=0, days=1),
        # # DIF > 0
        # technical_strategy.technical_indicator_constant_check_df(market_data_df, indicator="dif", direction="more", threshold=0, days=1),
        # # [(DIF / 收盤價) < 0.03] 或 [DIF 不是四個月內的最高]
        # technical_strategy.technical_indicator_greater_or_less_one_day_check_df(
        #     market_data_df,
        #     indicator_1="dif",
        #     indicator_2="收盤",
        #     direction="less",
        #     threshold=0.03,
        #     days=1,
        # )
        # | technical_strategy.today_price_is_not_max_check_df(
        #     market_data_df, price_type="dif", days=80
        # ),
    ]

    # Chip strategy filters
    chip_mask = [
        # 成交量 > 2000 張
        technical_strategy.volume_greater_check_df(
            market_data_df,
            shares_threshold=2000,
            days=1,
        ),
        # 今天成交量 > 昨天成交量
        technical_strategy.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="volume",
            indicator_2="volume",
            direction="more",
            threshold=1,
            days=1,
        ),
        # 今天成交量 > 5日均量
        technical_strategy.technical_indicator_greater_or_less_one_day_check_df(
            market_data_df,
            indicator_1="volume",
            indicator_2="mean_5_volume",
            direction="more",
            threshold=1,
            days=1,
        ),
        # # 5日均量 > 20日均量
        # technical_strategy.technical_indicator_greater_or_less_one_day_check_df(market_data_df, indicator_1="mean_5_volume", indicator_2="mean_20_volume", direction="more", threshold=1, days=1),
        # 5日均量 > 1000 張
        technical_strategy.technical_indicator_constant_check_df(
            market_data_df,
            indicator="mean_5_volume",
            direction="more",
            threshold=1000,
            days=1,
        ),
        # 20日均量 > 1000 張
        technical_strategy.technical_indicator_constant_check_df(
            market_data_df,
            indicator="mean_20_volume",
            direction="more",
            threshold=1000,
            days=1,
        ),
        # 「今天的5日均量」要大於「昨天的5日均量」
        technical_strategy.technical_indicator_greater_or_less_two_day_check_df(
            market_data_df,
            indicator_1="mean_5_volume",
            indicator_2="mean_5_volume",
            direction="more",
            threshold=1,
            days=1,
        ),
        # # 單一法人至少買超成交量的 10%
        # chip_strategy.single_institutional_buy_check_df(market_data_df, single_volume_threshold=10),
        # # 法人合計至少買超成交量的 1%
        # chip_strategy.total_institutional_buy_check_df(market_data_df, total_volume_threshold=1),
        # 外資買超 >= 0 股 (200 張 -> threshold=2e5)
        chip_strategy.foreign_buy_positive_check_df(market_data_df, threshold=-1),
        # # 投信買超 > 50,000 股
        # chip_strategy.investment_buy_positive_check_df(market_data_df, threshold=5e4),
        # # 自定義法人買超篩選
        # chip_strategy.buy_positive_check_df(market_data_df),
        # # 法人合計買超 > 0 股
        # chip_strategy.total_institutional_buy_positive_check_df(market_data_df, threshold=0),
    ]

    # Combine all the filters
    watch_list_df = helper.df_mask_helper(
        market_data_df, fundamental_mask + technical_mask + chip_mask
    )
    watch_list_df = watch_list_df.sort_values(by=["產業別"], ascending=False)
    watch_list_df = watch_list_df[
        watch_list_df.index.to_series().apply(technical_strategy.is_skyrocket)
    ]
    return watch_list_df


# Broadcast the watch list
def broadcast_watch_list(target_date, watch_list_df, need_broadcast=True):
    # Construct the final recommendation text message
    if len(watch_list_df) == 0:
        final_recommendation_text = f"🔎 今日無 [推薦觀察] 股票\n"
        logger.info("今日無 [推薦觀察] 股票")
    else:
        final_recommendation_text = (
            f"🔎 [推薦觀察]  股票有 {len(watch_list_df)} 檔\n" + "\n###########\n\n"
        )
        logger.info(f"[推薦觀察] 股票有 {len(watch_list_df)} 檔")
        for i, v in watch_list_df.iterrows():
            final_recommendation_text += f"{i} {v['名稱']}  {v['產業別']}\n"
            logger.info(f"{i} {v['名稱']}  {v['產業別']}")
    # Append the separator
    final_recommendation_text += "\n###########\n\n"
    # Append the source information
    final_recommendation_text += f"資料來源: 台股 {str(target_date)}"
    # Append the version information
    final_recommendation_text += f"\nJohnKuo © {YEAR} ({VERSION})"
    # Broadcast the final recommendation text message if needed
    if need_broadcast:
        line_bot_api.broadcast(TextSendMessage(text=final_recommendation_text))


####################################################

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
