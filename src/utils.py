import re
from typing import Dict, Any, Tuple, Optional, List


def clean_html(text: str) -> str:
    if not text:
        return ""
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)
    text = re.sub(r'&[a-z]+;', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def parse_salary(salary_data: Optional[Dict]) -> Tuple[Optional[int], Optional[int], Optional[str]]:
    if not salary_data:
        return None, None, None

    salary_from = salary_data.get("from")
    salary_to = salary_data.get("to")
    currency = salary_data.get("currency")

    if salary_from is not None:
        salary_from = int(salary_from)
    if salary_to is not None:
        salary_to = int(salary_to)

    return salary_from, salary_to, currency


def parse_description(vacancy: Dict[str, Any]) -> Optional[str]:
    if "full_description" in vacancy and vacancy["full_description"]:
        return clean_html(vacancy["full_description"])

    snippet = vacancy.get("snippet", {})
    responsibility = snippet.get("responsibility", "")
    requirement = snippet.get("requirement", "")

    description_parts = []

    if responsibility:
        responsibility = clean_html(responsibility)
        description_parts.append(f"Обязанности: {responsibility}")

    if requirement:
        requirement = clean_html(requirement)
        description_parts.append(f"Требования: {requirement}")

    return "\n\n".join(description_parts) if description_parts else None


def format_salary(salary_from: Optional[int] = None, salary_to: Optional[int] = None) -> str:
    if salary_from is None and salary_to is None:
        return "не указана"
    elif salary_from and salary_to:
        return f"{salary_from:,} - {salary_to:,} ₽".replace(",", " ")
    elif salary_from:
        return f"от {salary_from:,} ₽".replace(",", " ")
    elif salary_to:
        return f"до {salary_to:,} ₽".replace(",", " ")
    return "не указана"


def extract_company_id_from_url(url: str) -> Optional[str]:
    match = re.search(r'/employer/(\d+)', url)
    return match.group(1) if match else None


def validate_vacancy_data(vacancy: Dict[str, Any]) -> bool:
    required_fields = ["id", "name"]
    for field in required_fields:
        if field not in vacancy or not vacancy[field]:
            return False
    return True


def filter_vacancies_by_salary(vacancies: List[Dict], min_salary: int) -> List[Dict]:
    filtered = []
    for vacancy in vacancies:
        salary_data = vacancy.get("salary")
        if salary_data:
            salary_from = salary_data.get("from")
            if salary_from and salary_from >= min_salary:
                filtered.append(vacancy)
    return filtered


def get_top_vacancies_by_salary(vacancies: List[Dict], top_n: int = 10) -> List[Dict]:
    def get_salary_value(vacancy):
        salary_data = vacancy.get("salary")
        if not salary_data:
            return 0
        salary_from = salary_data.get("from") or 0
        salary_to = salary_data.get("to") or 0
        return max(salary_from, salary_to)

    sorted_vacancies = sorted(
        vacancies,
        key=get_salary_value,
        reverse=True
    )
    return sorted_vacancies[:top_n]