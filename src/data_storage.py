"""
Модуль для роботи з локальним сховищем оброблених тендерів
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict


class DataStorage:
    """Клас для збереження та завантаження оброблених тендерів"""
    
    def __init__(self, filepath: str = "data/processed_tenders.json"):
        """
        Ініціалізація сховища
        
        Args:
            filepath: Шлях до JSON файлу з даними
        """
        self.filepath = filepath
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Створити файл якщо він не існує"""
        if not os.path.exists(self.filepath):
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            self._save_data({
                "processed_tenders": {},
                "last_check": None
            })
    
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
        """
        Перевірити чи тендер вже оброблено
        
        Args:
            tender_id: ID тендера
            
        Returns:
            True якщо тендер вже оброблено, False якщо ні
        """
        data = self._load_data()
        processed = data["processed_tenders"]
        
        # Підтримка старого формату (список) і нового (словник)
        if isinstance(processed, list):
            return tender_id in processed
        return tender_id in processed
    
    def mark_as_processed(self, tender_id: str):
        """
        Позначити тендер як оброблений
        
        Args:
            tender_id: ID тендера
        """
        data = self._load_data()
        processed = data["processed_tenders"]
        
        # Підтримка старого формату (список) і нового (словник)
        if isinstance(processed, list):
            # Конвертуємо старий формат у новий
            processed = {tid: datetime.now().isoformat() for tid in processed}
            data["processed_tenders"] = processed
        
        if tender_id not in processed:
            processed[tender_id] = datetime.now().isoformat()
            data["last_check"] = datetime.now().isoformat()
            self._save_data(data)
    
    def get_processed_count(self) -> int:
        """Отримати кількість оброблених тендерів"""
        data = self._load_data()
        processed = data["processed_tenders"]
        
        if isinstance(processed, list):
            return len(processed)
        return len(processed)
    
    def get_last_check(self) -> str:
        """Отримати час останньої перевірки"""
        data = self._load_data()
        return data.get("last_check", "Ніколи")
    
    def cleanup_old_tenders(self, days: int = 90):
        """
        Видалити тендери старші за N днів
        
        Args:
            days: Кількість днів (за замовчуванням 90)
        """
        data = self._load_data()
        processed = data["processed_tenders"]
        
        # Якщо старий формат (список) - не можемо очистити по даті
        if isinstance(processed, list):
            print(f"⚠️  Старий формат даних, очищення неможливе")
            return
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Фільтруємо тільки свіжі записи
        old_count = len(processed)
        processed_clean = {}
        
        for tender_id, date_str in processed.items():
            try:
                tender_date = datetime.fromisoformat(date_str)
                if tender_date > cutoff_date:
                    processed_clean[tender_id] = date_str
            except:
                # Якщо дата невалідна - залишаємо
                processed_clean[tender_id] = date_str
        
        data["processed_tenders"] = processed_clean
        self._save_data(data)
        
        removed = old_count - len(processed_clean)
        if removed > 0:
            print(f"🧹 Видалено {removed} старих записів (старші {days} днів)")