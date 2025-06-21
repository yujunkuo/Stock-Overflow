# Third-party imports
from flask import current_app
from linebot.models import TextSendMessage

# Local imports
from app.core import logger


# Broadcast the watch list
def broadcast_watch_list(target_date, watch_list_dfs, economic_events, need_broadcast):
    # Final recommendation text message
    final_recommendation_text = ""
    # Append the recommendation stocks
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
        final_recommendation_text += "\n###########\n\n"
    # Append the economic events
    if len(economic_events) != 0:
        final_recommendation_text += "📆 預計經濟事件\n" + "\n###########\n\n"
        logger.info("預計經濟事件")
        for event in economic_events:
            final_recommendation_text += f"{event['date']} - {event['country']} - {event['title']}\n"
            logger.info(f"{event['date']} - {event['country']} - {event['title']}")
        final_recommendation_text += "\n###########\n\n"
    # Append the source information
    final_recommendation_text += f"資料來源: 台股 {str(target_date)}"
    # Append the version information
    final_recommendation_text += f"\nJohnKuo © {current_app.config['YEAR']} ({current_app.config['VERSION']})"
    # Broadcast the final recommendation text message if needed
    if need_broadcast:
        line_bot_api = current_app.config["LINE_BOT_API"]
        line_bot_api.broadcast(TextSendMessage(text=final_recommendation_text))
