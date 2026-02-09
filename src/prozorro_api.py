"""
Модуль для роботи з Prozorro API
Оптимізована версія - фільтрація по назві без зайвих запитів
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
    
    # Типи конкурентних процедур
    COMPETITIVE_TYPES = [
        'aboveThreshold',           # Відкриті торги з особливостями
        'aboveThresholdUA',         # Відкриті торги UA
        'aboveThresholdEU',         # Відкриті торги ЄС
        'aboveThreshold.defense',   # Відкриті торги оборона
        'aboveThresholdUA.defense', # Відкриті торги оборона UA
        'competitiveDialogueUA',    # Конкурентний діалог
        'competitiveDialogueEU',    # Конкурентний діалог ЄС
        'competitiveOrdering',      # Конкурентні замовлення
    ]
    
    def __init__(self):
        """Ініціалізація API клієнта"""
        self.api_url = os.getenv('PROZORRO_API_URL', 'https://api.prozorro.gov.ua/api/2.5/tenders')
        self.cpv_code = os.getenv('CPV_CODE', '79530000-8')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Prozorro Tender Monitor Bot/1.0',
            'Accept': 'application/json'
        })
    
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
    
    def is_competitive_procedure(self, proc_type: str) -> bool:
        """
        Перевірити чи це конкурентна процедура
        
        Args:
            proc_type: Тип процедури закупівлі
            
        Returns:
            True якщо конкурентна процедура
        """
        return proc_type in self.COMPETITIVE_TYPES
    
    def get_recent_tenders_with_filter(self, hours: int = 6) -> List[Dict]:
        """
        ОПТИМІЗОВАНО: Отримати тендери за останні N годин з попередньою фільтрацією
        
        Використовує opt_fields для отримання title та procurementMethodType
        прямо у списку, що дозволяє фільтрувати БЕЗ додаткових API запитів.
        
        Args:
            hours: Кількість годин назад для пошуку
            
        Returns:
            Список тендерів на переклад (попередньо відфільтрованих)
        """
        try:
            # Розрахувати дату початку пошуку (UTC з timezone)
            date_from = datetime.now(timezone.utc) - timedelta(hours=hours)
            date_from_str = date_from.strftime('%Y-%m-%d %H:%M:%S UTC')
            
            print(f"🔍 Пошук тендерів з {date_from_str}...")
            
            # КЛЮЧОВА ОПТИМІЗАЦІЯ: opt_fields дозволяє отримати title та procurementMethodType
            # прямо у списку без додаткових запитів!
            params = {
                'offset': '',
                'limit': 100,
                'mode': '_all_',
                'descending': 1,
                'opt_fields': 'title,procurementMethodType,datePublished'
            }
            
            translation_tenders = []
            total_checked = 0
            competitive_count = 0
            page = 0
            max_pages = 10  # Обмеження кількості сторінок
            stop_pagination = False
            
            while page < max_pages and not stop_pagination:
                response = self.session.get(self.api_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                tenders = data.get('data', [])
                
                if not tenders:
                    break
                
                # Обробка тендерів зі сторінки
                for tender in tenders:
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
                        
                        # Якщо тендер старший за потрібний період - зупиняємо пагінацію
                        if tender_date < date_from:
                            stop_pagination = True
                            break
                        
                        total_checked += 1
                        
                        # ФІЛЬТР 1: Конкурентна процедура?
                        proc_type = tender.get('procurementMethodType', '')
                        if not self.is_competitive_procedure(proc_type):
                            continue
                        
                        competitive_count += 1
                        
                        # ФІЛЬТР 2: Тендер на переклад?
                        title = tender.get('title', '')
                        if not self.is_translation_tender(title):
                            continue
                        
                        # ЗНАЙШЛИ тендер на переклад!
                        translation_tenders.append(tender)
                        print(f"\n  ✅ ЗНАЙДЕНО! {tender.get('id')}")
                        print(f"     Тип: {proc_type}")
                        print(f"     Назва: {title[:80]}...")
                        
                    except Exception as e:
                        continue
                
                # Отримати наступну сторінку
                next_page = data.get('next_page', {})
                offset = next_page.get('offset', '')
                
                if not offset or stop_pagination:
                    break
                
                params['offset'] = offset
                page += 1
                
                # Прогрес кожні 100 тендерів
                if total_checked % 100 == 0:
                    print(f"  📊 Перевірено: {total_checked} тендерів, конкурентних: {competitive_count}, на переклад: {len(translation_tenders)}")
            
            print(f"\n✅ Перевірено {total_checked} тендерів за останні {hours} годин")
            print(f"   Конкурентних процедур: {competitive_count}")
            print(f"   На письмовий переклад: {len(translation_tenders)}")
            
            return translation_tenders
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Помилка запиту до Prozorro API: {e}")
            return []
        except Exception as e:
            print(f"❌ Неочікувана помилка: {e}")
            import traceback
            traceback.print_exc()
            return []
    
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
            print(f"  ⚠️  Помилка отримання деталей {tender_id}: {e}")
            return None
    
    def enrich_tender_details(self, tender: Dict) -> Dict:
        """
        Збагатити тендер детальною інформацією
        
        Args:
            tender: Базова інформація про тендер
            
        Returns:
            Тендер з повною інформацією
        """
        tender_id = tender.get('id')
        if not tender_id:
            return tender
        
        details = self.get_tender_details(tender_id)
        if details:
            tender['title'] = details.get('title', tender.get('title', ''))
            tender['description'] = details.get('description', '')
            tender['value'] = details.get('value', {})
            tender['tenderPeriod'] = details.get('tenderPeriod', {})
            tender['procuringEntity'] = details.get('procuringEntity', {})
            tender['procurementMethodType'] = details.get('procurementMethodType', tender.get('procurementMethodType', ''))
        
        return tender
    
    def search_new_translation_tenders(self, hours: int = 6) -> List[Dict]:
        """
        ОПТИМІЗОВАНО: Пошук нових тендерів на переклад за останні N годин
        
        Новий алгоритм:
        1. Отримуємо тендери з title та procurementMethodType через opt_fields
        2. Фільтруємо по типу та назві БЕЗ додаткових запитів
        3. Робимо детальний запит ТІЛЬКИ для знайдених тендерів на переклад
        
        Це значно швидше: замість 100-1000 запитів робимо лише 1-5!
        
        Args:
            hours: Кількість годин назад (за замовчуванням 6 для 4 запусків на день)
            
        Returns:
            Список нових тендерів на переклад
        """
        print(f"\n{'='*70}")
        print(f"🚀 Початок пошуку нових тендерів на переклад (ОПТИМІЗОВАНО)")
        print(f"📅 Період: останні {hours} годин")
        print(f"🎯 Фільтр 1: конкурентні процедури")
        print(f"🎯 Фільтр 2: 'письмов' + 'переклад' або '79530000'")
        print(f"⚡ Метод: швидка фільтрація через opt_fields")
        print(f"{'='*70}\n")
        
        # Крок 1: Отримати тендери з попередньою фільтрацією
        translation_tenders = self.get_recent_tenders_with_filter(hours=hours)
        
        if not translation_tenders:
            print(f"\n{'='*70}")
            print(f"✅ Пошук завершено: тендерів на переклад не знайдено")
            print(f"{'='*70}\n")
            return []
        
        # Крок 2: Збагатити знайдені тендери детальною інформацією
        print(f"\n📋 Отримуємо деталі для {len(translation_tenders)} тендерів...")
        
        enriched_tenders = []
        for tender in translation_tenders:
            enriched = self.enrich_tender_details(tender)
            enriched_tenders.append(enriched)
        
        print(f"\n{'='*70}")
        print(f"✅ Пошук завершено: знайдено {len(enriched_tenders)} тендерів на переклад")
        print(f"{'='*70}\n")
        
        return enriched_tenders


    # Для зворотної сумісності - старі методи
    def get_recent_tenders(self, hours: int = 24) -> List[Dict]:
        """
        ЗАСТАРІЛО: Використовуйте get_recent_tenders_with_filter()
        Залишено для зворотної сумісності
        """
        return self.get_recent_tenders_with_filter(hours=hours)
    
    def check_tenders_for_translation(self, tenders: List[Dict], max_check: int = 100) -> List[Dict]:
        """
        ЗАСТАРІЛО: Тепер фільтрація відбувається в get_recent_tenders_with_filter()
        Залишено для зворотної сумісності
        """
        # Просто повертаємо вже відфільтровані тендери
        return tenders