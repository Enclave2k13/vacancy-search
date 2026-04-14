"""Тесты для конфигурации"""

from src.config import get_companies_with_names, COMPANY_IDS


class TestConfig:
    def test_get_companies_with_names(self):
        companies = get_companies_with_names()
        assert len(companies) == 12
        assert companies[0] == ("1740", "Яндекс")

    def test_company_ids(self):
        assert len(COMPANY_IDS) == 12
        assert "1740" in COMPANY_IDS
        assert "3529" in COMPANY_IDS