from __future__ import unicode_literals

import datetime
import gc
import os
import threading
import time

import pandas as pd
import psutil
from dotenv import load_dotenv
from flask import Flask, Response, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from crawlers import other, tpex, twse
from strategies import chip_strategy, fundamental_strategy, technical_strategy
from utils import helper

#################### 全域變數設定 ####################

# 版本年份
YEAR = "2024"

# 版本號
VERSION = "v4.1"


# API Interface
app = Flask(__name__)


# 載入環境變數
load_dotenv()


# 設定 LINE Bot 基本資料
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))


# 設定 API Access Token
api_access_token = os.getenv('API_ACCESS_TOKEN')

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


# 檢查 Server 是否活著
@app.route("/", methods=['GET'])
def home():
    # 清除冗余的記憶體使用
    gc.collect()
    # 檢查目前的記憶體使用量
    process = psutil.Process()
    memory_usage = process.memory_info().rss / 1024 ** 2
    print(f"=== 目前記憶體使用量: {memory_usage:.2f} MB ===")
    return Response(status=200)


# 喚醒 Dyno
@app.route("/wakeup", methods=['GET'])
def wakeup():
    # 檢查 request 是否有提供 'API-Access-Token' header
    if 'API-Access-Token' not in request.headers:
        return Response('Missing API-Access-Token', status=401)
    # 驗證提供的 token 是否正確
    elif request.headers['API-Access-Token'] != api_access_token:
        return Response('Invalid API-Access-Token', status=401)
    else:
        print("=== 開始喚醒主機 ===")
        # 指派更新與推播
        update_thread = threading.Thread(target=update)
        update_thread.start()
        return Response(status=200)


# 更新當日推薦股票
def update():
    if not helper.check_weekday():
        print("=== 假日不進行推播 ===")
        return
    else:
        print("=== 開始製作推薦清單 ===")
        final_date = datetime.date.today()
        final_df = get_watching_list(final_date)
        # 若今日休市則不進行後續更新與推播
        if final_df.shape[0] == 0:
            print("=== 今日休市故不推播 ===")
            return
        print("=== 推薦清單製作完成 ===")
        print("=== 開始進行好友推播 ===")
        broadcast(final_date, final_df)
        print("=== 好友推播完成 ===")
        return


# 取得今日股市資料表
def get_watching_list(date) -> pd.DataFrame:
    # 取得上市資料表
    twse_df = twse.get_twse_final(date)
    # 取得上櫃資料表
    tpex_df = tpex.get_tpex_final(date)
    # 兩張表接起來
    df = pd.concat([twse_df, tpex_df])
    # 若今日休市則不進行後續更新與推播
    if df.shape[0] == 0:
        return df
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
    # 印出台積電資料，確保爬蟲取得資料的正確性
    print("---------------------")
    print("核對 [2330 台積電] 今日交易資訊:")
    tsmc = df.loc["2330"]
    for column, value in tsmc.items():
        if type(value) == list and len(value) > 0:
            print(f"{column}: {value[-1]} (history length={len(value)})")
        else:
            print(f"{column}: {value}")
    print("---------------------")
    return df


# 進行盤後推播
def broadcast(final_date, final_df):
    # 顯示目前狀態
    print(f"今日日期: {str(final_date)}")
    print(f"資料表大小: {final_df.shape}")

    # 股票基本面篩選條件
    fundimental_mask = [
        ## (不改的條件 @ 20220723) 不用看基本面，基本面差的個股一樣會飆
        ## 不用看 MOM
        # # 月營收年增率 > 20%
        # final_df["(月)營收年增率(%)"] > 20,
        # # 累積營收年增率 > 10%
        # final_df["(月)累積營收年增率(%)"] > 10,
    ]

    # 股票技術面篩選條件
    technical_mask = [
        # (新條件 @ 20230312) 收盤價必須高於 30 (不碰低價股)
        technical_strategy.technical_indicator_constant_check_df(final_df, indicator="收盤", direction="more", threshold=30, days=1),
        ## (不改的條件 @ 20220603) 收盤價站上 5, 10, 20, 60 均線
        # MA1 > MA5
        technical_strategy.technical_indicator_greater_or_less_one_day_check_df(final_df, indicator_1="收盤", indicator_2="mean5", direction="more", threshold=1, days=1),
        # MA1 > MA10
        technical_strategy.technical_indicator_greater_or_less_one_day_check_df(final_df, indicator_1="收盤", indicator_2="mean10", direction="more", threshold=1, days=1),
        # MA1 > MA20
        technical_strategy.technical_indicator_greater_or_less_one_day_check_df(final_df, indicator_1="收盤", indicator_2="mean20", direction="more", threshold=1, days=1),
        # MA1 > MA60
        technical_strategy.technical_indicator_greater_or_less_one_day_check_df(final_df, indicator_1="收盤", indicator_2="mean60", direction="more", threshold=1, days=1),
        ## (不改的條件 @ 20220723) 今天收紅 K & 實體 K 棒漲幅大於 1% (收盤價 > 1.01 * 開盤價)
        technical_strategy.technical_indicator_greater_or_less_one_day_check_df(final_df, indicator_1="收盤", indicator_2="開盤", direction="more", threshold=1.01, days=1),
        ## (不改的條件 @ 20220723) K 棒底底高
        # (technical_strategy.technical_indicator_greater_or_less_two_day_check_df(final_df, indicator_1="開盤", indicator_2="開盤", direction="more", threshold=1, days=1) |\
        # technical_strategy.technical_indicator_greater_or_less_two_day_check_df(final_df, indicator_1="開盤", indicator_2="收盤", direction="more", threshold=1, days=1)),
        ## (不改的條件 @ 20220723) 今天開盤價 > 昨天收盤價 (開高表示主力表態拉抬)
        # technical_strategy.technical_indicator_greater_or_less_two_day_check_df(final_df, indicator_1="開盤", indicator_2="收盤", direction="more", threshold=1, days=1),
        ## (不改的條件 @ 20220723) 今天收盤 > 昨天最高（頭頭高）
        technical_strategy.technical_indicator_greater_or_less_two_day_check_df(final_df, indicator_1="收盤", indicator_2="最高", direction="more", threshold=1, days=1),
        ## (不改的條件 @ 20220724) 今天 K9 > 昨天 K9
        technical_strategy.technical_indicator_greater_or_less_two_day_check_df(final_df, indicator_1="k9", indicator_2="k9", direction="more", threshold=1, days=1),
        # # 今天 OSC > 昨天 OSC
        # technical_strategy.technical_indicator_greater_or_less_two_day_check_df(final_df, indicator_1="osc", indicator_2="osc", direction="more", threshold=1, days=1),
        ## |今天D9 - 今天K9| < 22
        technical_strategy.technical_indicator_difference_one_day_check_df(final_df, indicator_1="k9", indicator_2="d9", difference_threshold=22, days=1),
        ## 今天的 K9 要介於 49 ~ 87 之間
        # technical_strategy.technical_indicator_constant_check_df(final_df, indicator="k9", direction="more", threshold=49, days=1),
        # technical_strategy.technical_indicator_constant_check_df(final_df, indicator="k9", direction="less", threshold=87, days=1),
        # 今天的 J9 要小於 100
        technical_strategy.technical_indicator_constant_check_df(final_df, indicator="j9", direction="less", threshold=100, days=1),
        ## (今天 k9-d9) 大於等於 (昨天 k9-d9)
        # technical_strategy.technical_indicator_difference_greater_two_day_check_df(final_df, indicator_1="k9", indicator_2="d9", days=1),
        # # 5 日線趨勢向上 (MA5 趨勢向上)
        # technical_strategy.technical_indicator_greater_or_less_two_day_check_df(final_df, indicator_1="mean5", indicator_2="mean5", direction="more", threshold=1, days=1),
        ## (不改的條件 @ 20220724) 今天收盤 > 1.03 * 昨天收盤 (只抓今日漲幅 3% 以上的股票)
        technical_strategy.technical_indicator_greater_or_less_two_day_check_df(final_df, indicator_1="收盤", indicator_2="收盤", direction="more", threshold=1.03, days=1),
        ## (不改的條件 @ 20220724) 不能連續兩天漲幅超過 5%
        ~technical_strategy.technical_indicator_greater_or_less_two_day_check_df(final_df, indicator_1="收盤", indicator_2="收盤", direction="more", threshold=1.05, days=2),
        # ## 今天收盤 < 1.1 * Mean5 or Mean10 or Mean20 (不抓取乖離過大的股票)
        # technical_strategy.technical_indicator_greater_or_less_one_day_check_df(final_df, indicator_1="收盤", indicator_2="mean5", direction="less", threshold=1.1, days=1) |\
        # technical_strategy.technical_indicator_greater_or_less_one_day_check_df(final_df, indicator_1="收盤", indicator_2="mean10", direction="less", threshold=1.1, days=1) |\
        # technical_strategy.technical_indicator_greater_or_less_one_day_check_df(final_df, indicator_1="收盤", indicator_2="mean20", direction="less", threshold=1.1, days=1),
        ## 今天最高價不是一年內的最高 (不追高) -> 今天最高價不是四個月內的最高 (只抓得到四個月)
        # technical_strategy.today_price_is_not_max_check_df(final_df, price_type="最高", days=80),
        ## (不改的條件 @ 20220822) 上影線長度不能超過昨天收盤價的 2.2% (0.022) / 0% (0.000001) 以上
        technical_strategy.technical_indicator_difference_two_day_check_df(final_df, indicator_1="最高", indicator_2="收盤", direction="less", threshold=0.022, indicator_3="收盤", days=1),
        # # OSC 必須要大於0 (經驗顯示 OSC 大於 0 後勢出現強勁漲幅的機會較高)
        # technical_strategy.technical_indicator_constant_check_df(final_df, indicator="osc", direction="more", threshold=0, days=1),
        # DIF 要大於 0
        # technical_strategy.technical_indicator_constant_check_df(final_df, indicator="dif", direction="more", threshold=0, days=1),
        # [(DIF / 收盤價) < 0.03] 或 [DIF 不是四個月內的最高]
        technical_strategy.technical_indicator_greater_or_less_one_day_check_df(final_df, indicator_1="dif", indicator_2="收盤", direction="less", threshold=0.03, days=1) | 
        technical_strategy.today_price_is_not_max_check_df(final_df, price_type="dif", days=80),
    ]

    # 股票籌碼面篩選條件
    chip_mask = [
        ## (不改的條件 @ 20220723) 今天成交量 > 2000 張
        technical_strategy.volume_greater_check_df(final_df, shares_threshold=2000, days=1),
        ## 今天成交量不能是 2 天內最低量 (今天成交量要比昨天高)
        # technical_strategy.today_volume_is_not_min_check_df(final_df, days=2),
        ## (不改的條件 @ 20220603) 今天成交量要大於昨天成交量
        technical_strategy.technical_indicator_greater_or_less_two_day_check_df(final_df, indicator_1="volume", indicator_2="volume", direction="more", threshold=1, days=1),
        ## (不改的條件 @ 20220603) 今量 > 5日均量
        technical_strategy.technical_indicator_greater_or_less_one_day_check_df(final_df, indicator_1="volume", indicator_2="mean_5_volume", direction="more", threshold=1, days=1),
        # # 5日均量 > 20日均量
        # technical_strategy.technical_indicator_greater_or_less_one_day_check_df(final_df, indicator_1="mean_5_volume", indicator_2="mean_20_volume", direction="more", threshold=1, days=1),
        # 5日均量 > 1000
        technical_strategy.technical_indicator_constant_check_df(final_df, indicator="mean_5_volume", direction="more", threshold=1000, days=1),
        # 20日均量 > 1000
        technical_strategy.technical_indicator_constant_check_df(final_df, indicator="mean_20_volume", direction="more", threshold=1000, days=1),
        ## 「今天的5日均量」要大於「昨天的5日均量」
        technical_strategy.technical_indicator_greater_or_less_two_day_check_df(final_df, indicator_1="mean_5_volume", indicator_2="mean_5_volume", direction="more", threshold=1, days=1),
        # 單一法人至少買超成交量的 10%
        # chip_strategy.single_institutional_buy_check_df(final_df, single_volume_threshold=10),
        # 三大法人合計買超至少超過成交量的 1%
        # chip_strategy.total_institutional_buy_check_df(final_df, total_volume_threshold=1),
        # 外資買超至少超過 -1 股 (大於等於 0) (200 張 -> threshold=2e5)
        chip_strategy.foreign_buy_positive_check_df(final_df, threshold=-1),
        # # 投信買超至少超過 50 張
        # chip_strategy.investment_buy_positive_check_df(final_df, threshold=5e4),
        ## (不改的條件 @ 20220723) 自定義法人買超張數篩選 (法人買賣常常跟起漲點相反)
        # chip_strategy.buy_positive_check_df(final_df),
        ## (不改的條件 @ 20220723) 三大法人合計買超為正值 (法人買賣常常跟起漲點相反)
        # chip_strategy.total_institutional_buy_positive_check_df(final_df, threshold=0),
    ]

    # 取得推薦觀察清單
    final_filter = helper.df_mask_helper(final_df, fundimental_mask + technical_mask + chip_mask)
    final_filter = final_filter.sort_values(by=["產業別"], ascending=False)
    final_filter = final_filter[final_filter.index.to_series().apply(technical_strategy.is_skyrocket)]
    # 轉換為字串回傳
    final_recommendation_text = ""
    # 建構推播訊息
    if len(final_filter) == 0:
        final_recommendation_text = f"🔎 今日無 [推薦觀察] 股票\n"
        print("今日無 [推薦觀察] 股票")
    else:
        final_recommendation_text = f"🔎 [推薦觀察]  股票有 {len(final_filter)} 檔\n" + "\n###########\n\n"
        print(f"[推薦觀察] 股票有 {len(final_filter)} 檔")
        for i, v in final_filter.iterrows():
            final_recommendation_text += f"{i} {v['名稱']}  {v['產業別']}\n"
            print(f"{i} {v['名稱']}  {v['產業別']}")
    # 加上末尾分隔線
    final_recommendation_text += "\n###########\n\n"
    # 加上資料來源說明
    final_recommendation_text += f"資料來源: 台股 {str(final_date)}"
    # 加上版權聲明
    final_recommendation_text += f"\nJohnKuo © {YEAR} ({VERSION})"
    # 透過 LINE API 進行推播
    line_bot_api.broadcast(TextSendMessage(text=final_recommendation_text))
    return


####################################################

if __name__ == "__main__":
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
