import sys
sys.path.insert(0, 'src')

from prozorro_api import ProzorroAPI
from telegram_bot import TelegramNotifier
from data_storage import DataStorage

print("="*70)
print("ПОВНИЙ ТЕСТ БОТА З РЕАЛЬНИМ ТЕНДЕРОМ")
print("="*70)

# Ініціалізація
api = ProzorroAPI()
telegram = TelegramNotifier()
storage = DataStorage()

# ID тендера з довгим форматом
test_tender_id = "390e331367a74da7aac848cdb29dc3a1"

print(f"\nОтримання деталей тендера {test_tender_id}...")

# Отримати деталі
details = api.get_tender_details(test_tender_id)

if details:
    # Створити об'єкт тендера
    tender = {
        'id': test_tender_id,
        'title': details.get('title', ''),
        'description': details.get('description', ''),
        'value': details.get('value', {}),
        'tenderPeriod': details.get('tenderPeriod', {}),
        'procuringEntity': details.get('procuringEntity', {}),
        'procurementMethodType': details.get('procurementMethodType', '')
    }
    
    print(f"\n✅ Тендер отримано!")
    print(f"Назва: {tender['title'][:80]}...")
    print(f"Тип: {tender['procurementMethodType']}")
    
    # Перевірити, чи вже оброблений
    processed_ids = storage.load_processed_tenders()
    
    if test_tender_id in processed_ids:
        print(f"\n⚠️  Тендер вже був оброблений раніше")
        print(f"Очищаю storage для тесту...")
        processed_ids.remove(test_tender_id)
        storage.save_processed_tenders(processed_ids)
    
    # Відправити в Telegram
    print(f"\n📤 Відправка в Telegram...")
    success = telegram.send_tender_notification(tender)
    
    if success:
        print(f"✅ Повідомлення успішно відправлено!")
        print(f"📱 Перевірте свій Telegram!")
        
        # Зберегти як оброблений
        processed_ids = storage.load_processed_tenders()
        processed_ids.append(test_tender_id)
        storage.save_processed_tenders(processed_ids)
        print(f"💾 Тендер збережено як оброблений")
    else:
        print(f"❌ Помилка відправки")
else:
    print(f"❌ Не вдалося отримати деталі тендера")

print("\n" + "="*70)