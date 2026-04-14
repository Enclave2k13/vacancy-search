"""Класс для управления подключением к БД и основными операциями"""

import os
import psycopg2
from typing import List, Dict, Any
from src.config import get_db_params
from src.logger import app_logger
from src.utils import clean_html, parse_salary, parse_description


class Database:
    """Класс для управления подключением к БД"""

    def __init__(self):
        """Инициализация подключения к БД"""
        try:
            params = get_db_params()
            self.conn = psycopg2.connect(**params)
            self.cur = self.conn.cursor()
            app_logger.info("Успешное подключение к базе данных")
        except Exception as e:
            app_logger.error(f"Ошибка подключения к БД: {e}")
            raise

    def create_tables(self, schema_path: str = "../sql/schema.sql") -> None:
        """
        Создает таблицы из SQL-файла

        Args:
            schema_path: путь к файлу со схемой БД
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(current_dir, schema_path)

        try:
            self.cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'companies'
                );
            """)
            tables_exist = self.cur.fetchone()[0]

            if tables_exist:
                app_logger.info("Таблицы уже существуют. Пропускаем создание.")
                return

            current_dir = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(current_dir, schema_path)

            with open(full_path, 'r', encoding='utf-8') as f:
                sql = f.read()

            self.cur.execute(sql)
            self.conn.commit()
            app_logger.info("Таблицы успешно созданы")

        except FileNotFoundError:
            app_logger.error(f"Файл {full_path} не найден")
            raise
        except Exception as e:
            app_logger.error(f"Ошибка при создании таблиц: {e}")
            raise

    def insert_companies(self, companies: List[Dict[str, Any]]) -> None:
        """
        Вставляет список компаний в таблицу с очисткой HTML из описания

        Args:
            companies: список словарей с данными о компаниях
        """
        insert_query = """
            INSERT INTO companies (company_id, company_name, description, url)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (company_id) DO NOTHING
        """

        count = 0
        for company in companies:
            try:
                company_id = int(company["id"])
                name = company.get("name", "")
                raw_description = company.get("description", "")
                description = clean_html(raw_description) if raw_description else None
                url = company.get("site_url") or company.get("alternate_url", "")

                self.cur.execute(insert_query, (company_id, name, description, url))
                count += 1
                app_logger.debug(f"Компания {name} (ID={company_id}) добавлена")
            except Exception as e:
                app_logger.error(f"Ошибка при вставке компании {company.get('id')}: {e}")

        self.conn.commit()
        app_logger.info(f"Добавлено {count} компаний")

    def insert_vacancies(self, vacancies: List[Dict[str, Any]], company_id: int) -> None:
        """
        Вставляет вакансии компании в таблицу

        Args:
            vacancies: список вакансий
            company_id: ID компании
        """
        insert_query = """
            INSERT INTO vacancies (
                vacancy_id, company_id, vacancy_name, description,
                salary_from, salary_to, salary_currency, url
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (vacancy_id) DO NOTHING
        """

        count = 0
        for vacancy in vacancies:
            try:
                vacancy_id = int(vacancy["id"])
                name = vacancy.get("name", "")
                url = vacancy.get("alternate_url", "")

                description = parse_description(vacancy)
                salary_from, salary_to, currency = parse_salary(vacancy.get("salary"))

                self.cur.execute(
                    insert_query,
                    (vacancy_id, company_id, name, description,
                     salary_from, salary_to, currency, url)
                )
                count += 1
                app_logger.debug(f"Вакансия {name} (ID={vacancy_id}) добавлена")
            except Exception as e:
                app_logger.error(f"Ошибка при вставке вакансии {vacancy.get('id')}: {e}")

        self.conn.commit()
        app_logger.info(f"Добавлено {count} вакансий для компании {company_id}")

    def close(self) -> None:
        """Закрывает соединение с БД"""
        app_logger.info("Закрытие соединения с базой данных")
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()