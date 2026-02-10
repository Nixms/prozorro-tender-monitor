import requests

# Спробуємо знайти тендер напряму через пошук
url = "https://api.prozorro.gov.ua/api/2.5/tenders"

# Пошук по даті публікації 09.02.2026
params = {
    'offset': '',
    'limit': 100,
    'mode': '_all_',
    'descending': 1
}

session = requests.Session()
session.headers.update({'User-Agent': 'Test', 'Accept': 'application/json'})

response = session.get(url, params=params, timeout=30)
data = response.json()

print(f"Отримано {len(data.get('data', []))} тендерів")
print(f"\nПерші 3 tenderID:")

for tender in data.get('data', [])[:3]:
    # Отримуємо деталі
    detail_url = f"{url}/{tender.get('id')}"
    detail_resp = session.get(detail_url, timeout=30)
    detail_data = detail_resp.json().get('data', {})
    print(f"  {detail_data.get('tenderID')} - {detail_data.get('dateModified')}")

print(f"\nШукаємо 003989...")

# Шукаємо наш тендер
for page in range(5):
    for tender in data.get('data', []):
        detail_url = f"{url}/{tender.get('id')}"
        detail_resp = session.get(detail_url, timeout=30)
        detail_data = detail_resp.json().get('data', {})
        
        if detail_data.get('tenderID') and '003989' in detail_data.get('tenderID'):
            print(f"\nЗНАЙДЕНО: {detail_data.get('tenderID')}")
            print(f"Назва: {detail_data.get('title')}")
            print(f"Тип: {detail_data.get('procurementMethodType')}")
            exit()
    
    next_offset = data.get('next_page', {}).get('offset')
    if not next_offset:
        break
    params['offset'] = next_offset
    response = session.get(url, params=params, timeout=30)
    data = response.json()
    print(f"Сторінка {page+2}...")

print("\nНе знайдено")