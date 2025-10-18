from pytrends.request import TrendReq

def fetch_daily_trends():
    pytrends = TrendReq(hl='en-US', tz=360)
    for pn in ['united_states', 'p1', 'global', 'us', 'p30']:
        try:
            daily_trends = pytrends.trending_searches(pn=pn)
            print(f"Success for region: {pn}")
            top_10 = daily_trends[0].tolist()[:10]
            return top_10
        except Exception as e:
            print(f"Failed for region '{pn}': {e}")
    raise Exception("No valid region found.")

if __name__ == "__main__":
    trends = fetch_daily_trends()
    print("Top 10 Trending Searches:")
    for i, trend in enumerate(trends, 1):
        print(f"{i}. {trend}")
