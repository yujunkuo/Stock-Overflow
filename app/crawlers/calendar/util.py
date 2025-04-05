import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup

from config import logger


def _clean_title(title):
    title_mapping = {
        "講話": "發言",
        "特朗普": "川普",
    }
    title = title.replace(" ", "")
    for key, value in title_mapping.items():
        title = title.replace(key, value)
    return title


def fetch_economic_calendar(date_from: str, date_to: str) -> str:
    url = "https://hk.investing.com/economic-calendar/Service/getCalendarFilteredData"

    headers = {
        'accept': '*/*',
        'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://hk.investing.com',
        'referer': 'https://hk.investing.com/economic-calendar/',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }

    payload = {
        'country[]': ['46', '5'],  # TW and US
        'category[]': [
            '_employment', '_economicActivity', '_inflation',
            '_centralBanks', '_confidenceIndex', '_Bonds'
        ],
        'importance[]': '3',  # most important events
        'dateFrom': date_from,
        'dateTo': date_to,
        'timeZone': '28',  # UTC+8
        'timeFilter': 'timeRemain',
        'currentTab': 'custom',
        'limit_from': '0',
    }

    response = requests.post(url, headers=headers, data=payload)

    if response.status_code == 200:
        logger.info("Fetched economic calendar data successfully.")
        html_content = response.json().get("data", "")
        return html_content
    else:
        logger.error(f"Failed to fetch economic calendar data. Status code: {response.status_code}")
        return ""


def parse_events_from_calendar(html_content: str) -> list:
    soup = BeautifulSoup(html_content, "html.parser")
    rows = soup.select("tr.js-event-item")
    events = []

    for row in rows:
        try:
            date = row.get("data-event-datetime", "").strip()
            country = row.select_one("td.flagCur > span").get("title", "").strip() if row.select_one("td.flagCur > span") else "N/A"
            title = row.select_one("td.event").text.strip() if row.select_one("td.event") else "N/A"

            date = datetime.strptime(date, "%Y/%m/%d %H:%M:%S").strftime("%m/%d %H:%M")
            title = re.sub(r"\s*\(.*?\)", "", title).strip()
            title = _clean_title(title)

            event = {
                "date": date,
                "country": country,
                "title": title,
            }

            if event not in events:
                events.append(event)

        except Exception as e:
            logger.warning(f"Failed to parse economic calendar data: {e}")
            continue

    logger.info(f"Parsed {len(events)} events from the economic calendar.")
    return events