# Standard library imports
import re
from datetime import datetime

# Third-party imports
import requests
from bs4 import BeautifulSoup

# Local imports
from config import logger


def _clean_title(title: str) -> str:
    """Clean and standardize event titles."""
    # Map simplified Chinese terms to traditional Chinese terms
    title_mapping = {
        "講話": "發言",
        "特朗普": "川普",
    }
    title = title.replace(" ", "")
    for key, value in title_mapping.items():
        title = title.replace(key, value)
    return title


def _fetch_economic_calendar(date_from: str, date_to: str) -> str:
    """Fetch economic calendar data from Investing.com for a specified date range."""
    # API endpoint
    url = "https://hk.investing.com/economic-calendar/Service/getCalendarFilteredData"

    # Headers to mimic browser request
    headers = {
        'accept': '*/*',
        'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://hk.investing.com',
        'referer': 'https://hk.investing.com/economic-calendar/',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }

    # Request parameters for filtering economic events
    payload = {
        'country[]': ['46', '5'],  # 46: Taiwan, 5: United States
        'category[]': [
            '_employment', '_economicActivity', '_inflation',
            '_centralBanks', '_confidenceIndex', '_Bonds'
        ],
        'importance[]': '3',  # Filter for high importance events only
        'dateFrom': date_from,
        'dateTo': date_to,
        'timeZone': '28',  # UTC+8 timezone
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


def _parse_events_from_calendar(html_content: str) -> list:
    """Parse economic events from the HTML content of the calendar."""
    soup = BeautifulSoup(html_content, "html.parser")
    rows = soup.select("tr.js-event-item")
    events = []

    for row in rows:
        try:
            # Extract event details from each row
            date = row.get("data-event-datetime", "").strip()
            country = row.select_one("td.flagCur > span").get("title", "").strip() if row.select_one("td.flagCur > span") else "N/A"
            title = row.select_one("td.event").text.strip() if row.select_one("td.event") else "N/A"

            # Format date and clean title
            date = datetime.strptime(date, "%Y/%m/%d %H:%M:%S").strftime("%m/%d %H:%M")
            title = re.sub(r"\s*\(.*?\)", "", title).strip()  # Remove text in parentheses
            title = _clean_title(title)

            event = {
                "date": date,
                "country": country,
                "title": title,
            }

            # Avoid duplicate events
            if event not in events:
                events.append(event)

        except Exception as e:
            logger.warning(f"Failed to parse economic calendar data: {e}")
            continue

    logger.info(f"Parsed {len(events)} events from the economic calendar.")
    return events


def get_economic_events(date_from: str, date_to: str) -> list:
    """
    Get economic events from Investing.com calendar for a specified date range.
    
    This function fetches and parses economic calendar data, including important
    economic indicators, central bank meetings, and other significant financial events.
    
    Args:
        date_from (str): Start date in format 'YYYY-MM-DD'
        date_to (str): End date in format 'YYYY-MM-DD'
        
    Returns:
        list: List of dictionaries containing economic events
              Each event contains:
              - date: Event date and time (MM/DD HH:MM)
              - country: Country where the event occurs
              - title: Event title/description
    """
    # Fetch the economic calendar data
    economic_calendar = _fetch_economic_calendar(date_from, date_to)
    if not economic_calendar:
        return []
    # Parse the events from the fetched data
    events = _parse_events_from_calendar(economic_calendar)
    return events