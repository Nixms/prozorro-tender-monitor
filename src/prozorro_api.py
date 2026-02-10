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
        """
        if not title:
            return False
        
        title_lower = title.lower()
        
        if 'письмов' in title_lower and 'переклад' in title_lower:
            return True
        
        if '79530000' in title_lower:
            return True
        
        return False
    
    def is_competitive_procedure(self, proc_type: str) -> bool:
        """
        Перевірити чи це конкурентна процедура
        """
        return proc_type in self.COMPETITIVE_TYPES
    
    def get_tender_details(self, tender_id: str) -> Optional[Dict]:
        """
        Отримати детальну інформацію про тендер
        """
        try:
            url = f"{self.api_url}/{tender_id}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get('data')
            
        except requests.exceptions.RequestException as e:
            return None
    
    def get_recent_tenders(self, hours: int = 6) -> List[Dict]:
        """
        Отримати список тендерів за останні N годин
        """
        try:
            date_from = datetime.now(timezone.utc) - timedelta(hours=hours)
            date_from_str = date_from.strftime('%Y-%m-%d %H:%M:%S UTC')
            
            print(f"🔍 Пошук тендерів з {date_from_str}...")
            
            params = {
                'offset': '',
                'limit': 100,
                'mode': '_all_',
                'descending': 1
            }
            
            all_tenders = []
            page = 0
            max_pages = 20
            stop_pagination = False
            
            while page < max_pages and not stop_pagination:
                response = self.session.get(self.api_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                tenders = data.get('data', [])
                
                if not tenders:
                    break
                
                for tender in tenders:
                    tender_date_str = tender.get('dateModified', '')
                    
                    if not tender_date_str:
                        continue
                        
                    try:
                        tender_date_str_clean = tender_date_str.replace('Z', '+00:00')
                        tender_date = datetime.fromisoformat(tender_date_str_clean)
                        
                        if tender_date.tzinfo is None:
                            tender_date = tender_date.replace(tzinfo=timezone.utc)
                        
                        if tender_date < date_from:
                            stop_pagination = True
                            break
                        
                        all_tenders.append(tender)
                    except Exception:
                        continue
                
                next_page = data.get('next_page', {})
                offset = next_page.get('offset', '')
                
                if not offset or stop_pagination:
                    break
                
                params['offset'] = offset
                page += 1
            
            print(f"✅ Знайдено {len(all_tenders)} тендерів за останні {hours} годин")
            return all_tenders
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Помилка запиту до Prozorro API: {e}")
            return []
        except Exception as e:
            print(f"❌ Неочікувана помилка: {e}")
            return []
    
    def search_new_translation_tenders(self, hours: int = 6) -> List[Dict]:
        """
        Пошук нових тендерів на переклад за останні N годин
        """
        print(f"\n{'='*70}")
        print(f"🚀 Початок пошуку нових тендерів на переклад")
        print(f"📅 Період: останні {hours} годин")
        print(f"🎯 Фільтр: конкурентні процедури + письмовий переклад")
        print(f"{'='*70}\n")
        
        # Крок 1: Отримати всі тендери за період
        all_tenders = self.get_recent_tenders(hours=hours)
        
        if not all_tenders:
            print("⚠️  Тендери не знайдено")
            return []
        
        # Крок 2: Перевірити КОЖЕН тендер (робимо детальний запит)
        print(f"\n🔍 Перевірка {len(all_tenders)} тендерів...")
        
        translation_tenders = []
        competitive_count = 0
        
        for i, tender in enumerate(all_tenders, 1):
            tender_id = tender.get('id')
            
            if not tender_id:
                continue
            
            if i % 50 == 0:
                print(f"  📊 Перевірено: {i}/{len(all_tenders)}, конкурентних: {competitive_count}, на переклад: {len(translation_tenders)}")
            
            # Отримати деталі
            details = self.get_tender_details(tender_id)
            
            if not details:
                continue
            
            # Фільтр 1: Конкурентна процедура?
            proc_type = details.get('procurementMethodType', '')
            if not self.is_competitive_procedure(proc_type):
                continue
            
            competitive_count += 1
            
            # Фільтр 2: Тендер на переклад?
            title = details.get('title', '')
            if not self.is_translation_tender(title):
                continue
            
            # Знайшли!
            details['id'] = tender_id
            translation_tenders.append(details)
            
            print(f"\n  ✅ ЗНАЙДЕНО! {details.get('tenderID', tender_id)}")
            print(f"     Назва: {title[:70]}...")
        
        print(f"\n📊 Результати:")
        print(f"   Всього перевірено: {len(all_tenders)}")
        print(f"   Конкурентних процедур: {competitive_count}")
        print(f"   На письмовий переклад: {len(translation_tenders)}")
        
        print(f"\n{'='*70}")
        print(f"✅ Пошук завершено: знайдено {len(translation_tenders)} тендерів")
        print(f"{'='*70}\n")
        
        return translation_tenders