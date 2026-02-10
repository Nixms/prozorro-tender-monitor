from src.prozorro_api import ProzorroAPI

api = ProzorroAPI()

# Шукаємо тендер UA-2026-02-09-003989-a по tenderID в списку
params = {
    'offset': '',
    'limit': 100,
    'mode': '_all_',
    'descending': 1
}

print("Шукаємо тендер UA-2026-02-09-003989-a...\n")

for page in range(15):
    response = api.session.get(api.api_url, params=params, timeout=30)
    data = response.json()
    tenders = data.get('data', [])
    
    for tender in tenders:
        # Отримуємо деталі кожного тендера і перевіряємо tenderID
        details = api.get_tender_details(tender.get('id'))
        if details:
            tender_id = details.get('tenderID', '')
            if 'UA-2026-02-09-003989' in tender_id:
                print(f"ЗНАЙДЕНО!")
                print(f"Internal ID: {tender.get('id')}")
                print(f"Public ID: {tender_id}")
                print(f"Назва: {details.get('title')}")
                print(f"Тип: {details.get('procurementMethodType')}")
                print(f"Дата: {details.get('dateModified')}")
                exit()
    
    next_page = data.get('next_page', {})
    offset = next_page.get('offset', '')
    if not offset:
        break
    params['offset'] = offset
    print(f"Сторінка {page + 1}... не знайдено")

print("\nТендер не знайдено в останніх 1500 тендерах")