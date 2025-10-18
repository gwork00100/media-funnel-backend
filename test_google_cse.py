import requests

# ✅ Replace these with your actual credentials
API_KEY = 'AIzaSyDz7HXgh4t8C-7Tw_DH1d6zaMe3LlZdwxY'
CX = '30898967c7dd54c74'  # Your real Search Engine ID

query = 'AI trends 2025'

url = f'https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={CX}&q={query}'

response = requests.get(url)
results = response.json()

for item in results.get('items', []):
    print(item['title'])
    print(item['link'])
    print('---')
