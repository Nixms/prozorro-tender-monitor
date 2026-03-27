"""
Модуль для планування щоденних перевірок
"""
import time
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
    
    def check_new_tenders(self):
        """Перевірити нові тендери та відправити сповіщення"""
        print(f"\n{'='*70}")
        print(f"Запуск перевірки тендерів: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        try:
            # Отримати нові тендери за останні 2 години (з запасом для щогодинних перевірок)
            tenders = self.api.search_new_translation_tenders(hours=2)
            
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
                success = self.notifier.send_tender_notification(tender)
                
                if success:
                    # Позначити як оброблений
                    self.storage.mark_as_processed(tender_id)
                    sent_count += 1
                    
                    # Затримка між повідомленнями
                    if sent_count < len(new_tenders):
                        time.sleep(2)
            
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
        # Очищення старих записів (старші 90 днів)
        self.storage.cleanup_old_tenders(days=90)
        self.check_new_tenders()
    
    def start_scheduler(self):
        """Запустити планувальник для щогодинних перевірок"""
        # Отримати часовий пояс з environment variables
        timezone_str = os.getenv('TIMEZONE', 'Europe/Kiev')
        local_tz = pytz.timezone(timezone_str)

        print(f"\n{'='*70}")
        print(f"Prozorro Tender Monitor запущено!")
        print(f"Перевірки кожну годину ({timezone_str})")
        print(f"Моніторинг: конкурентні процедури на письмовий переклад")
        print(f"{'='*70}\n")

        # Створити scheduler
        scheduler = BlockingScheduler(timezone=local_tz)

        # Перевірка кожну годину (о :00 кожної години)
        trigger = CronTrigger(
            minute=0,  # Кожну годину о :00
            timezone=local_tz
        )
        scheduler.add_job(
            self.run_check,
            trigger=trigger,
            id='tender_check_hourly',
            name='Щогодинна перевірка тендерів',
            replace_existing=True
        )
        
        print(f"✅ Заплановано перевірки кожну годину")
        print(f"   🕐 Наступна перевірка о :00\n")
        
        # Запустити першу перевірку одразу (для тестування)
        print("Виконуємо першу перевірку одразу...\n")
        self.run_check()
        
        # Запустити scheduler
        print(f"\n{'='*70}")
        print(f"Scheduler запущено. Очікування наступних перевірок...")
        print(f"{'='*70}\n")
        
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            print("\n\nЗупинка моніторингу...")
            print("До побачення!\n")
    
    def run_test(self):
        """Запустити тестову перевірку зараз"""
        print(f"\n{'='*70}")
        print(f"ТЕСТОВИЙ РЕЖИМ")
        print(f"{'='*70}\n")
        
        # Відправити тестове повідомлення
        print("Відправка тестового повідомлення...")
        self.notifier.send_test_message()
        
        # Запустити перевірку тендерів
        print("\nЗапуск перевірки тендерів...\n")
        self.check_new_tenders()
        
        print(f"\n{'='*70}")
        print(f"ТЕСТ ЗАВЕРШЕНО")
        print(f"{'='*70}\n")