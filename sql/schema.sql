-- Удаляем таблицы, если существуют
DROP TABLE IF EXISTS vacancies;
DROP TABLE IF EXISTS companies;

-- Создание таблицы компаний
CREATE TABLE companies (
    company_id INTEGER PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    description TEXT,
    url VARCHAR(255)
);

-- Создание таблицы вакансий (с описанием!)
CREATE TABLE vacancies (
    vacancy_id INTEGER PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    vacancy_name VARCHAR(255) NOT NULL,
    description TEXT,
    salary_from INTEGER,
    salary_to INTEGER,
    salary_currency VARCHAR(10),
    url VARCHAR(255)
);

-- Индекс для ускорения запросов по company_id
CREATE INDEX IF NOT EXISTS idx_vacancies_company_id ON vacancies(company_id);