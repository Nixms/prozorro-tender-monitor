"""
Тести для модуля prozorro_api
"""
import pytest
from src.prozorro_api import ProzorroAPI


class TestIsTranslationTender:
    """Тести для методу is_translation_tender"""
    
    def setup_method(self):
        """Створити екземпляр API перед кожним тестом"""
        self.api = ProzorroAPI()
    
    def test_finds_translation_with_both_words(self):
        """Знаходить тендер коли є 'письмов' і 'переклад'"""
        assert self.api.is_translation_tender("Послуги письмового перекладу") == True
        assert self.api.is_translation_tender("Письмовий переклад документів") == True
        assert self.api.is_translation_tender("ПИСЬМОВИЙ ПЕРЕКЛАД") == True
    
    def test_finds_translation_with_cpv_code(self):
        """Знаходить тендер коли є CPV код 79530000"""
        assert self.api.is_translation_tender("Послуги за кодом 79530000-8") == True
        assert self.api.is_translation_tender("CPV 79530000") == True
    
    def test_rejects_unrelated_tenders(self):
        """Відхиляє тендери без перекладу"""
        assert self.api.is_translation_tender("Будівельні роботи") == False
        assert self.api.is_translation_tender("Медичні послуги") == False
        assert self.api.is_translation_tender("Харчування") == False
    
    def test_rejects_partial_match(self):
        """Відхиляє якщо тільки одне слово"""
        assert self.api.is_translation_tender("Письмові роботи") == False
        assert self.api.is_translation_tender("Усний переклад") == False
    
    def test_handles_empty_and_none(self):
        """Коректно обробляє пусті значення"""
        assert self.api.is_translation_tender("") == False
        assert self.api.is_translation_tender(None) == False


class TestIsCompetitiveProcedure:
    """Тести для методу is_competitive_procedure"""
    
    def setup_method(self):
        self.api = ProzorroAPI()
    
    def test_accepts_competitive_types(self):
        """Приймає конкурентні типи процедур"""
        assert self.api.is_competitive_procedure("aboveThreshold") == True
        assert self.api.is_competitive_procedure("aboveThresholdUA") == True
        assert self.api.is_competitive_procedure("aboveThresholdEU") == True
    
    def test_rejects_non_competitive_types(self):
        """Відхиляє неконкурентні типи"""
        assert self.api.is_competitive_procedure("reporting") == False
        assert self.api.is_competitive_procedure("negotiation") == False
        assert self.api.is_competitive_procedure("") == False