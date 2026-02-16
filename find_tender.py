import requests

# Пошук по descending (від нових до старих) починаючи з зараз
s = requests.Session()
offset = ''
page = 0

while page < 150:
    params = {'offset': offset, 'limit': 100, 'mode': '_all_', 'descending': 1}
    r = s.get('https://api.prozorro.gov.ua/api/2.5/tenders', params=params)
    data = r.json()
    for t in data['data']:
        if t['id'] in ['4355d7fff5f248b69aa9725b394f61d5']:
            continue
        d = s.get(f'https://api.prozorro.gov.ua/api/2.5/tenders/{t["id"]}').json().get('data', {})
        if d.get('tenderID') == 'UA-2026-02-11-015038-a':
            print(f'FOUND! Internal ID: {t["id"]}')
            print(f'title: {d.get("title")}')
            from src.telegram_bot import TelegramNotifier
            TelegramNotifier().send_tender_notification(d)
            print('Sent to Telegram!')
            exit()
    offset = data.get('next_page', {}).get('offset', '')
    page += 1
    if page % 10 == 0:
        print(f'Page {page}...')
    if not offset:
        break

print('Not found')