from agents.google_trends_agent import fetch_google_trends

if __name__ == "__main__":
    input_json = '{"region": "united_states"}'
    summary = fetch_google_trends.invoke(input_json)
    print(summary)
