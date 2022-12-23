# Stock-Overflow

## Deployment Tools
- Web Service: [render](https://render.com/)
- Scheduler: [cron-job](https://cron-job.org/en/)
- LINE Chatbot: [LINE Developers](https://developers.line.biz/zh-hant/)

## How to Deploy the Service
1. Create **render.yaml** file in your repo (Can find template from [here](https://github.com/haojiwu/line-bot-python-on-render))
    - Modify the value of name, repo, buildCommand, startCommand, and envVars
2. Direct to render's [blueprint](https://dashboard.render.com/blueprints), and create new instance with the target repo and **render.yaml** file
    - Environment Variable ```CHANNEL_ACCESS_TOKEN``` and ```CHANNEL_SECRET``` can be found from [LINE Developers](https://developers.line.biz/zh-hant/)
    - Environment Variable ```TZ``` should be set to ```Asia/Taipei```
3. After create and run the instance, you will get a service URL of this web service from the dashboard (e.g. https://stock-overflow-api.onrender.com)
4. Add ```/callback``` after the service URL to build the webhook URL, and paste the webhook URL to the ```LINE Webhook URL``` section in [LINE Developers](https://developers.line.biz/zh-hant/)
5. Update the settings of Scheduler (e.g. [cron-job](https://cron-job.org/en/)) to get notification 

## Reference
- https://ithelp.ithome.com.tw/articles/10283836
- https://github.com/haojiwu/line-bot-python-on-render
- https://bamorlove.com/blog/render
