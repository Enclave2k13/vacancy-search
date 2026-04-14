"""Конфигурация и создание базы данных"""

import os

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from src.logger import app_logger

load_dotenv()


def get_db_params() -> dict:
    """Возвращает параметры подключения к БД из .env файла"""
    params = {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME")
    }

    # Проверяем, что все параметры заданы
    missing = [k for k, v in params.items() if not v]
    if missing:
        error_msg = f"Отсутствуют обязательные параметры в .env: {', '.join(missing)}"
        app_logger.error(error_msg)
        raise ValueError(error_msg)

    app_logger.debug(f"Параметры БД: host={params['host']}, port={params['port']}, database={params['database']}")
    return params


def create_database() -> None:
    """
    Создает базу данных, если она не существует.
    Подключается к системной БД 'postgres' для выполнения команды CREATE DATABASE.
    """
    params = get_db_params()
    db_name = params.pop("database")

    app_logger.info(f"Проверка существования базы данных '{db_name}'")

    try:
        conn = psycopg2.connect(**params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cur.fetchone()

        if not exists:
            cur.execute(f"CREATE DATABASE {db_name}")
            app_logger.info(f"База данных '{db_name}' успешно создана")
        else:
            app_logger.info(f"База данных '{db_name}' уже существует")

        cur.close()
        conn.close()

    except Exception as e:
        app_logger.error(f"Ошибка при создании базы данных: {e}")
        raise


COMPANIES = [
    ("1740", "Яндекс"),
    ("3529", "Сбер"),
    ("39305", "Тинькофф"),
    ("4181", "ВКонтакте"),
    ("80", "Альфа-Банк"),
    ("15478", "Ozon"),
    ("3776", "МТС"),
    ("1057", "Лаборатория Касперского"),
    ("78638", "Wildberries"),
    ("2381", "HeadHunter"),
    ("9498120", "Avito"),
    ("87021", "2ГИС"),
]

COMPANY_IDS = [company_id for company_id, _ in COMPANIES]


def get_companies_with_names() -> list:
    """Возвращает список компаний с ID и названиями"""
    return COMPANIES
