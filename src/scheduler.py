"""
Модуль для планування щоденних перевірок
"""
import asyncio
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import os
from src.prozorro_api import ProzorroAPI
from src.telegram_bot import TelegramNotifier
from src.data_storage import DataStorage


class TenderMonitor:
    """Клас для моніторингу тендерів"""
    
    def __init__(self):
        """Ініціалізація моніторингу"""
        self.api = ProzorroAPI()
        self.notifier = TelegramNotifier()
        self.storage = DataStorage()
    
    async def check_new_tenders(self):
        """Перевірити нові тендери та відправити сповіщення"""
        print(f"\n{'='*70}")
        print(f"Запуск перевірки тендерів: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        try:
            # Отримати нові тендери за останні 24 години
            tenders = self.api.search_new_translation_tenders(hours=24)
            
            if not tenders:
                print("Нових тендерів на переклад не знайдено")
                return
            
            # Відфільтрувати вже оброблені
            new_tenders = []
            for tender in tenders:
                tender_id = tender.get('id')
                if not self.storage.is_processed(tender_id):
                    new_tenders.append(tender)
            
            if not new_tenders:
                print(f"Всі знайдені тендери ({len(tenders)}) вже були оброблені раніше")
                return
            
            print(f"\nНових тендерів для обробки: {len(new_tenders)}")
            print(f"{'='*70}\n")
            
            # Відправити сповіщення про кожен новий тендер
            sent_count = 0
            for tender in new_tenders:
                tender_id = tender.get('id')
                
                # Відправити сповіщення
                success = await self.notifier.send_tender_notification(tender)
                
                if success:
                    # Позначити як оброблений
                    self.storage.mark_as_processed(tender_id)
                    sent_count += 1
                    
                    # Затримка між повідомленнями
                    if sent_count < len(new_tenders):
                        await asyncio.sleep(2)
            
            print(f"\n{'='*70}")
            print(f"Перевірку завершено!")
            print(f"Відправлено сповіщень: {sent_count} з {len(new_tenders)}")
            print(f"Всього оброблено тендерів: {self.storage.get_processed_count()}")
            print(f"{'='*70}\n")
            
        except Exception as e:
            print(f"Помилка під час перевірки тендерів: {e}")
            import traceback
            traceback.print_exc()
    
    def run_check(self):
        """Запустити перевірку (синхронна обгортка для scheduler)"""
        asyncio.run(self.check_new_tenders())
    
    def start_scheduler(self):
        """Запустити планувальник для щоденних перевірок о 09:00"""
        # Отримати часовий пояс з environment variables
        timezone_str = os.getenv('TIMEZONE', 'Europe/Kiev')
        timezone = pytz.timezone(timezone_str)
        
        print(f"\n{'='*70}")
        print(f"Prozorro Tender Monitor запущено!")
        print(f"Перевірки щоденно о 09:00 ({timezone_str})")
        print(f"Моніторинг CPV: 79530000-8 (Письмовий переклад)")
        print(f"{'='*70}\n")
        
        # Створити scheduler
        scheduler = BlockingScheduler(timezone=timezone)
        
        # Запланувати щоденну перевірку о 09:00
        trigger = CronTrigger(hour=9, minute=0, timezone=timezone)
        scheduler.add_job(
            self.run_check,
            trigger=trigger,
            id='daily_tender_check',
            name='Щоденна перевірка тендерів',
            replace_existing=True
        )
        
        # Показати наступний запуск
        next_run = scheduler.get_job('daily_tender_check').next_run_time
        print(f"Наступна перевірка: {next_run.strftime('%d.%m.%Y %H:%M:%S')}\n")
        
        # Запустити першу перевірку одразу (для тестування)
        print("Виконуємо першу перевірку одразу...\n")
        self.run_check()
        
        # Запустити scheduler
        print(f"\n{'='*70}")
        print(f"Scheduler запущено. Очікування наступної перевірки...")
        print(f"{'='*70}\n")
        
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            print("\n\nЗупинка моніторингу...")
            print("До побачення!\n")
    
    async def run_test(self):
        """Запустити тестову перевірку зараз"""
        print(f"\n{'='*70}")
        print(f"ТЕСТОВИЙ РЕЖИМ")
        print(f"{'='*70}\n")
        
        # Відправити тестове повідомлення
        print("Відправка тестового повідомлення...")
        await self.notifier.send_test_message()
        
        # Запустити перевірку тендерів
        print("\nЗапуск перевірки тендерів...\n")
        await self.check_new_tenders()
        
        print(f"\n{'='*70}")
        print(f"ТЕСТ ЗАВЕРШЕНО")
        print(f"{'='*70}\n")