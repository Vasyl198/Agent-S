import requests
import json

try:
    r = requests.post(
        'http://localhost:11434/api/generate',
        json={
            'model': 'codellama:7b-instruct', 
            'prompt': 'Напиши рабочий Python-код для парсинга сайтов', 
            'stream': False
        }, 
        timeout=300
    )
    print('Status:', r.status_code)
    if r.status_code == 200:
        response = r.json()
        print('Response:', response.get('response', '')[:500])
    else:
        print('Error:', r.text[:500])
except Exception as e:
    print('Exception:', e)
