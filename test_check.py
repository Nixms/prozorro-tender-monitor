from src.prozorro_api import ProzorroAPI

api = ProzorroAPI()

# Перевіримо конкретний тендер
details = api.get_tender_details('UA-2026-02-09-003989-a')
if details:
    print('Тендер знайдено!')
    print(f'Назва: {details.get("title")}')
    print(f'Тип: {details.get("procurementMethodType")}')
    print(f'Конкурентний: {api.is_competitive_procedure(details.get("procurementMethodType", ""))}')
    print(f'На переклад: {api.is_translation_tender(details.get("title", ""))}')
else:
    print('Тендер НЕ знайдено')