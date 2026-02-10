"""
Модуль для відправки повідомлень у Telegram
"""
import os
from telegram import Bot
from telegram.error import TelegramError
from typing import Dict
from dotenv import load_dotenv
import asyncio

# Завантажити змінні середовища
load_dotenv()


class TelegramNotifier:
    """Клас для відправки сповіщень у Telegram"""
    
    def __init__(self):
        """Ініціалізація Telegram бота"""
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.bot_token or not self.chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN та TELEGRAM_CHAT_ID мають бути встановлені в .env файлі")
        
        self.bot = Bot(token=self.bot_token)
    
    def format_tender_message(self, tender: Dict) -> str:
        """
        Форматувати повідомлення про тендер
        """
        title = tender.get('title', 'N/A')
        value = tender.get('value', {})
        amount = value.get('amount', 0)
        currency = value.get('currency', 'UAH')
        
        tender_period = tender.get('tenderPeriod', {})
        end_date = tender_period.get('endDate', 'N/A')
        
        procuring_entity = tender.get('procuringEntity', {})
        customer = procuring_entity.get('name', 'N/A')
        
        description = tender.get('description', 'Опис відсутній')
        
        # Використовуємо tenderID (публічний ID) для посилання
        tender_id = tender.get('tenderID', tender.get('id', ''))
        
        uub_link = f"https://tender.uub.com.ua/tender/{tender_id}/"
        
        message = f"""🔔 Новий тендер на переклад

📋 Назва: {title}
💰 Бюджет: {amount:,.2f} {currency}
📅 Дедлайн подачі: {end_date}
🏢 Замовник: {customer}
📝 Опис: {description[:200]}...

🔗 Посилання: {uub_link}
"""
        
        return message
    
    async def send_tender_notification_async(self, tender: Dict) -> bool:
        """
        Відправити сповіщення про тендер (async)
        """
        try:
            message = self.format_tender_message(tender)
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                disable_web_page_preview=True
            )
            
            return True
            
        except TelegramError as e:
            print(f"❌ Помилка відправки в Telegram: {e}")
            return False
        except Exception as e:
            print(f"❌ Неочікувана помилка: {e}")
            return False
    
    def send_tender_notification(self, tender: Dict) -> bool:
        """
        Відправити сповіщення про тендер (sync wrapper)
        """
        return asyncio.run(self.send_tender_notification_async(tender))
    
    async def send_test_message_async(self) -> bool:
        """
        Відправити тестове повідомлення (async)
        """
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text="✅ Тестове повідомлення від Prozorro Tender Monitor"
            )
            return True
        except Exception as e:
            print(f"❌ Помилка: {e}")
            return False
    
    def send_test_message(self) -> bool:
        """Відправити тестове повідомлення (sync wrapper)"""
        return asyncio.run(self.send_test_message_async())