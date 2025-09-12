import requests

# Replace with your actual API URL
API_URL = "http://localhost:8000/process-trend"

# Sample trend topics to test
trend_topics = [
    "AI advancements",
    "Climate change",
    "Space exploration",
]

def test_trends():
    for trend in trend_topics:
        print(f"Sending trend topic: {trend}")
        try:
            response = requests.post(API_URL, json={"trend": trend})
            response.raise_for_status()  # Raises error for bad responses

            data = response.json()
            print(f"Response for '{trend}':")
            print(data)
            print("-" * 40)

        except requests.exceptions.RequestException as e:
            print(f"Error for trend '{trend}': {e}")

if __name__ == "__main__":
    test_trends()
