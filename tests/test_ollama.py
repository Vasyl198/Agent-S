import requests
import json

try:
    r = requests.post(
        'http://localhost:11434/api/generate',
        json={
            'model': 'deepseek-coder:6.7b', 
            'prompt': 'print("hello")', 
            'stream': False
        }, 
        timeout=10
    )
    print('Status:', r.status_code)
    if r.status_code == 200:
        response = r.json()
        print('Response:', response.get('response', '')[:200])
    else:
        print('Error:', r.text[:200])
except Exception as e:
    print('Exception:', e)
