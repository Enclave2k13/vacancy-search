"""Общие фикстуры для тестов"""

import pytest
import sys
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_db_params
from src.database import Database
from src.logger import app_logger


@pytest.fixture(scope="session")
def test_database():
    """
    SETUP SESSION: Создает тестовую БД один раз для всех тестов
    TEARDOWN SESSION: Удаляет тестовую БД после всех тестов
    """
    params = get_db_params()
    db_name = params["database"]
    test_db_name = f"{db_name}_test"

    # ========== SETUP SESSION ==========
    print(f"\n{'='*60}")
    print(f"🔨 SETUP SESSION: Создание тестовой БД '{test_db_name}'")
    print(f"{'='*60}")

    # Подключаемся к системной БД
    admin_params = params.copy()
    admin_params["database"] = "postgres"
    admin_conn = psycopg2.connect(**admin_params)
    admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    admin_cur = admin_conn.cursor()

    # Убиваем все соединения с тестовой БД, если она существует
    admin_cur.execute(f"""
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = '{test_db_name}'
    """)

    # Удаляем старую БД, если есть
    admin_cur.execute(f"DROP DATABASE IF EXISTS {test_db_name}")

    # Создаем новую БД
    admin_cur.execute(f"CREATE DATABASE {test_db_name}")

    admin_cur.close()
    admin_conn.close()

    # Подключаемся к тестовой БД и создаем таблицы
    params["database"] = test_db_name
    conn = psycopg2.connect(**params)
    conn.autocommit = True
    cur = conn.cursor()

    db = Database()
    db.conn = conn
    db.cur = cur
    db.create_tables()

    app_logger.info(f"✅ Тестовая БД '{test_db_name}' создана")

    yield db  # Передаем БД в тесты

    # ========== TEARDOWN SESSION ==========
    print(f"\n{'='*60}")
    print(f"🧹 TEARDOWN SESSION: Удаление тестовой БД '{test_db_name}'")
    print(f"{'='*60}")

    # Закрываем соединение
    cur.close()
    conn.close()

    # Убиваем все активные соединения
    admin_conn = psycopg2.connect(**admin_params)
    admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    admin_cur = admin_conn.cursor()

    admin_cur.execute(f"""
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = '{test_db_name}'
    """)

    # Удаляем БД
    admin_cur.execute(f"DROP DATABASE IF EXISTS {test_db_name}")

    admin_cur.close()
    admin_conn.close()

    app_logger.info(f"✅ Тестовая БД '{test_db_name}' удалена")
    print(f"{'='*60}\n")


@pytest.fixture(autouse=True)
def clean_tables_before_each_test(test_database):
    """
    SETUP FUNCTION: Очищает таблицы перед КАЖДЫМ тестом
    TEARDOWN FUNCTION: (не нужен)
    """
    print("  🔨 SETUP FUNCTION: Очистка таблиц перед тестом")

    # Очищаем таблицы
    test_database.cur.execute("TRUNCATE TABLE vacancies CASCADE")
    test_database.cur.execute("TRUNCATE TABLE companies CASCADE")
    test_database.conn.commit()

    yield  # Запускаем тест

    # Ничего не делаем после теста (очистка уже произошла перед следующим)
    print("  ✅ TEST COMPLETED")


@pytest.fixture
def sample_companies_data(test_database):
    """
    SETUP: Создает тестовые компании
    """
    print("    📦 SETUP: Добавление тестовых компаний")

    companies = [
        (1, "Company A", "Description A", "url1"),
        (2, "Company B", "Description B", "url2"),
    ]

    for company in companies:
        test_database.cur.execute("""
            INSERT INTO companies (company_id, company_name, description, url)
            VALUES (%s, %s, %s, %s)
        """, company)

    test_database.conn.commit()

    yield companies

    # TEARDOWN: удаляем только что созданные компании
    print("    🧹 TEARDOWN: Удаление тестовых компаний")
    test_database.cur.execute("DELETE FROM companies WHERE company_id IN (1, 2)")
    test_database.conn.commit()


@pytest.fixture
def sample_vacancies_data(test_database, sample_companies_data):
    """
    SETUP: Создает тестовые вакансии (зависит от компаний)
    """
    print("    📦 SETUP: Добавление тестовых вакансий")

    vacancies = [
        (1, 1, "Python Dev", 100000, 150000, "RUR", "url1"),
        (2, 1, "Java Dev", 120000, 180000, "RUR", "url2"),
        (3, 2, "JS Dev", 90000, 110000, "RUR", "url3"),
        (4, 2, "Python Backend", 130000, 170000, "RUR", "url4"),
    ]

    for vacancy in vacancies:
        test_database.cur.execute("""
            INSERT INTO vacancies (vacancy_id, company_id, vacancy_name,
                                 salary_from, salary_to, salary_currency, url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, vacancy)

    test_database.conn.commit()

    yield vacancies

    # TEARDOWN: удаляем вакансии
    print("    🧹 TEARDOWN: Удаление тестовых вакансий")
    test_database.cur.execute("DELETE FROM vacancies WHERE company_id IN (1, 2)")
    test_database.conn.commit()


@pytest.fixture
def sample_company():
    """Простой пример компании (без БД)"""
    return {
        "id": "12345",
        "name": "Test Company",
        "description": "<p>Test <b>description</b></p>",
        "site_url": "https://test.com",
        "alternate_url": "https://hh.ru/employer/12345"
    }


@pytest.fixture
def sample_vacancy():
    """Простой пример вакансии (без БД)"""
    return {
        "id": "67890",
        "name": "Python Developer",
        "alternate_url": "https://hh.ru/vacancy/67890",
        "salary": {
            "from": 100000,
            "to": 150000,
            "currency": "RUR"
        },
        "snippet": {
            "responsibility": "<p>Разработка бэкенда</p>",
            "requirement": "<p>Знание Python</p>"
        }
    }