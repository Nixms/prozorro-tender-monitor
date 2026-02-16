import requests, sys

s = requests.Session()
offset = '2026-02-11T12:00:00Z'
page = 0
while page < 30:
    r = s.get(f'https://api.prozorro.gov.ua/api/2.5/tenders?offset={offset}&limit=100&mode=_all_')
    data = r.json()
    for t in data['data']:
        d = s.get(f'https://api.prozorro.gov.ua/api/2.5/tenders/{t["id"]}').json().get('data', {})
        if d.get('tenderID') == 'UA-2026-02-11-015038-a':
            print(f'FOUND: {t["id"]}')
            print(f'title: {d.get("title")}')
            sys.exit()
    offset = data.get('next_page', {}).get('offset', '')
    page += 1
    print(f'Page {page}...')
    if not offset:
        break