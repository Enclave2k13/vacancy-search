"""Тесты для вспомогательных функций"""

from src.utils import (
    clean_html,
    parse_salary,
    parse_description,
    format_salary,
    validate_vacancy_data
)


class TestCleanHtml:
    def test_clean_simple_html(self):
        assert clean_html("<p>Text</p>") == "Text"

    def test_clean_empty(self):
        assert clean_html("") == ""
        assert clean_html(None) == ""

    def test_clean_html_entities(self):
        assert clean_html("Hello &amp; World") == "Hello World"


class TestParseSalary:
    def test_full_salary(self):
        result = parse_salary({"from": 100000, "to": 150000, "currency": "RUR"})
        assert result == (100000, 150000, "RUR")

    def test_no_salary(self):
        result = parse_salary(None)
        assert result == (None, None, None)


class TestParseDescription:
    def test_from_full_description(self):
        vacancy = {"full_description": "<p>Test</p>"}
        result = parse_description(vacancy)
        assert result == "Test"

    def test_from_snippet(self):
        vacancy = {
            "snippet": {
                "responsibility": "<p>Dev</p>",
                "requirement": "<p>Python</p>"
            }
        }
        result = parse_description(vacancy)
        assert "Dev" in result
        assert "Python" in result


class TestFormatSalaryDisplay:
    def test_full_salary(self):
        result = format_salary(100000, 150000)
        assert "100 000" in result
        assert "150 000" in result

    def test_no_salary(self):
        result = format_salary(None, None)
        assert "не указана" in result


class TestValidateVacancyData:
    def test_valid(self):
        vacancy = {"id": "1", "name": "Test"}
        assert validate_vacancy_data(vacancy) is True

    def test_invalid_no_id(self):
        vacancy = {"name": "Test"}
        assert validate_vacancy_data(vacancy) is False