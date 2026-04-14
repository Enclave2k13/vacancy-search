"""Клиент для работы с API hh.ru с использованием curl_cffi для обхода защиты"""

from curl_cffi import requests
from typing import List, Dict, Any
from src.logger import app_logger


class HHAPIClient:
    """Клиент для взаимодействия с публичным API hh.ru"""

    BASE_URL = "https://api.hh.ru"

    def __init__(self, timeout: int = 10):
        """
        Инициализация клиента

        Args:
            timeout: таймаут запросов в секундах
        """
        self.timeout = timeout
        self.impersonate = "chrome"  # имитируем браузер Chrome
        app_logger.info(f"Инициализирован HHAPIClient с таймаутом {timeout}с")

    def get_company(self, company_id: str) -> Dict[str, Any]:
        """
        Получает информацию о компании по ID

        Args:
            company_id: ID компании на hh.ru

        Returns:
            Словарь с данными о компании
        """
        url = f"{self.BASE_URL}/employers/{company_id}"
        app_logger.debug(f"Запрос компании: {url}")

        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                impersonate=self.impersonate
            )
            response.raise_for_status()
            app_logger.info(f"Компания {company_id} успешно загружена")
            return response.json()
        except Exception as e:
            app_logger.error(f"Ошибка при загрузке компании {company_id}: {e}")
            raise

    def get_vacancies(self, employer_id: str, per_page: int = 100, max_vacancies: int = 10) -> List[Dict[str, Any]]:
        """
        Получает до max_vacancies вакансий компании с указанной зарплатой в рублях
        """
        vacancies = []
        page = 0
        app_logger.info(f"Начало загрузки вакансий для компании {employer_id}, нужно {max_vacancies} шт.")

        while len(vacancies) < max_vacancies:
            params = {
                "employer_id": employer_id,
                "per_page": min(per_page, max_vacancies - len(vacancies)),
                "page": page,
                "only_with_salary": True
            }

            try:
                response = requests.get(
                    f"{self.BASE_URL}/vacancies",
                    params=params,
                    timeout=self.timeout,
                    impersonate=self.impersonate
                )
                response.raise_for_status()
                data = response.json()
                app_logger.debug(f"Страница {page}: получено {len(data.get('items', []))} вакансий")

                for item in data.get("items", []):
                    salary = item.get("salary")
                    # Фильтруем только вакансии с зарплатой в рублях
                    if salary and salary.get("currency") == "RUR":
                        snippet = item.get("snippet", {})
                        full_description = "\n\n".join(filter(None, [
                            snippet.get("responsibility"),
                            snippet.get("requirement")
                        ]))
                        item["full_description"] = full_description or None
                        vacancies.append(item)
                        app_logger.debug(f"Добавлена вакансия {item.get('id')} с зарплатой {salary}")

                        if len(vacancies) >= max_vacancies:
                            break

                if page >= data.get("pages", 1) - 1:
                    app_logger.debug(f"Достигнут последняя страница ({page})")
                    break
                page += 1

            except Exception as e:
                app_logger.error(f"Ошибка при загрузке вакансий для компании {employer_id}: {e}")
                break

        app_logger.info(f"Загружено {len(vacancies)} вакансий для компании {employer_id}")
        return vacancies[:max_vacancies]

    def close(self):
        """Закрывает сессию (для совместимости, т.к. curl_cffi не требует явного закрытия)"""
        app_logger.debug("Закрытие HHAPIClient")
        pass