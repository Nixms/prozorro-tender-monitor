"""
Модуль для роботи з локальним сховищем оброблених тендерів
"""
import json
import os
from datetime import datetime
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
                "processed_tenders": [],
                "last_check": None
            })
    
    def _load_data(self) -> Dict:
        """Завантажити дані з файлу"""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"processed_tenders": [], "last_check": None}
    
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
        return tender_id in data["processed_tenders"]
    
    def mark_as_processed(self, tender_id: str):
        """
        Позначити тендер як оброблений
        
        Args:
            tender_id: ID тендера
        """
        data = self._load_data()
        if tender_id not in data["processed_tenders"]:
            data["processed_tenders"].append(tender_id)
            data["last_check"] = datetime.now().isoformat()
            self._save_data(data)
    
    def get_processed_count(self) -> int:
        """Отримати кількість оброблених тендерів"""
        data = self._load_data()
        return len(data["processed_tenders"])
    
    def get_last_check(self) -> str:
        """Отримати час останньої перевірки"""
        data = self._load_data()
        return data.get("last_check", "Ніколи")