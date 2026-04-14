"""Тесты для DBManager"""

from src.db_manager import DBManager


class TestDBManager:
    """Тесты для DBManager"""

    def test_get_companies_and_vacancies_count(self, test_database, sample_companies_data, sample_vacancies_data):
        """Тест получения компаний с количеством вакансий"""
        manager = DBManager(test_database)
        result = manager.get_companies_and_vacancies_count()

        assert len(result) == 2
        companies_dict = dict(result)
        assert companies_dict['Company A'] == 2
        assert companies_dict['Company B'] == 2

    def test_get_avg_salary(self, test_database, sample_companies_data, sample_vacancies_data):
        """Тест получения средней зарплаты"""
        manager = DBManager(test_database)
        avg = manager.get_avg_salary()

        assert avg == 131250.0