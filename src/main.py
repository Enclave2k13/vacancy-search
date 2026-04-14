import sys

from src.api_client import HHAPIClient
from src.config import create_database, COMPANY_IDS
from src.database import Database
from src.db_manager import DBManager
from src.logger import app_logger
from src.utils import format_salary


def ask_user_choice() -> str:
    print("\n" + "=" * 50)
    print("Добро пожаловать в Vacancy Search!")
    print("=" * 50)
    print("\nЧто вы хотите сделать?")
    print("  1. Полностью обновить данные (создать/пересоздать БД и загрузить свежие вакансии)")
    print("  2. Использовать существующую БД (без загрузки новых данных)")
    print("  3. Выйти из программы")
    print("-" * 50)

    while True:
        choice = input("Ваш выбор (1/2/3): ").strip()
        if choice == "1":
            return "create"
        elif choice == "2":
            return "skip"
        elif choice == "3":
            return "exit"
        else:
            print("Неверный ввод. Пожалуйста, введите 1, 2 или 3.")


def confirm_overwrite() -> bool:
    print("\nВНИМАНИЕ! Это действие удалит все существующие данные")
    print("   и загрузит новые вакансии с hh.ru.")
    print("   Весь процесс может занять несколько минут.")

    while True:
        answer = input("\nВы уверены, что хотите продолжить? (да/нет): ").strip().lower()
        if answer in ["да", "yes", "y", "д"]:
            return True
        elif answer in ["нет", "no", "n", "н"]:
            return False
        else:
            print("Пожалуйста, ответьте 'да' или 'нет'")


def load_fresh_data():
    app_logger.info("=" * 50)
    app_logger.info("Начало загрузки свежих данных")

    print("\nСоздание/обновление базы данных...")
    create_database()

    print("\nСоздание таблиц...")
    db = Database()
    db.create_tables()

    print("\nПолучение данных из API hh.ru...")
    api = HHAPIClient()

    companies_data = []
    all_vacancies_count = 0

    for i, company_id in enumerate(COMPANY_IDS, 1):
        print(f"\n[{i}/{len(COMPANY_IDS)}] Загрузка компании ID={company_id}...")
        app_logger.info(f"Загрузка компании {company_id}")
        try:
            company = api.get_company(company_id)
            companies_data.append(company)
            print(f"Компания: {company.get('name')}")
        except Exception as e:
            print(f"Ошибка загрузки компании {company_id}: {e}")
            app_logger.error(f"Ошибка загрузки компании {company_id}: {e}")

    print("\nСохранение компаний в БД...")
    db.insert_companies(companies_data)

    for company in companies_data:
        company_id = int(company["id"])
        company_name = company.get('name')
        print(f"\nЗагрузка вакансий для {company_name} (ID={company_id})...")
        app_logger.info(f"Загрузка вакансий для компании {company_name}")

        try:
            vacancies = api.get_vacancies(str(company_id), max_vacancies=10)
            all_vacancies_count += len(vacancies)
            print(f"   Загружено {len(vacancies)} вакансий с зарплатой")

            if vacancies:
                db.insert_vacancies(vacancies, company_id)
            else:
                app_logger.warning(f"Для компании {company_name} не найдено вакансий с зарплатой в рублях")
        except Exception as e:
            print(f"Ошибка загрузки вакансий: {e}")
            app_logger.error(f"Ошибка загрузки вакансий для {company_name}: {e}")

    api.close()
    db.close()

    print("\n" + "=" * 50)
    print(f"Загрузка завершена!")
    print(f"   - Компаний: {len(companies_data)}")
    print(f"   - Вакансий с зарплатой: {all_vacancies_count}")
    print("=" * 50)

    app_logger.info(f"Загрузка завершена: {len(companies_data)} компаний, {all_vacancies_count} вакансий")


def use_existing_db():
    print("\nПодключение к существующей базе данных...")
    app_logger.info("Подключение к существующей БД")

    db = Database()

    db.cur.execute("SELECT COUNT(*) FROM companies")
    companies_count = db.cur.fetchone()[0]

    db.cur.execute("SELECT COUNT(*) FROM vacancies")
    vacancies_count = db.cur.fetchone()[0]

    print(f"Найдено компаний: {companies_count}")
    print(f"Найдено вакансий: {vacancies_count}")
    app_logger.info(f"Существующая БД: {companies_count} компаний, {vacancies_count} вакансий")

    if companies_count == 0:
        print("\nБаза данных пуста. Рекомендуем загрузить данные (выберите вариант 1).")
        app_logger.warning("База данных пуста")

    db.close()
    return companies_count, vacancies_count


def show_interactive_menu(db_manager: DBManager):
    app_logger.info("Запуск интерактивного меню")

    while True:
        print("\n" + "=" * 50)
        print("МЕНЮ АНАЛИЗА ДАННЫХ")
        print("=" * 50)
        print("  1. Список компаний и количество вакансий")
        print("  2. Список всех вакансий")
        print("  3. Средняя зарплата по всем вакансиям")
        print("  4. Вакансии с зарплатой выше средней")
        print("  5. Поиск вакансий по ключевому слову")
        print("  6. Средняя зарплата по конкретной компании")
        print("  7. Сравнение средней зарплаты по всем компаниям")
        print("  0. Выход")
        print("-" * 50)

        choice = input("Ваш выбор: ").strip()

        if choice == "1":
            print("\nКомпании и количество вакансий:")
            print("-" * 40)
            results = db_manager.get_companies_and_vacancies_count()
            for company, count in results:
                print(f"   {company}: {count} вакансий")
            if not results:
                print("   Нет данных")
            app_logger.debug("Выполнен запрос 1")

        elif choice == "2":
            print("\nСписок всех вакансий:")
            print("-" * 60)
            results = db_manager.get_all_vacancies()
            for company, name, salary_from, salary_to, url in results:
                salary_str = format_salary(salary_from, salary_to)
                print(f"   {company} - {name}")
                print(f"      Зарплата: {salary_str}")
                print(f"      Ссылка: {url}")
                print()
            if not results:
                print("   Нет данных")
            app_logger.debug("Выполнен запрос 2")

        elif choice == "3":
            avg_salary = db_manager.get_avg_salary()
            print(f"\nСредняя зарплата по всем вакансиям: {avg_salary:,.0f} ₽".replace(",", " "))
            app_logger.debug(f"Средняя зарплата: {avg_salary}")

        elif choice == "4":
            print("\nВакансии с зарплатой выше средней:")
            print("-" * 60)
            results = db_manager.get_vacancies_with_higher_salary()
            for company, name, salary_from, salary_to, url, vacancy_avg in results:
                salary_str = format_salary(salary_from, salary_to)
                print(f"   {company} - {name}")
                print(f"      Зарплата: {salary_str} (средняя: {vacancy_avg:,.0f} ₽)".replace(",", " "))
                print(f"      Ссылка: {url}")
                print()
            if not results:
                print("   Нет данных")
            app_logger.debug("Выполнен запрос 4")

        elif choice == "5":
            keyword = input("\nВведите ключевое слово для поиска: ").strip()
            if keyword:
                print(f"\nРезультаты поиска по слову '{keyword}':")
                print("-" * 60)
                results = db_manager.get_vacancies_with_keyword(keyword)
                for company, name, salary_from, salary_to, url in results:
                    salary_str = format_salary(salary_from, salary_to)
                    print(f"   {company} - {name}")
                    print(f"      Зарплата: {salary_str}")
                    print(f"      Ссылка: {url}")
                    print()
                if not results:
                    print(f"   По слову '{keyword}' ничего не найдено")
                app_logger.info(f"Поиск по ключевому слову '{keyword}': найдено {len(results)} вакансий")
            else:
                print("   Ключевое слово не может быть пустым")

        elif choice == "6":
            print("\nСредняя зарплата по компании")
            print("-" * 50)
            from src.config import get_companies_with_names
            companies = get_companies_with_names()
            print("\nДоступные компании:")
            print("-" * 60)
            print(f"{'ID':<12} {'Название компании':<35}")
            print("-" * 60)
            for company_id, company_name in companies:
                print(f"{company_id:<12} {company_name:<35}")
            print("-" * 60)
            print("\nВведите ID компании из списка выше")
            print("-" * 40)
            try:
                company_id_input = input("Введите ID компании: ").strip()
                if not company_id_input.isdigit():
                    print("ID должен быть числом")
                    app_logger.error(f"Неверный формат ID компании: {company_id_input}")
                else:
                    company_id = int(company_id_input)
                    valid_ids = [int(cid) for cid, _ in companies]
                    if company_id not in valid_ids:
                        print(f"Компания с ID {company_id} не найдена в списке")
                        print(f"Доступные ID: {', '.join(map(str, valid_ids))}")
                        app_logger.warning(f"Попытка запроса несуществующего ID: {company_id}")
                    else:
                        result = db_manager.get_avg_salary_by_company(company_id)
                        if "error" in result:
                            print(f"{result['error']}")
                            app_logger.warning(f"Компания с ID {company_id} не найдена в БД")
                        else:
                            print(f"\n{result['company_name']}")
                            print(f"Вакансий с зарплатой: {result['vacancies_count']}")
                            print(f"Средняя зарплата: {result['avg_salary']:,.0f} ₽".replace(",", " "))
                            app_logger.debug(f"Средняя зарплата для компании {company_id}: {result['avg_salary']}")
            except ValueError:
                print("ID должен быть числом")
                app_logger.error("Неверный формат ID компании")

        elif choice == "7":
            print("\nСравнение средней зарплаты по компаниям:")
            print("-" * 60)
            results = db_manager.get_all_companies_avg_salary()
            if results:
                print(f"{'Компания':<30} {'Вакансий':<10} {'Средняя з/п':<15}")
                print("-" * 60)
                for name, count, avg in results:
                    if avg > 0:
                        avg_str = f"{avg:,.0f} ₽".replace(",", " ")
                    else:
                        avg_str = "нет данных"
                    print(f"{name:<30} {count:<10} {avg_str:<15}")
                app_logger.debug(f"Выполнено сравнение зарплат по {len(results)} компаниям")
            else:
                print("Нет данных")

        elif choice in ["0", "exit", "выход", "quit", "q", "выйти"]:
            print("\nДо свидания!")
            app_logger.info("Завершение работы программы")
            break
        else:
            print("\nНеверный выбор. Пожалуйста, введите число от 0 до 7.")
            app_logger.warning(f"Неверный выбор в меню: {choice}")

def main():
    app_logger.info("=" * 50)
    app_logger.info("Запуск приложения Vacancy Search")
    app_logger.info("=" * 50)

    user_choice = ask_user_choice()

    if user_choice == "exit":
        print("\nДо свидания!")
        app_logger.info("Программа завершена пользователем")
        sys.exit(0)

    elif user_choice == "create":
        if confirm_overwrite():
            load_fresh_data()
        else:
            print("\nЗагрузка отменена. Выход из программы.")
            app_logger.info("Загрузка отменена пользователем")
            sys.exit(0)

    elif user_choice == "skip":
        use_existing_db()

    print("\nПодключение к базе данных для аналитики...")
    try:
        db = Database()
        db_manager = DBManager(db)
        show_interactive_menu(db_manager)
        db.close()
    except Exception as e:
        app_logger.error(f"Критическая ошибка: {e}")
        print(f"\nПроизошла ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()