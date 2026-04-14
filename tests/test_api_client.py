"""Тесты для API клиента"""

import pytest
from unittest.mock import Mock, patch
from src.api_client import HHAPIClient


class TestHHAPIClient:
    """Тесты для HHAPIClient"""

    @pytest.fixture
    def client(self):
        """Фикстура клиента"""
        return HHAPIClient(timeout=5)

    @patch('src.api_client.requests.get')
    def test_get_company_success(self, mock_get, client):
        """Тест успешного получения компании"""
        mock_response = Mock()
        mock_response.json.return_value = {"id": "123", "name": "Test Company"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = client.get_company("123")

        assert result["id"] == "123"
        assert result["name"] == "Test Company"
        mock_get.assert_called_once()

    @patch('src.api_client.requests.get')
    def test_get_company_error(self, mock_get, client):
        """Тест ошибки при получении компании"""
        class ConnectionError(Exception):
            pass

        mock_get.side_effect = ConnectionError("API Error")

        with pytest.raises(ConnectionError):
            client.get_company("123")

    @patch('src.api_client.requests.get')
    def test_get_vacancies_filter_by_rur(self, mock_get, client):
        """Тест фильтрации вакансий по рублям"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [
                {
                    "id": "1",
                    "name": "Vacancy 1",
                    "salary": {"from": 100000, "currency": "RUR"},
                    "snippet": {"responsibility": "", "requirement": ""}
                },
                {
                    "id": "2",
                    "name": "Vacancy 2",
                    "salary": {"from": 100000, "currency": "USD"},
                    "snippet": {"responsibility": "", "requirement": ""}
                }
            ],
            "pages": 1
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        vacancies = client.get_vacancies("123", max_vacancies=10)

        assert len(vacancies) == 1
        assert vacancies[0]["id"] == "1"

    @patch('src.api_client.requests.get')
    def test_get_vacancies_with_description(self, mock_get, client):
        """Тест формирования описания из snippet"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [
                {
                    "id": "1",
                    "name": "Vacancy",
                    "salary": {"from": 100000, "currency": "RUR"},
                    "snippet": {
                        "responsibility": "Develop features",
                        "requirement": "Python knowledge"
                    }
                }
            ],
            "pages": 1
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        vacancies = client.get_vacancies("123", max_vacancies=10)

        assert len(vacancies) == 1
        assert "full_description" in vacancies[0]
        assert "Develop features" in vacancies[0]["full_description"]