from apscheduler.schedulers.blocking import BlockingScheduler
import requests
from main import update, broadcast

sched = BlockingScheduler()
wakeup_url = "https://stock-overflow-api.herokuapp.com/wakeup"
update_url = "https://stock-overflow-api.herokuapp.com/update"
broadcast_url = "https://stock-overflow-api.herokuapp.com/broadcast"

# 週一至週五每 20 分鐘喚醒一次
@sched.scheduled_job('cron', day_of_week='mon-fri', minute='*/20')
def scheduled_job():
    r = requests.get(wakeup_url)
    return r.status_code

# 週一至週五 16:30 更新資料
@sched.scheduled_job('cron', day_of_week='mon-fri', hour=20, minute=27)
def scheduled_update():
    update()
    return 


# 週一至週五 17:30 發送推播
@sched.scheduled_job('cron', day_of_week='mon-fri', hour=19, minute=25)
def scheduled_broadcast():
    broadcast()
    return
    
sched.start()