"""
Тести для модуля data_storage
"""
import pytest
import os
import json
import tempfile
from datetime import datetime, timedelta
from src.data_storage import DataStorage


class TestDataStorage:
    """Тести для DataStorage"""
    
    def setup_method(self):
        """Створити тимчасовий файл перед кожним тестом"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = os.path.join(self.temp_dir, "test_tenders.json")
        self.storage = DataStorage(filepath=self.temp_file)
    
    def teardown_method(self):
        """Видалити тимчасовий файл після тесту"""
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_new_tender_not_processed(self):
        """Новий тендер не повинен бути в оброблених"""
        assert self.storage.is_processed("UA-2026-01-01-000001-a") == False
    
    def test_mark_as_processed(self):
        """Після mark_as_processed тендер має бути в оброблених"""
        tender_id = "UA-2026-01-01-000001-a"
        
        self.storage.mark_as_processed(tender_id)
        
        assert self.storage.is_processed(tender_id) == True
    
    def test_count_processed(self):
        """Перевірка підрахунку оброблених тендерів"""
        assert self.storage.get_processed_count() == 0
        
        self.storage.mark_as_processed("tender-1")
        self.storage.mark_as_processed("tender-2")
        self.storage.mark_as_processed("tender-3")
        
        assert self.storage.get_processed_count() == 3
    
    def test_no_duplicates(self):
        """Один тендер не додається двічі"""
        tender_id = "UA-2026-01-01-000001-a"
        
        self.storage.mark_as_processed(tender_id)
        self.storage.mark_as_processed(tender_id)
        self.storage.mark_as_processed(tender_id)
        
        assert self.storage.get_processed_count() == 1
    
    def test_cleanup_old_tenders(self):
        """Очищення видаляє старі записи"""
        old_date = (datetime.now() - timedelta(days=100)).isoformat()
        new_date = datetime.now().isoformat()
        
        data = {
            "processed_tenders": {
                "old-tender": old_date,
                "new-tender": new_date
            },
            "last_check": new_date
        }
        
        with open(self.temp_file, 'w') as f:
            json.dump(data, f)
        
        self.storage.cleanup_old_tenders(days=90)
        
        assert self.storage.is_processed("old-tender") == False
        assert self.storage.is_processed("new-tender") == True