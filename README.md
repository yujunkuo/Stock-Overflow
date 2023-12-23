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

2. Go to **Render**'s [blueprint](https://dashboard.render.com/blueprints), create a new instance with the target repository and the **`render.yaml`** file.
    - The environment variables `CHANNEL_ACCESS_TOKEN` and `CHANNEL_SECRET` can be found from [LINE Developers](https://developers.line.biz/zh-hant/).
    - The environment variable `API_ACCESS_TOKEN` should be designated with a unique value to enhance the security.
    - The environment variable `TZ` should be configured to `Asia/Taipei`.

3. Upon creating and running the instance, you will receive a service URL for this web service from the dashboard (e.g., https://stock-overflow-api.onrender.com).

4. Append `/callback` to the service URL to construct the webhook URL. Paste this webhook URL into the `LINE Webhook URL` section on [LINE Developers](https://developers.line.biz/zh-hant/).

5. Configure the scheduler (e.g., [Cron-job](https://cron-job.org/en/)) to invoke the `/wakeup` API endpoint at designated times daily, ensuring users receive notifications.


## 💬 LINE Notification Message
Below is an example of what the LINE notification message looks like:

<img src="line_notification.jpg" alt="LINE Notification Screenshot" width="38%"/>


## ⚠️ Disclaimer and Customization
**Please** note that Stock-Overflow is a stock recommendation system offering investment advice for informational purposes only. We do not assume any responsibility for financial decisions made based on our recommendations. Investing in the stock market involves risks, and users are advised to exercise caution and conduct their own research before making any investment decisions.

**Moreover,** the system's filtering criteria can be adjusted according to individual investment preferences. Users can modify the source code's stock screening conditions to better align with their unique investment strategies. Feel free to explore and adapt the criteria to suit your preferences and risk tolerance.


## 🧷 Reference
- https://render.com/
- https://cron-job.org/en/
- https://developers.line.biz/en/
- https://ithelp.ithome.com.tw/articles/10283836
- https://github.com/haojiwu/line-bot-python-on-render
- https://bamorlove.com/blog/render


## 🧸 Contributing
Your contributions or suggestions are not only greatly welcome but also truly appreciated! If you have any idea for enhancements or something amazing brewing in your mind, please don't hesitate to create a pull request. Your feedback is invaluable, and every contribution, no matter how small, has the power to make a significant impact.

Thank you for being a crucial part of this project and for bringing your unique brilliance to the table! Let's create something extraordinary together! 🎉