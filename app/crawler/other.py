# Standard library imports
import datetime
import json
import warnings
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

# Third-party imports
import pandas as pd
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# Local imports
from app.crawler.common.base import ApiEndpointConfig, DataFetcher, DataProcessor, DataAggregator
from app.crawler.common.decorator import retry_on_failure, log_execution_time
from app.utils import convert_milliseconds_to_date
from config import config, logger
from model.data_type import DataType

warnings.simplefilter(action="ignore", category=FutureWarning)


@dataclass
class OtherApiEndpointConfig(ApiEndpointConfig):
    """Configuration for other API endpoints."""
    headers: Dict[str, str] = None


class IndustryCategoryFetcher(DataFetcher):
    """Class to handle API requests for industry category data."""
    
    API_ENDPOINT = OtherApiEndpointConfig(
        url="https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInfo",
    )
    
    @classmethod
    @retry_on_failure(
        max_retries=3,
        fallback=lambda cls, data_type: (
            logger.warning(f"{cls.__name__} fetch failed for data type: {data_type.value}") or
            pd.DataFrame(columns=config.COLUMN_KEEP_SETTING[data_type])
        )
    )
    def fetch_data(cls, data_type: DataType) -> pd.DataFrame:
        """Fetch data from FinMind API with retry mechanism."""
        response = requests.get(cls.API_ENDPOINT.url)
        response.raise_for_status()
        data = response.json()["data"]
        return pd.DataFrame(data)


class IndustryCategoryProcessor(DataProcessor):
    """Class to handle industry category data processing operations."""

    @classmethod
    def process_data(cls, data_type: DataType, df: pd.DataFrame) -> pd.DataFrame:
        """Process industry category data.""" 
        if df.empty:
            return df
        
        df = cls._standardize_columns(df)
        
        # Keep only columns defined in config settings for this data type
        df = df[df.columns.intersection(config.COLUMN_KEEP_SETTING[data_type])]

        # Remove duplicate rows, keeping the row with shortest industry category name
        df = df.sort_values("產業別", key=lambda x: x.str.len()).drop_duplicates("代號", keep="first")
        
        # Sort and reset index
        return df.sort_values(by=["代號"]).reset_index(drop=True)


class MomYoyFetcher(DataFetcher):
    """Class to handle API requests for MoM/YoY data."""
    
    API_ENDPOINT = OtherApiEndpointConfig(
        url="https://stock.wespai.com/p/44850",
        headers={
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        }
    )
    
    @classmethod
    @retry_on_failure(
        max_retries=3,
        fallback=lambda cls, data_type: (
            logger.warning(f"{cls.__name__} fetch failed for data type: {data_type.value}") or
            pd.DataFrame(columns=config.COLUMN_KEEP_SETTING[data_type])
        )
    )
    def fetch_data(cls, data_type: DataType) -> pd.DataFrame:
        """Fetch MoM/YoY data from wespai.com with retry mechanism."""
        response = requests.get(cls.API_ENDPOINT.url, headers=cls.API_ENDPOINT.headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        data = soup.find_all("td")
        
        mom_yoy_list = [
            [
                data[x].text,
                data[x+1].select_one("a").text,
                data[x+3].text,
                data[x+4].text,
                data[x+5].text,
            ]
            for x in range(0, len(data), 6)
        ]
        
        return pd.DataFrame(mom_yoy_list, columns=config.COLUMN_KEEP_SETTING[data_type])


class MomYoyProcessor(DataProcessor):
    """Class to handle MoM/YoY data processing operations."""

    @classmethod
    def process_data(cls, data_type: DataType, df: pd.DataFrame) -> pd.DataFrame:
        """Process MoM/YoY data."""
        if df.empty:
            return df
        
        df = cls._standardize_columns(df)
        df = cls._convert_to_numeric(df)
        
        # Keep only columns defined in config settings for this data type
        df = df[df.columns.intersection(config.COLUMN_KEEP_SETTING[data_type])]
        
        # Sort and reset index
        return df.sort_values(by=["代號"]).reset_index(drop=True)


class TechnicalIndicatorsFetcher(DataFetcher):
    """Class to handle API requests for technical indicators data."""
    
    API_ENDPOINT = OtherApiEndpointConfig(
        # days = 240 may causes OOM; days = 120 may miss latest data; original API uses days = 80
        url="https://histock.tw/stock/chip/chartdata.aspx?no={stock_id}&days=80&m=dailyk,close,volume,mean5,mean10,mean20,mean60,mean5volume,mean20volume,k9,d9,dif,macd,osc",
    )
    
    @classmethod
    @retry_on_failure(max_retries=2)
    def fetch_data(cls, stock_id: str) -> Optional[Dict[str, Any]]:
        """Fetch technical indicators data from histock with retry mechanism."""
        headers = {
            "User-Agent": UserAgent().random,
            "authority": "histock.tw",
            "referer": f"https://histock.tw/stock/{stock_id}",
        }
        url = cls.API_ENDPOINT.url.format(stock_id=stock_id)
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()


class TechnicalIndicatorsProcessor(DataProcessor):
    """Class to handle technical indicators data processing operations."""
    
    @staticmethod
    def _format_technical_indicator_list(technical_indicator_list: List[Any], data_date: datetime.date) -> List[Any]:
        """Format certain technical indicator data up to a given date."""
        filtered_indicators = []
        for indicator_time, indicator_value in technical_indicator_list:
            indicator_time = convert_milliseconds_to_date(indicator_time)
            if indicator_time <= data_date:
                filtered_indicators.append([indicator_time, indicator_value])
            else:
                break
        return filtered_indicators
    
    @staticmethod
    def _format_daily_k_list(daily_k_list: List[Any], data_date: datetime.date) -> List[Any]:
        """Format daily K data up to a given date."""
        filtered_ks = []
        for k_time, *k_values in daily_k_list:
            k_time = convert_milliseconds_to_date(k_time)
            if k_time <= data_date:
                k_value = {
                    "開盤": k_values[0],
                    "最高": k_values[1],
                    "最低": k_values[2],
                    "收盤": k_values[3],
                }
                filtered_ks.append([k_time, k_value])
            else:
                break
        return filtered_ks
    
    @staticmethod
    def _get_j9_list(k9_list: List[float], d9_list: List[float]) -> List[float]:
        """Calculate J9 values from K9 and D9 values."""
        j9_list = []
        for (date, k9_value), (_, d9_value) in zip(k9_list, d9_list):
            j9_value = round(3 * k9_value - 2 * d9_value, 2)
            j9_list.append([date, j9_value])
        return j9_list
    
    @classmethod
    def process_data(cls, technical_indicators: Dict[str, Any], data_date: datetime.date) -> Optional[Dict[str, Any]]:
        """Process technical indicators data."""
        if not technical_indicators:
            return None

        # Process each indicator
        indicators = {}
        for key in ["K9", "D9", "DIF", "MACD", "OSC", "Mean5", "Mean10", "Mean20", "Mean60", "Volume", "Mean5Volume", "Mean20Volume"]:
            value = cls._format_technical_indicator_list(json.loads(technical_indicators[key]), data_date)
            indicators[key.lower()] = value
            
        # Process daily K indicator
        indicators["daily_k"] = cls._format_daily_k_list(json.loads(technical_indicators["DailyK"]), data_date)
            
        # Calculate J9 indicator
        indicators["j9"] = cls._get_j9_list(indicators["k9"], indicators["d9"])
        
        return indicators


def fetch_and_process_industry_category(data_type: DataType) -> pd.DataFrame:
    """Fetch and process industry category data."""
    df = IndustryCategoryFetcher.fetch_data(data_type)
    return IndustryCategoryProcessor.process_data(data_type, df)


def fetch_and_process_mom_yoy(data_type: DataType) -> pd.DataFrame:
    """Fetch and process MoM/YoY data."""
    df = MomYoyFetcher.fetch_data(data_type)
    return MomYoyProcessor.process_data(data_type, df)


def _fetch_and_process_technical_indicators_by_stock_id(stock_id: str, data_date: datetime.date) -> Optional[Dict[str, Any]]:
    """Fetch and process technical indicators data for a specific stock."""
    technical_indicators = TechnicalIndicatorsFetcher.fetch_data(stock_id)
    return TechnicalIndicatorsProcessor.process_data(technical_indicators, data_date)


def fetch_and_process_technical_indicators(reference_df: pd.DataFrame, data_date: datetime.date) -> pd.DataFrame:
    """
    Fetch and process technical indicators for all stocks sequentially.
    
    Args:
        reference_df: DataFrame containing stock information
        data_date: Date to process data up to
        
    Returns:
        DataFrame containing processed technical indicators
    """
    # Initialize result columns
    result_columns = ["名稱", "代號"] + [
        "k9", "d9", "j9", "dif", "macd", "osc",
        "mean5", "mean10", "mean20", "mean60",
        "volume", "mean5volume", "mean20volume", "daily_k",
    ]
    
    # Get stock information
    stock_info = reference_df[["名稱", "代號"]].values.tolist()
    total_stocks = len(stock_info)
    all_results = []
    print_flag = False
    
    # Process stocks sequentially
    for idx, (name, stock_id) in enumerate(stock_info, 1):
        try:
            technical_indicators = _fetch_and_process_technical_indicators_by_stock_id(stock_id, data_date)
            if technical_indicators:
                result = {
                    "名稱": name,
                    "代號": stock_id,
                    **{col: technical_indicators.get(col) for col in result_columns[2:]}
                }
                all_results.append(result)
            
            # Log progress every 100 stocks
            if idx % 100 == 0 or print_flag:
                print_flag = False
                logger.info(f"Processed technical data: {idx}/{total_stocks} ({(idx/total_stocks)*100:.1f}%), stock_id = {stock_id}")
        except:
            if idx % 100 == 0:
                print_flag = True
    
    # Convert results to DataFrame
    result_df = pd.DataFrame(all_results) if all_results else pd.DataFrame(columns=result_columns)
    return result_df.sort_values(by=["代號"]).reset_index(drop=True)


class OtherDataAggregator(DataAggregator):
    """Class to handle other data aggregating for different data types."""
    
    # Class-level configuration
    MERGE_KEYS = ["代號", "名稱"]
    
    @classmethod
    def _retrieve_all_dataframes(cls, data_date: datetime.date) -> List[pd.DataFrame]:
        """Retrieve all required dataframes for a given date."""
        # Get industry category data
        industry_category_df = fetch_and_process_industry_category(DataType.INDUSTRY_CATEGORY)
        
        # Get MoM/YoY data
        mom_yoy_df = fetch_and_process_mom_yoy(DataType.MOM_YOY)
        
        # Get technical indicators data
        technical_indicators_df = fetch_and_process_technical_indicators(industry_category_df, data_date)
        
        return [industry_category_df, mom_yoy_df, technical_indicators_df]
    
    @classmethod
    @log_execution_time(log_message="取得其他資料表花費時間")
    def aggregate_data(cls, data_date: datetime.date) -> Optional[pd.DataFrame]:
        """Aggregate all other data for a given date."""
        # Retrieve dataframes for all data types
        dfs = cls._retrieve_all_dataframes(data_date)
            
        # Combine dataframes
        df = cls._combine_dataframes(dfs)
            
        # Set index
        df = df.set_index("代號")
        
        return df


def get_other_data(data_date: datetime.date) -> Optional[pd.DataFrame]:
    """Get final aggregated other data for a given date."""
    return OtherDataAggregator.aggregate_data(data_date)