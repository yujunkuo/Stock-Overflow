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

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

app = Flask(__name__)

# LINE 聊天機器人的基本資料
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))


# 接收 LINE 的資訊
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


# 學你說話
@handler.add(MessageEvent, message=TextMessage)
def echo(event):
    
    if event.source.user_id != "Udeadbeefdeadbeefdeadbeefdeadbeef":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=event.message.text)
        )



if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


# # 全域設定

# # 顯示全部的行列
# pd.set_option('display.max_columns', None)
# pd.set_option("max_rows", 5)


# def get_all_final(date) -> pd.DataFrame:
#     # 取得上市資料表
#     twse_df = twse.get_twse_final(date)
#     # 取得上櫃資料表
#     tpex_df = tpex.get_tpex_final(date)
#     # 兩張表接起來
#     df = pd.concat([twse_df, tpex_df])
#     # 取得產業別
#     industry_category_df = other.get_industry_category()
#     # 合併資料表
#     df = pd.merge(industry_category_df, df, how="left", on=["代號", "名稱", "股票類型"])
#     # 補上 MoM 與 YoY
#     mom_yoy_df = other.get_mom_yoy()
#     df = pd.merge(df, mom_yoy_df, how="left", on=["代號", "名稱"])
#     # 先移除重複的股票
#     df = df[~df.index.duplicated(keep='first')]
#     # 補上技術指標
#     df = other.get_technical_indicators(df)
#     # 再次移除重複的股票
#     df = df[~df.index.duplicated(keep='first')]
#     # 重新按股票代碼排序
#     df = df.sort_index()
#     return df


# # 欲查詢日期
# # search_date = datetime.date(2021,7,12)
# search_date = datetime.date.today()

# final_df = get_all_final(search_date)


# # 基本面篩選
# fundimental_mask = [
# #     per_check_df(final_df, per_threshold=15),
# #     dividend_yield_check_df(final_df, dividend_yield_threshold=1.5),
# #     pbr_check_df(final_df, pbr_threshold=2),
# #     yoy_check_df(final_df, yoy_threshold=10),
# #     mom_check_df(final_df, mom_threshold=10),
# #     acc_yoy_check_df(final_df, acc_yoy_threshold=10)
#     # 月營收月增率 > 10% 或 月營收年增率 > 10%
#     (final_df["(月)營收月增率(%)"] > 10) | (final_df["(月)營收年增率(%)"] > 10),
#     # 累積營收年增率 > 0%
#     final_df["(月)累積營收年增率(%)"] > 0,
# ]

# # 技術面篩選
# technical_mask = [
#     # MA1 > MA5
#     technical_indicator_greater_one_day_check_df(final_df, indicator_1="收盤", indicator_2="mean5", days=1),
#     # 今天 K9 > 昨天 K9
#     technical_indicator_greater_or_less_two_day_check_df(final_df, indicator_1="k9", indicator_2="k9", direction="more", threshold=1, days=1),
#     # 今天 OSC > 昨天 OSC
#     technical_indicator_greater_or_less_two_day_check_df(final_df, indicator_1="osc", indicator_2="osc", direction="more", threshold=1, days=1),
#     # 今天最低 > 昨天最低
#     technical_indicator_greater_or_less_two_day_check_df(final_df, indicator_1="最低", indicator_2="最低", direction="more", threshold=1, days=1),
#     # |今天D9 - 今天K9| < 20
#     technical_indicator_difference_one_day_check_df(final_df, indicator_1="k9", indicator_2="d9", difference_threshold=20, days=1),
#     # 今天的 K9 要介於 20~80 之間
#     technical_indicator_constant_check_df(final_df, indicator="k9", direction="more", threshold=20, days=1),
#     technical_indicator_constant_check_df(final_df, indicator="k9", direction="less", threshold=80, days=1),
#     # (今天 k9-d9) 大於等於 (昨天 k9-d9)
#     technical_indicator_difference_greater_two_day_check_df(final_df, indicator_1="k9", indicator_2="d9", days=1),
#     # 今天成交量 > 500 張 (1000張)
#     volume_greater_check_df(final_df, shares_threshold=1000, days=1),
#     # 今天成交量不能是 3 天內最低量
#     today_volume_is_not_min_check_df(final_df, days=3),
#     # 今天收盤 < 1.08 * 昨天收盤
#     technical_indicator_greater_or_less_two_day_check_df(final_df, indicator_1="收盤", indicator_2="收盤", direction="less", threshold=1.08, days=1),
# ]

# # 籌碼面篩選
# chip_mask = [
#     # 三大法人合計買超
#     total_institutional_buy_positive_check_df(final_df),
#     # 三大法人合計買超股數超過成交量的 10% 或 單一法人至少買超 10%
#     total_institutional_buy_check_df(final_df, total_volume_threshold=10) | single_institutional_buy_check_df(final_df, single_volume_threshold=10)
#     # 外資買超
# #     foreign_buy_positive_check_df(final_df),

# ]

# # 最終選股結果
# final_filter = df_mask_helper(final_df, fundimental_mask + technical_mask + chip_mask)
# final_filter = final_filter.sort_values(by=['成交股數'], ascending=False)
# # print(f"滿足條件的股票共有: {final_filter.shape[0]} 檔 (依照成交量由大到小排序)")
# # print(final_filter)

# print(f"滿足條件的股票共有: {final_filter.shape[0]} 檔 (依照成交量由大到小排序)")
# for i, v in final_filter.iterrows():
#     print(f"{i} {v['名稱']}  {v['產業別']}")

