"""
Модуль для відправки повідомлень у Telegram
"""
import os
import requests
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

        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"

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
📝 Опис: {description[:200] + '...' if len(description) > 200 else description}

🔗 Посилання: {uub_link}
"""

        return message

    def send_tender_notification(self, tender: Dict) -> bool:
        """
        Відправити сповіщення про тендер
        """
        try:
            message = self.format_tender_message(tender)

            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "disable_web_page_preview": True
                },
                timeout=30
            )

            if response.status_code == 200:
                return True
            else:
                error_data = response.json()
                print(f"❌ Помилка відправки в Telegram: {error_data.get('description', response.status_code)}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Помилка з'єднання з Telegram: {e}")
            return False
        except Exception as e:
            print(f"❌ Неочікувана помилка: {e}")
            return False

    def send_test_message(self) -> bool:
        """Відправити тестове повідомлення"""
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": "✅ Тестове повідомлення від Prozorro Tender Monitor"
                },
                timeout=30
            )

            if response.status_code == 200:
                return True
            else:
                error_data = response.json()
                print(f"❌ Помилка: {error_data.get('description', response.status_code)}")
                return False

        except Exception as e:
            print(f"❌ Помилка: {e}")
            return False