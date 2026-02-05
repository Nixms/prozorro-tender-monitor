import requests

# Спробуємо обидва ID
tender_ids = [
    "UA-2026-02-03-015419-a",  # Короткий формат
    "390e331367a74da7aac848cdb29dc3a1"  # Довгий формат (з сайту)
]

for tender_id in tender_ids:
    print(f"\n{'='*70}")
    print(f"Тестую ID: {tender_id}")
    print(f"{'='*70}")
    
    url = f"https://api.prozorro.gov.ua/api/2.5/tenders/{tender_id}"
    response = requests.get(url)
    
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json().get('data', {})
        print(f"✅ ПРАЦЮЄ!")
        print(f"Назва: {data.get('title', '')[:80]}...")
        print(f"Тип: {data.get('procurementMethodType', '')}")
    else:
        print(f"❌ НЕ ПРАЦЮЄ")