from __future__ import unicode_literals

import requests
from bs4 import BeautifulSoup
import datetime
import time
import random
import pandas as pd
import numpy as np
from io import StringIO
import json
from functools import reduce

import twse
import tpex
import other

import fundamental_strategy
import technical_strategy
import chip_strategy

import helper

from flask import Flask, Response, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import os
from dotenv import load_dotenv

import threading

#################### 全域變數設定 ####################

# API Interface
app = Flask(__name__)


# 載入環境變數
load_dotenv()


# 設定 LINE Bot 基本資料
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))


# 初始化股票當日交易紀錄資料表
final_df = pd.DataFrame(columns=['名稱', '產業別', '股票類型', '收盤', '漲跌', '開盤', '最高', '最低', '成交股數', '本益比',
       '股利年度', '殖利率(%)', '股價淨值比', '融資買進', '融資賣出', '融資前日餘額', '融資今日餘額', '融券買進',
       '融券賣出', '融券前日餘額', '融券今日餘額', '資券互抵', '融資變化量', '融券變化量', '券資比(%)',
       '外資買賣超股數', '投信買賣超股數', '自營商買賣超股數', '三大法人買賣超股數', '外資持股比率(%)',
       '(月)營收月增率(%)', '(月)營收年增率(%)', '(月)累積營收年增率(%)', 'k9', 'd9', 'dif',
       'macd', 'osc', 'mean5', 'mean10', 'mean20', 'mean60', 'volume',
       'daily_k'])


# 最新資料表的日期
final_date = None

####################################################


# 接收 LINE 的資訊（固定寫法）
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


# LINE Bot 自動回覆
@handler.add(MessageEvent, message=TextMessage)
def echo(event):
    
    if event.source.user_id != "Udeadbeefdeadbeefdeadbeefdeadbeef":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="買股票賺大錢！")
        )


# 喚醒 Dyno
@app.route("/wakeup", methods=['GET'])
def wakeup():
    try:
        print("Wakeup Sucess!")
        # 透過 Thread 指派更新
        update_thread = threading.Thread(target=update)
        update_thread.start()
        # 透過 Thread 指派推播
        # broadcast_thread = threading.Thread(target=broadcast)
        # broadcast_thread.start()
        return Response(status=200)
    except:
        print("Wakeup Error!")
        return Response(status=500)


# 更新今日推薦股票(1630-1730)
def update():
    if not helper.check_time_between(datetime.time(16,30), datetime.time(17,30)):
        print("Not yet Update!")
        return
    try:
        # 欲查詢日期
        search_date = datetime.date.today()
        # 取得資料表
        global final_df
        global final_date
        final_df = get_all_final(search_date)
        final_date = search_date
        print("Update Sucess!")
        print(f"Final date is {str(final_date)}")
        print(final_df.head())
        print("Start Broadcast!")
        broadcast()
        return
    except:
        print("Update Error!")
        return


# 進行全好友推播(1730-1830)
def broadcast():
    # if not helper.check_time_between(datetime.time(17,30), datetime.time(18,30)):
    #     print("Not yet broadcast!")
    #     return
    try:
        print(f"Final date is {str(final_date)}")
        print(final_df.head())
        # 股票基本面篩選條件
        fundimental_mask = [
            # # 月營收年增率 > 5%
            # final_df["(月)營收年增率(%)"] > 5,
            # # 累積營收年增率 > 5%
            # final_df["(月)累積營收年增率(%)"] > 5,
        ]

        # 股票技術面篩選條件
        technical_mask = [
            # MA1 > MA5
            technical_strategy.technical_indicator_greater_one_day_check_df(final_df, indicator_1="收盤", indicator_2="mean5", days=1),
            # # MA1 > MA20
            # technical_strategy.technical_indicator_greater_one_day_check_df(final_df, indicator_1="收盤", indicator_2="mean20", days=1),
            # 今天開盤價 > 昨天收盤價 (主力表態拉抬)
            technical_strategy.technical_indicator_greater_or_less_two_day_check_df(df, indicator_1="開盤", indicator_2="收盤", direction="more", threshold=1, days=1),
            # 今天 K9 > 昨天 K9
            technical_strategy.technical_indicator_greater_or_less_two_day_check_df(final_df, indicator_1="k9", indicator_2="k9", direction="more", threshold=1, days=1),
            # 今天 OSC > 昨天 OSC
            technical_strategy.technical_indicator_greater_or_less_two_day_check_df(final_df, indicator_1="osc", indicator_2="osc", direction="more", threshold=1, days=1),
            # 今天最低 > 昨天最低
            technical_strategy.technical_indicator_greater_or_less_two_day_check_df(final_df, indicator_1="最低", indicator_2="最低", direction="more", threshold=1, days=1),
            # |今天D9 - 今天K9| < 20
            technical_strategy.technical_indicator_difference_one_day_check_df(final_df, indicator_1="k9", indicator_2="d9", difference_threshold=20, days=1),
            # 今天的 K9 要介於 20~80 之間
            technical_strategy.technical_indicator_constant_check_df(final_df, indicator="k9", direction="more", threshold=20, days=1),
            technical_strategy.technical_indicator_constant_check_df(final_df, indicator="k9", direction="less", threshold=80, days=1),
            # (今天 k9-d9) 大於等於 (昨天 k9-d9)
            technical_strategy.technical_indicator_difference_greater_two_day_check_df(final_df, indicator_1="k9", indicator_2="d9", days=1),
            # 月線趨勢向上 (MA20 趨勢向上)
            technical_strategy.technical_indicator_greater_or_less_two_day_check_df(df, indicator_1="mean20", indicator_2="mean20", direction="more", threshold=1, days=1),
            # # 今天收盤 < 1.08 * 昨天收盤 (只抓今日漲幅 8% 以內的股票) (要留嗎？)
            # technical_strategy.technical_indicator_greater_or_less_two_day_check_df(final_df, indicator_1="收盤", indicator_2="收盤", direction="less", threshold=1.08, days=1),
            # # 今天最高價不是一年內的最高 (不追高)
            # technical_strategy.today_price_is_not_max_check_df(final_df, price_type="最高", days=240),
            # # OSC 必須要大於0 (經驗顯示 OSC 大於 0 後勢出現強勁漲幅的機會較高) (要留嗎？)
            # technical_strategy.technical_indicator_constant_check_df(final_df, indicator="osc", direction="more", threshold=0, days=1),
        ]

        # 股票籌碼面篩選條件
        chip_mask = [
            # # 今天成交量 > 2000 張
            # technical_strategy.volume_greater_check_df(final_df, shares_threshold=2000, days=1),
            # # 今天成交量不能是 2 天內最低量 (今天成交量要比昨天高)
            # technical_strategy.today_volume_is_not_min_check_df(final_df, days=2),
            # 今天成交量要大於 2 倍的昨天成交量
            technical_strategy.technical_indicator_greater_or_less_two_day_check_df(df, indicator_1="volume", indicator_2="volume", direction="more", threshold=2, days=1),
            # 今量 > 5日均量
            technical_strategy.technical_indicator_greater_one_day_check_df(final_df, indicator_1="volume", indicator_2="mean_5_volume", days=1),
            # # 5日均量 > 20日均量
            # technical_strategy.technical_indicator_greater_one_day_check_df(final_df, indicator_1="mean_5_volume", indicator_2="mean_20_volume", days=1),
            # 5日均量 > 1000
            technical_strategy.technical_indicator_constant_check_df(final_df, indicator="mean_5_volume", direction="more", threshold=1000, days=1),
            # 20日均量 > 1000
            technical_strategy.technical_indicator_constant_check_df(final_df, indicator="mean_20_volume", direction="more", threshold=1000, days=1),
            # 單一法人至少買超成交量的 10%
            chip_strategy.single_institutional_buy_check_df(final_df, single_volume_threshold=10),
            # # 三大法人合計買超至少超過成交量的 10%
            # chip_strategy.total_institutional_buy_check_df(final_df, total_volume_threshold=10),
        ]

        # 取得推薦清單
        final_filter = helper.df_mask_helper(final_df, fundimental_mask + technical_mask + chip_mask)
        final_filter = final_filter.sort_values(by=['成交股數'], ascending=False)
        # 轉換為字串回傳
        if not final_filter.shape[0]:
            final_recommendation_text = f"今日無推薦之股票 {str(final_date)}"
            print("今日無推薦之股票")
        else:
            final_recommendation_text = f"滿足條件的股票共有: {final_filter.shape[0]} 檔 (依照成交量由大到小排序)\n\n"
            print(f"滿足條件的股票共有: {final_filter.shape[0]} 檔 (依照成交量由大到小排序)\n")
            for i, v in final_filter.iterrows():
                final_recommendation_text += f"{i} {v['名稱']}  {v['產業別']}\n"
            final_recommendation_text += f"\n此清單係依據台股於 {str(final_date)} 成交資料所做之推薦"
        # 透過 LINE API 進行推播
        line_bot_api.broadcast(TextSendMessage(text=final_recommendation_text))
        print("Broadcast Sucess!")
        return
    except:
        print("Broadcast Error!")
        return


# 取得今日股市資料表
def get_all_final(date) -> pd.DataFrame:
    # 取得上市資料表
    twse_df = twse.get_twse_final(date)
    # 取得上櫃資料表
    tpex_df = tpex.get_tpex_final(date)
    # 兩張表接起來
    df = pd.concat([twse_df, tpex_df])
    # 取得產業別
    industry_category_df = other.get_industry_category()
    # 合併資料表
    df = pd.merge(industry_category_df, df, how="left", on=["代號", "名稱", "股票類型"])
    # 補上 MoM 與 YoY
    mom_yoy_df = other.get_mom_yoy()
    df = pd.merge(df, mom_yoy_df, how="left", on=["代號", "名稱"])
    # 先移除重複的股票
    df = df[~df.index.duplicated(keep='first')]
    # 補上技術指標
    df = other.get_technical_indicators(df)
    # 再次移除重複的股票
    df = df[~df.index.duplicated(keep='first')]
    # 重新按股票代碼排序
    df = df.sort_index()
    return df
    


if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

