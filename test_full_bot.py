import os
import requests
from telegram import Bot
from dotenv import load_dotenv
import asyncio

load_dotenv()

async def send_tender():
    test_tender_id = "390e331367a74da7aac848cdb29dc3a1"
    
    print("="*70)
    print("ВІДПРАВКА РЕАЛЬНОГО ТЕНДЕРА В TELEGRAM")
    print("="*70)
    print(f"\nОтримання деталей тендера {test_tender_id}...")
    
    # Отримати деталі
    url = f"https://api.prozorro.gov.ua/api/2.5/tenders/{test_tender_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        details = response.json().get('data', {})
        
        print(f"✅ Тендер отримано!")
        
        # Форматувати повідомлення
        title = details.get('title', 'N/A')
        value = details.get('value', {})
        amount = value.get('amount', 0)
        currency = value.get('currency', 'UAH')
        
        tender_period = details.get('tenderPeriod', {})
        end_date = tender_period.get('endDate', 'N/A')
        
        procuring_entity = details.get('procuringEntity', {})
        customer = procuring_entity.get('name', 'N/A')
        
        description = details.get('description', 'Опис відсутній')
        
        tender_id_short = details.get('tenderID', test_tender_id)
        uub_link = f"https://tender.uub.com.ua/tender/{tender_id_short}/"
        
        message = f"""🔔 Новий тендер на переклад

📋 Назва: {title}
💰 Бюджет: {amount:,.2f} {currency}
📅 Дедлайн подачі: {end_date}
🏢 Замовник: {customer}
📝 Опис: {description[:200]}...

🔗 Посилання: {uub_link}
"""
        
        print(f"\n📤 Відправка в Telegram...")
        
        # Відправити
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        bot = Bot(token=bot_token)
        result = await bot.send_message(
            chat_id=chat_id,
            text=message,
            disable_web_page_preview=True
        )
        
        print(f"✅ Повідомлення відправлено! Message ID: {result.message_id}")
        print(f"📱 Перевірте Telegram!")
    else:
        print(f"❌ Помилка: {response.status_code}")
    
    print("="*70)

if __name__ == "__main__":
    asyncio.run(send_tender())