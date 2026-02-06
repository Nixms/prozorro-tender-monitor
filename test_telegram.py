import os
from telegram import Bot
from dotenv import load_dotenv
import asyncio

load_dotenv()

async def send_test_message():
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    print(f"Bot Token: {bot_token[:10]}...{bot_token[-5:] if bot_token else 'MISSING'}")
    print(f"Chat ID: {chat_id}")

    if bot_token and chat_id:
        try:
            bot = Bot(token=bot_token)
            result = await bot.send_message(
                chat_id=chat_id,
                text="🧪 Тестове повідомлення з бота Prozorro!"
            )
            print(f"\n✅ Повідомлення відправлено!")
            print(f"Message ID: {result.message_id}")
            print(f"\n📱 ПЕРЕВІРТЕ TELEGRAM ЗАРАЗ!")
        except Exception as e:
            print(f"\n❌ Помилка: {e}")
    else:
        print("\n❌ Токен або Chat ID відсутні!")

if __name__ == "__main__":
    asyncio.run(send_test_message())