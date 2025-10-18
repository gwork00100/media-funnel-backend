import random

PROXIES = [
    "http://user:pass@proxy1:port",
    "http://user:pass@proxy2:port",
    # add more proxies here
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def get_random_proxy():
    return {"https": random.choice(PROXIES)}
