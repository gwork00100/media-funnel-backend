from pytrends.request import TrendReq
import time

pytrends = TrendReq(hl='en-US', tz=360)
time.sleep(2)

try:
    df = pytrends.trending_searches(pn='united_states')
    print(df.head(10))
except Exception as e:
    print(f"Error: {e}")
