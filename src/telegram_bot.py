"""
Модуль для відправки повідомлень у Telegram
"""
import os
from telegram import Bot
from telegram.error import TelegramError
from typing import Dict
from dotenv import load_dotenv

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
        
        Args:
            tender: Словник з даними тендера
            
        Returns:
            Відформатоване повідомлення
        """
        tender_id = tender.get('id', 'N/A')
        title = tender.get('title', 'Без назви')
        
        # Бюджет
        value = tender.get('value', {})
        amount = value.get('amount', 0)
        currency = value.get('currency', 'UAH')
        budget = f"{amount:,.0f} {currency}".replace(',', ' ')
        
        # Дедлайн
        tender_period = tender.get('tenderPeriod', {})
        deadline = tender_period.get('endDate', 'Не вказано')
        if deadline != 'Не вказано':
            # Конвертувати ISO дату в читабельний формат
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                deadline = dt.strftime('%d.%m.%Y %H:%M')
            except:
                pass
        
        # Замовник
        procuring_entity = tender.get('procuringEntity', {})
        customer = procuring_entity.get('name', 'Не вказано')
        
        # Опис (обмежити до 200 символів)
        description = tender.get('description', 'Опис відсутній')
        if len(description) > 200:
            description = description[:200] + '...'
        
        # Посилання (Варіант Б - два посилання)
        prozorro_url = f"https://prozorro.gov.ua/tender/{tender_id}"
        uub_url = f"https://tender.uub.com.ua/tender/{tender_id}/"
        
        # Форматування повідомлення
        message = f"""🔔 Новий тендер на переклад

📋 Назва: {title}
💰 Бюджет: {budget} (з ПДВ)
📅 Дедлайн подачі: {deadline}
🏢 Замовник: {customer}
📝 Опис: {description}

🔗 Переглянути на Prozorro:
{prozorro_url}

🔗 Ваш майданчик UUB:
{uub_url}
"""
        
        return message
    
    async def send_tender_notification(self, tender: Dict) -> bool:
        """
        Відправити сповіщення про тендер
        
        Args:
            tender: Словник з даними тендера
            
        Returns:
            True якщо відправлено успішно, False якщо помилка
        """
        try:
            message = self.format_tender_message(tender)
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            print(f"✅ Відправлено сповіщення про тендер {tender.get('id')}")
            return True
        except TelegramError as e:
            print(f"❌ Помилка відправки в Telegram: {e}")
            return False
        except Exception as e:
            print(f"❌ Неочікувана помилка: {e}")
            return False
    
    async def send_test_message(self) -> bool:
        """
        Відправити тестове повідомлення
        
        Returns:
            True якщо відправлено успішно
        """
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text="✅ Prozorro Tender Monitor працює!\nТестове повідомлення від бота."
            )
            print("✅ Тестове повідомлення відправлено")
            return True
        except TelegramError as e:
            print(f"❌ Помилка: {e}")
            return False