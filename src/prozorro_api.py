"""
Модуль для роботи з Prozorro API
"""
import os
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Завантажити змінні середовища
load_dotenv()


class ProzorroAPI:
    """Клас для роботи з Prozorro API"""
    
    def __init__(self):
        """Ініціалізація API клієнта"""
        self.api_url = os.getenv('PROZORRO_API_URL', 'https://api.prozorro.gov.ua/api/2.5/tenders')
        self.cpv_code = os.getenv('CPV_CODE', '79530000-8')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Prozorro Tender Monitor Bot/1.0',
            'Accept': 'application/json'
        })
    
    def get_recent_tenders(self, hours: int = 24) -> List[Dict]:
        """
        Отримати тендери за останні N годин
        
        Args:
            hours: Кількість годин назад для пошуку
            
        Returns:
            Список тендерів
        """
        try:
            # Розрахувати дату початку пошуку (UTC з timezone)
            date_from = datetime.now(timezone.utc) - timedelta(hours=hours)
            date_from_str = date_from.strftime('%Y-%m-%d %H:%M:%S UTC')
            
            print(f"🔍 Пошук тендерів з {date_from_str}...")
            
            # Параметри запиту (без opt_fields - він не працює)
            params = {
                'offset': '',
                'limit': 100,
                'mode': '_all_',
                'descending': 1
            }
            
            all_tenders = []
            page = 0
            max_pages = 10  # Обмеження кількості сторінок
            
            while page < max_pages:
                response = self.session.get(self.api_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                tenders = data.get('data', [])
                
                if not tenders:
                    break
                
                print(f"📄 Сторінка {page + 1}: знайдено {len(tenders)} тендерів")
                
                # Фільтрувати по даті
                for tender in tenders:
                    # Використовуємо datePublished замість dateModified
                    tender_date_str = tender.get('datePublished', tender.get('dateModified', ''))
                    
                    if not tender_date_str:
                        continue
                        
                    try:
                        # Парсимо дату з timezone
                        tender_date_str_clean = tender_date_str.replace('Z', '+00:00')
                        tender_date = datetime.fromisoformat(tender_date_str_clean)
                        
                        # Якщо дата без timezone, додаємо UTC
                        if tender_date.tzinfo is None:
                            tender_date = tender_date.replace(tzinfo=timezone.utc)
                        
                        # Порівнюємо з date_from (обидві дати з timezone)
                        if tender_date >= date_from:
                            all_tenders.append(tender)
                            # Виводимо лише перші та останні 5 тендерів для стислості
                            if len(all_tenders) <= 5 or len(all_tenders) % 100 == 0:
                                print(f"  ✓ Тендер {tender.get('id')}: {tender_date.strftime('%Y-%m-%d %H:%M:%S')}")
                        else:
                            # Якщо дата старіша - продовжуємо (не зупиняємо!)
                            if page < 2:  # Логуємо лише перші сторінки
                                print(f"  ✗ Тендер {tender.get('id')}: {tender_date.strftime('%Y-%m-%d %H:%M:%S')} (старіше {hours}h)")
                    except Exception as e:
                        print(f"  ⚠️  Помилка парсингу дати для {tender.get('id')}: {e}")
                        continue
                
                # Отримати наступну сторінку
                next_page = data.get('next_page', {})
                offset = next_page.get('offset', '')
                
                if not offset:
                    break
                
                params['offset'] = offset
                page += 1
            
            print(f"✅ Всього знайдено {len(all_tenders)} тендерів за останні {hours} годин")
            return all_tenders
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Помилка запиту до Prozorro API: {e}")
            return []
        except Exception as e:
            print(f"❌ Неочікувана помилка: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def is_translation_tender(self, title: str) -> bool:
        """
        Перевірити чи тендер на послуги письмового перекладу за назвою
        
        Args:
            title: Назва тендера
            
        Returns:
            True якщо це тендер на переклад
        """
        if not title:
            return False
        
        title_lower = title.lower()
        
        # Варіант 1: "письмовий переклад" (обидва слова разом)
        if 'письмов' in title_lower and 'переклад' in title_lower:
            return True
        
        # Варіант 2: CPV код у назві
        if '79530000' in title_lower:
            return True
        
        return False
    
    def filter_translation_tenders(self, tenders: List[Dict]) -> List[Dict]:
        """
        Фільтрувати тендери по назві (пошук ключових слів)
        
        Args:
            tenders: Список всіх тендерів
            
        Returns:
            Список тендерів на переклад
        """
        translation_tenders = []
        
        print(f"\n🔍 Перевірка {len(tenders)} тендерів по назві...")
        print(f"   Шукаємо: 'письмов' + 'переклад' або '79530000'\n")
        
        # Перевіряємо перші 20 тендерів детально
        check_limit = min(20, len(tenders))
        
        for i, tender in enumerate(tenders):
            tender_id = tender.get('id', 'unknown')
            title = tender.get('title', '')
            
            if not title:
                if i < check_limit:
                    print(f"  ⚠️  {tender_id}: немає назви")
                continue
            
            # Перевірити по назві
            if self.is_translation_tender(title):
                translation_tenders.append(tender)
                print(f"  ✅ {tender_id}: MATCH!")
                print(f"     {title[:100]}...")
            else:
                # Логуємо перші 20 тендерів детально
                if i < check_limit:
                    print(f"  ❌ {tender_id}: {title[:80]}...")
        
        if len(tenders) > check_limit:
            remaining = len(tenders) - check_limit
            remaining_found = len([t for t in tenders[check_limit:] if self.is_translation_tender(t.get('title', ''))])
            if remaining_found > 0:
                print(f"\n  ... перевірено ще {remaining} тендерів (знайдено {remaining_found})")
            else:
                print(f"\n  ... перевірено ще {remaining} тендерів (логування скорочено)")
        
        print(f"\n📊 Знайдено {len(translation_tenders)} тендерів на послуги письмового перекладу")
        return translation_tenders
    
    def get_tender_details(self, tender_id: str) -> Optional[Dict]:
        """
        Отримати детальну інформацію про тендер
        
        Args:
            tender_id: ID тендера
            
        Returns:
            Детальна інформація про тендер або None
        """
        try:
            url = f"{self.api_url}/{tender_id}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get('data')
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Помилка отримання деталей тендера {tender_id}: {e}")
            return None
    
    def search_new_translation_tenders(self, hours: int = 24) -> List[Dict]:
        """
        Пошук нових тендерів на переклад за останні N годин
        
        Args:
            hours: Кількість годин назад
            
        Returns:
            Список нових тендерів на переклад
        """
        print(f"\n{'='*60}")
        print(f"🚀 Початок пошуку нових тендерів на переклад")
        print(f"📅 Період: останні {hours} годин")
        print(f"🔍 Метод пошуку: по ключовим словам у назві")
        print(f"🏷️  Ключові слова: 'письмов' + 'переклад' або '79530000'")
        print(f"{'='*60}\n")
        
        # Отримати всі тендери
        all_tenders = self.get_recent_tenders(hours=hours)
        
        if not all_tenders:
            print("⚠️  Тендери не знайдено")
            return []
        
        # Фільтрувати по назві
        translation_tenders = self.filter_translation_tenders(all_tenders)
        
        print(f"\n{'='*60}")
        print(f"✅ Пошук завершено: знайдено {len(translation_tenders)} тендерів")
        print(f"{'='*60}\n")
        
        return translation_tenders