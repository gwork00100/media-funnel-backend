from pytrends.request import TrendReq
import time

def fetch_trends(keywords=["Python"], proxies=None):
    """
    Fetch Google Trends data with optional proxy support.
    """
    pytrends = TrendReq(hl='en-US', tz=360, proxies=proxies)
    time.sleep(2)  # polite delay
    pytrends.build_payload(kw_list=keywords, timeframe='now 1-d', geo='US')
    data = pytrends.related_topics()
    return data
