"""
Модуль для роботи з локальним сховищем оброблених тендерів
З підтримкою збереження при перезапуску Railway
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict


class DataStorage:
    """Клас для збереження та завантаження оброблених тендерів"""
    
    def __init__(self, filepath: str = "data/processed_tenders.json"):
        """Ініціалізація сховища"""
        self.filepath = filepath
        self._ensure_file_exists()
        self._restore_from_env_if_needed()
    
    def _ensure_file_exists(self):
        """Створити файл якщо він не існує"""
        if not os.path.exists(self.filepath):
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            self._save_data({
                "processed_tenders": {},
                "last_check": None
            })
    
    def _restore_from_env_if_needed(self):
        """
        Відновити дані з PROCESSED_TENDERS_BACKUP якщо локальний файл порожній
        """
        backup = os.getenv('PROCESSED_TENDERS_BACKUP', '')
        
        if not backup:
            return
        
        data = self._load_data()
        
        if len(data.get("processed_tenders", {})) == 0:
            try:
                backup_data = json.loads(backup)
                if backup_data.get("processed_tenders"):
                    print(f"🔄 Відновлено {len(backup_data['processed_tenders'])} тендерів з backup")
                    self._save_data(backup_data)
            except json.JSONDecodeError:
                print("⚠️  Помилка парсингу PROCESSED_TENDERS_BACKUP")
    
    def _load_data(self) -> Dict:
        """Завантажити дані з файлу"""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"processed_tenders": {}, "last_check": None}
    
    def _save_data(self, data: Dict):
        """Зберегти дані у файл"""
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def is_processed(self, tender_id: str) -> bool:
        """Перевірити чи тендер вже оброблено"""
        data = self._load_data()
        processed = data["processed_tenders"]
        
        if isinstance(processed, list):
            return tender_id in processed
        return tender_id in processed
    
    def mark_as_processed(self, tender_id: str):
        """Позначити тендер як оброблений"""
        data = self._load_data()
        processed = data["processed_tenders"]
        
        if isinstance(processed, list):
            processed = {tid: datetime.now().isoformat() for tid in processed}
            data["processed_tenders"] = processed
        
        if tender_id not in processed:
            processed[tender_id] = datetime.now().isoformat()
            data["last_check"] = datetime.now().isoformat()
            self._save_data(data)
            self._print_backup_instruction(data)
    
    def _print_backup_instruction(self, data: Dict):
        """Вивести JSON для збереження в Railway Variables"""
        count = len(data.get("processed_tenders", {}))
        if count > 0 and count % 5 == 0:
            print(f"\n💾 Backup ({count} тендерів). Оновіть PROCESSED_TENDERS_BACKUP в Railway:")
            compact = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
            if len(compact) < 2000:
                print(f"   {compact[:500]}...")
    
    def get_processed_count(self) -> int:
        """Отримати кількість оброблених тендерів"""
        data = self._load_data()
        processed = data["processed_tenders"]
        
        if isinstance(processed, list):
            return len(processed)
        return len(processed)
    
    def get_processed_ids(self) -> List[str]:
        """Отримати список ID оброблених тендерів"""
        data = self._load_data()
        processed = data["processed_tenders"]
        
        if isinstance(processed, list):
            return processed
        return list(processed.keys())
    
    def get_last_check(self) -> str:
        """Отримати час останньої перевірки"""
        data = self._load_data()
        return data.get("last_check", "Ніколи")
    
    def get_backup_json(self) -> str:
        """Отримати JSON для збереження в PROCESSED_TENDERS_BACKUP"""
        data = self._load_data()
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    
    def cleanup_old_tenders(self, days: int = 90):
        """Видалити тендери старші за N днів"""
        data = self._load_data()
        processed = data["processed_tenders"]
        
        if isinstance(processed, list):
            print(f"⚠️  Старий формат даних, очищення неможливе")
            return
        
        cutoff_date = datetime.now() - timedelta(days=days)
        old_count = len(processed)
        processed_clean = {}
        
        for tender_id, date_str in processed.items():
            try:
                tender_date = datetime.fromisoformat(date_str)
                if tender_date > cutoff_date:
                    processed_clean[tender_id] = date_str
            except (ValueError, TypeError):
                processed_clean[tender_id] = date_str
        
        data["processed_tenders"] = processed_clean
        self._save_data(data)
        
        removed = old_count - len(processed_clean)
        if removed > 0:
            print(f"🧹 Видалено {removed} старих записів (старші {days} днів)")