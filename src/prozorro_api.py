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
    
    # Типи конкурентних процедур
    COMPETITIVE_TYPES = [
        'aboveThresholdUA',      # Відкриті торги
        'aboveThresholdEU',      # Відкриті торги ЄС
        'competitiveDialogueUA', # Конкурентний діалог
        'competitiveDialogueEU', # Конкурентний діалог ЄС
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
            
            # Параметри запиту
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
                        
                        # Порівнюємо з date_from
                        if tender_date >= date_from:
                            all_tenders.append(tender)
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
    
    def filter_competitive_tenders(self, tenders: List[Dict]) -> List[Dict]:
        """
        Фільтрувати тільки конкурентні процедури
        
        Args:
            tenders: Список всіх тендерів
            
        Returns:
            Список тільки конкурентних тендерів
        """
        competitive = []
        
        for tender in tenders:
            proc_type = tender.get('procurementMethodType', '')
            if proc_type in self.COMPETITIVE_TYPES:
                competitive.append(tender)
        
        print(f"🎯 Відфільтровано конкурентних процедур: {len(competitive)} з {len(tenders)}")
        return competitive
    
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
    
    def check_tenders_for_translation(self, tenders: List[Dict], max_check: int = 100) -> List[Dict]:
        """
        Перевірити тендери на наявність послуг письмового перекладу
        
        Args:
            tenders: Список тендерів для перевірки
            max_check: Максимальна кількість тендерів для детальної перевірки
            
        Returns:
            Список тендерів на переклад
        """
        translation_tenders = []
        
        # Обмежити кількість для перевірки
        tenders_to_check = tenders[:max_check]
        
        print(f"\n🔍 Перевірка {len(tenders_to_check)} тендерів на наявність послуг перекладу...")
        print(f"   Робимо детальні запити для отримання назв...\n")
        
        for i, tender in enumerate(tenders_to_check, 1):
            tender_id = tender.get('id')
            
            if not tender_id:
                continue
            
            # Отримати деталі тендера (включно з title)
            details = self.get_tender_details(tender_id)
            
            if not details:
                continue
            
            title = details.get('title', '')
            
            # Перевірити чи це тендер на переклад
            if self.is_translation_tender(title):
                # Додати title до основного об'єкта тендера
                tender['title'] = title
                tender['description'] = details.get('description', '')
                tender['value'] = details.get('value', {})
                tender['tenderPeriod'] = details.get('tenderPeriod', {})
                tender['procuringEntity'] = details.get('procuringEntity', {})
                
                translation_tenders.append(tender)
                print(f"  ✅ {i}/{len(tenders_to_check)}: {tender_id} - MATCH!")
                print(f"     {title[:80]}...")
            else:
                # Показуємо прогрес кожні 10 тендерів
                if i % 10 == 0:
                    print(f"  📊 Перевірено: {i}/{len(tenders_to_check)}...")
        
        print(f"\n📊 Знайдено {len(translation_tenders)} тендерів на послуги письмового перекладу")
        return translation_tenders
    
    def search_new_translation_tenders(self, hours: int = 6) -> List[Dict]:
        """
        Пошук нових тендерів на переклад за останні N годин
        
        Args:
            hours: Кількість годин назад (за замовчуванням 6 для 4 запусків на день)
            
        Returns:
            Список нових тендерів на переклад
        """
        print(f"\n{'='*70}")
        print(f"🚀 Початок пошуку нових тендерів на переклад")
        print(f"📅 Період: останні {hours} годин")
        print(f"🎯 Фільтр: конкурентні процедури")
        print(f"🔍 Ключові слова: 'письмов' + 'переклад' або '79530000'")
        print(f"{'='*70}\n")
        
        # Крок 1: Отримати всі тендери за період
        all_tenders = self.get_recent_tenders(hours=hours)
        
        if not all_tenders:
            print("⚠️  Тендери не знайдено")
            return []
        
        # Крок 2: Відфільтрувати тільки конкурентні процедури
        competitive_tenders = self.filter_competitive_tenders(all_tenders)
        
        if not competitive_tenders:
            print("⚠️  Конкурентних тендерів не знайдено")
            return []
        
        # Крок 3: Перевірити перші 100 на наявність послуг перекладу
        translation_tenders = self.check_tenders_for_translation(
            competitive_tenders, 
            max_check=100
        )
        
        print(f"\n{'='*70}")
        print(f"✅ Пошук завершено: знайдено {len(translation_tenders)} тендерів")
        print(f"{'='*70}\n")
        
        return translation_tenders