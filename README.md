# 💵 Stock-Overflow 💶


## 🔎 Overview
**Stock-Overflow** is a **stock recommendation system** tailored for the Taiwanese stock market. It leverages various strategies and indicators to identify potentially lucrative stock investment opportunities. The system provides recommendations based on fundamental analysis, technical analysis, and chip analysis. Additionally, it utilizes web scraping to fetch real-time stock market data and sends recommendations to users via the LINE messaging platform.


## 📌 Features
- **Highly Customizable Filtering Criteria:** Tailor screening conditions to match specific investment preferences, allowing users to define criteria that align with their unique strategies.

- **Convenient Daily Push Notifications via LINE:** Enjoy the convenience of receiving daily stock recommendations directly through LINE messaging, ensuring users stay informed without the need for manual checks.


## 🪄 Deployment Tools
- **Web Service:** [Render](https://render.com/)
- **Scheduler:** [Cron-job](https://cron-job.org/en/)
- **LINE Chatbot:** [LINE Developers](https://developers.line.biz/zh-hant/)


## 🔖 How to Deploy the Service
1. Modify the **`render.yaml`** file in your repository. (You can also find the template [here](https://github.com/haojiwu/line-bot-python-on-render).)
    - Modify the value of `name`, `repo`, and maybe some values of `envVars`.

2. Navigate to **Render**'s [blueprint](https://dashboard.render.com/blueprints), and create a new instance with the target repository and the **`render.yaml`** file.
    - The environment variables `CHANNEL_ACCESS_TOKEN` and `CHANNEL_SECRET` can be found from [LINE Developers](https://developers.line.biz/zh-hant/).
    - The environment variable `API_ACCESS_TOKEN` should be designated with a unique value to enhance the security.
    - The environment variable `TZ` should be configured to `Asia/Taipei`.

3. Upon creating and running the instance, you will receive a service URL for this web service from the dashboard (e.g., https://stock-overflow-api.onrender.com).

4. Append `/callback` to the service URL to construct the webhook URL. Paste this webhook URL into the `LINE Webhook URL` section on [LINE Developers](https://developers.line.biz/zh-hant/).

5. Configure the scheduler (e.g., [Cron-job](https://cron-job.org/en/)) to invoke the `/wakeup` API endpoint at designated times daily, ensuring users receive notifications.


## 💬 LINE Notification Message
Below is an example of what the LINE notification message looks like:

<img src="line_notification.jpg" alt="LINE Notification Screenshot" width="47%"/>


## 🧷 Reference
- https://render.com/
- https://cron-job.org/en/
- https://developers.line.biz/en/
- https://ithelp.ithome.com.tw/articles/10283836
- https://github.com/haojiwu/line-bot-python-on-render
- https://bamorlove.com/blog/render


## 🧸 Contributing
Contributions are greatly welcome and appreciated! 

Thank you for being part of this project! 🎉