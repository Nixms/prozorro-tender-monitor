"""
Prozorro Tender Monitor - Головний файл
Моніторинг тендерів на послуги письмового перекладу
"""
import sys
import asyncio
from src.scheduler import TenderMonitor


def print_help():
    """Показати довідку по використанню"""
    print("""
===================================================================
         PROZORRO TENDER MONITOR - Моніторинг тендерів
===================================================================

РЕЖИМИ РОБОТИ:

1. python main.py                - Запустити моніторинг (щоденні перевірки о 09:00)
2. python main.py test            - Тестовий режим (перевірити зараз)
3. python main.py help            - Показати цю довідку

-------------------------------------------------------------------

ЩО РОБИТЬ БОТ:
   • Щоденно о 09:00 перевіряє нові тендери в Prozorro
   • Фільтрує по CPV коду 79530000-8 (Письмовий переклад)
   • Відправляє сповіщення в Telegram про нові тендери
   • Не надсилає дублікати

ІНФОРМАЦІЯ:
   • CPV код: 79530000-8
   • API: https://api.prozorro.gov.ua
   • Частота: 1 раз на добу (09:00)

НАЛАШТУВАННЯ:
   • Токени в файлі .env
   • Логи виводяться в консоль

-------------------------------------------------------------------
    """)


def main():
    """Головна функція"""
    # Перевірити аргументи командного рядка
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'help':
            print_help()
            return
        
        elif command == 'test':
            # Тестовий режим
            monitor = TenderMonitor()
            asyncio.run(monitor.run_test())
            return
        
        else:
            print(f"Невідома команда: {command}")
            print("Використовуйте: python main.py help")
            return
    
    # Звичайний режим - запуск планувальника
    try:
        monitor = TenderMonitor()
        monitor.start_scheduler()
    except KeyboardInterrupt:
        print("\n\nЗупинка програми...")
        print("До побачення!\n")
    except Exception as e:
        print(f"\nКритична помилка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()