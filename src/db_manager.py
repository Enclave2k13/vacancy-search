"""Класс для работы с данными в БД (бизнес-запросы)"""

from typing import List, Tuple, Optional
from src.database import Database


class DBManager:
    """Класс для выполнения аналитических запросов к БД"""

    def __init__(self, db: Database):
        """
        Инициализация DBManager

        Args:
            db: экземпляр класса Database для работы с БД
        """
        self.db = db

    def get_companies_and_vacancies_count(self) -> List[Tuple[str, int]]:
        """
        Получает список всех компаний и количество вакансий у каждой компании

        Returns:
            Список кортежей (название_компании, количество_вакансий)
        """
        query = """
            SELECT c.company_name, COUNT(v.vacancy_id) as vacancy_count
            FROM companies c
            LEFT JOIN vacancies v ON c.company_id = v.company_id
            GROUP BY c.company_id, c.company_name
            ORDER BY vacancy_count DESC, c.company_name
        """
        self.db.cur.execute(query)
        return self.db.cur.fetchall()

    def get_all_vacancies(self) -> List[Tuple[str, str, Optional[int], Optional[int], str]]:
        """
        Получает список всех вакансий с указанием названия компании,
        названия вакансии, зарплаты и ссылки на вакансию

        Returns:
            Список кортежей (название_компании, название_вакансии,
                           зарплата_от, зарплата_до, ссылка)
        """
        query = """
            SELECT c.company_name, v.vacancy_name,
                   v.salary_from, v.salary_to, v.url
            FROM vacancies v
            JOIN companies c ON v.company_id = c.company_id
            ORDER BY c.company_name, v.vacancy_name
        """
        self.db.cur.execute(query)
        return self.db.cur.fetchall()

    def get_avg_salary(self) -> float:
        """Получает среднюю зарплату по вакансиям в рублях"""
        query = """
            SELECT AVG(vacancy_avg_salary) as avg_salary
            FROM (
                SELECT 
                    CASE 
                        WHEN salary_from IS NOT NULL AND salary_to IS NOT NULL 
                            THEN (salary_from + salary_to) / 2.0
                        WHEN salary_from IS NOT NULL AND salary_to IS NULL 
                            THEN salary_from
                        WHEN salary_from IS NULL AND salary_to IS NOT NULL 
                            THEN salary_to
                        ELSE NULL
                    END as vacancy_avg_salary
                FROM vacancies
                WHERE salary_currency = 'RUR'
                  AND (salary_from IS NOT NULL OR salary_to IS NOT NULL)
            ) as salary_data
            WHERE vacancy_avg_salary IS NOT NULL
        """
        self.db.cur.execute(query)
        result = self.db.cur.fetchone()[0]
        return float(result) if result else 0.0

    def get_avg_salary_by_company(self, company_id: int) -> dict:
        """
        Получает среднюю зарплату по вакансиям компании по ID компании

        Args:
            company_id: ID компании

        Returns:
            Словарь с информацией о компании и средней зарплате
        """
        query = """
            SELECT 
                c.company_id,
                c.company_name,
                COUNT(v.vacancy_id) as vacancy_count,
                AVG(
                    CASE 
                        WHEN v.salary_from IS NOT NULL AND v.salary_to IS NOT NULL 
                            THEN (v.salary_from + v.salary_to) / 2.0
                        WHEN v.salary_from IS NOT NULL AND v.salary_to IS NULL 
                            THEN v.salary_from
                        WHEN v.salary_from IS NULL AND v.salary_to IS NOT NULL 
                            THEN v.salary_to
                        ELSE NULL
                    END
                ) as avg_salary
            FROM companies c
            LEFT JOIN vacancies v ON c.company_id = v.company_id
            WHERE c.company_id = %s
              AND (v.salary_currency = 'RUR' OR v.salary_currency IS NULL)
            GROUP BY c.company_id, c.company_name
        """

        self.db.cur.execute(query, (company_id,))
        result = self.db.cur.fetchone()

        if not result or result[2] == 0:
            return {"error": f"Компания с ID {company_id} не найдена или нет вакансий с зарплатой"}

        return {
            "company_id": result[0],
            "company_name": result[1],
            "vacancies_count": result[2],
            "avg_salary": float(result[3]) if result[3] else 0
        }

    def get_all_companies_avg_salary(self) -> List[Tuple[str, int, float]]:
        """
        Получает среднюю зарплату для всех компаний (только с вакансиями в рублях)

        Returns:
            Список кортежей (название_компании, количество_вакансий, средняя_зарплата)
        """
        query = """
            SELECT 
                c.company_name,
                COUNT(v.vacancy_id) as vacancy_count,
                AVG(
                    CASE 
                        WHEN v.salary_from IS NOT NULL AND v.salary_to IS NOT NULL 
                            THEN (v.salary_from + v.salary_to) / 2.0
                        WHEN v.salary_from IS NOT NULL AND v.salary_to IS NULL 
                            THEN v.salary_from
                        WHEN v.salary_from IS NULL AND v.salary_to IS NOT NULL 
                            THEN v.salary_to
                        ELSE NULL
                    END
                ) as avg_salary
            FROM companies c
            LEFT JOIN vacancies v ON c.company_id = v.company_id
            WHERE v.salary_currency = 'RUR' OR v.salary_currency IS NULL
            GROUP BY c.company_id, c.company_name
            HAVING COUNT(v.vacancy_id) > 0
            ORDER BY avg_salary DESC NULLS LAST
        """
        self.db.cur.execute(query)
        results = self.db.cur.fetchall()

        return [(name, count, float(avg) if avg else 0) for name, count, avg in results]

    def get_vacancies_with_higher_salary(self) -> List[Tuple]:
        """Получает вакансии с зарплатой выше средней (только в рублях)"""
        avg_salary = self.get_avg_salary()

        query = """
            SELECT c.company_name, v.vacancy_name,
                   v.salary_from, v.salary_to, v.url,
                   CASE 
                       WHEN salary_from IS NOT NULL AND salary_to IS NOT NULL 
                           THEN (salary_from + salary_to) / 2.0
                       WHEN salary_from IS NOT NULL AND salary_to IS NULL 
                           THEN salary_from
                       WHEN salary_from IS NULL AND salary_to IS NOT NULL 
                           THEN salary_to
                       ELSE NULL
                   END as vacancy_avg_salary
            FROM vacancies v
            JOIN companies c ON v.company_id = c.company_id
            WHERE v.salary_currency = 'RUR'
              AND (CASE 
                       WHEN salary_from IS NOT NULL AND salary_to IS NOT NULL 
                           THEN (salary_from + salary_to) / 2.0
                       WHEN salary_from IS NOT NULL AND salary_to IS NULL 
                           THEN salary_from
                       WHEN salary_from IS NULL AND salary_to IS NOT NULL 
                           THEN salary_to
                       ELSE NULL
                   END) > %s
            ORDER BY vacancy_avg_salary DESC
        """
        self.db.cur.execute(query, (avg_salary,))
        return self.db.cur.fetchall()

    def get_vacancies_with_keyword(self, keyword: str) -> List[Tuple[str, str, Optional[int], Optional[int], str]]:
        """
        Получает список всех вакансий, в названии которых содержится переданное слово

        Args:
            keyword: ключевое слово для поиска (например, "python")

        Returns:
            Список кортежей (название_компании, название_вакансии,
                           зарплата_от, зарплата_до, ссылка)
        """
        query = """
            SELECT c.company_name, v.vacancy_name,
                   v.salary_from, v.salary_to, v.url
            FROM vacancies v
            JOIN companies c ON v.company_id = c.company_id
            WHERE v.vacancy_name ILIKE %s
            ORDER BY c.company_name, v.vacancy_name
        """
        search_pattern = f"%{keyword}%"
        self.db.cur.execute(query, (search_pattern,))
        return self.db.cur.fetchall()