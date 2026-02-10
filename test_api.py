import requests

session = requests.Session()
session.headers.update({'User-Agent': 'Test', 'Accept': 'application/json'})

url = "https://api.prozorro.gov.ua/api/2.5/tenders"

params = {
    'offset': '',
    'limit': 100,
    'descending': 1,
    'mode': '_all_'
}

print("Рахуємо тендери за останню годину...\n")

count = 0
page = 0

while page < 20:
    response = session.get(url, params=params, timeout=30)
    data = response.json()
    tenders = data.get('data', [])
    
    for tender in tenders:
        date_str = tender.get('dateModified', '')
        # Зараз ~20:30, шукаємо до 19:30
        if '2026-02-09T19:' in date_str or '2026-02-09T18:' in date_str:
            print(f"Дійшли до години тому. Тендерів за годину: {count}")
            exit()
        count += 1
    
    next_offset = data.get('next_page', {}).get('offset')
    if not next_offset:
        break
    params['offset'] = next_offset
    page += 1
    print(f"Сторінка {page}: {count}")

print(f"Всього: {count}")