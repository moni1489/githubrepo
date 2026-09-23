#!/usr/bin/env python3
"""
CLI-скрипт для получения статистики пользователя GitHub через GitHub REST API.
"""

import argparse
from collections import Counter
from datetime import datetime
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

# Обеспечиваем корректный вывод UTF-8 в Windows-консоли
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

import requests
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env, если он существует
load_dotenv()


def get_auth_headers(token: Optional[str] = None) -> Dict[str, str]:
    """Формирует заголовки запроса к GitHub API, включая токен при наличии."""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "GitHub-User-Stats-CLI",
    }
    # Проверяем токен из аргументов или переменных окружения GITHUB_TOKEN / GH_TOKEN
    resolved_token = token or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if resolved_token:
        headers["Authorization"] = f"Bearer {resolved_token.strip()}"
    return headers


def format_date(iso_date_str: str) -> str:
    """Форматирует дату из ISO 8601 в человекочитаемый вид."""
    try:
        # Python 3.11+ поддерживает 'Z' в fromisoformat
        dt = datetime.fromisoformat(iso_date_str.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M:%S UTC")
    except Exception:
        return iso_date_str


def fetch_user_data(username: str, headers: Dict[str, str]) -> Dict[str, Any]:
    """Получает информацию о профиле пользователя."""
    url = f"https://api.github.com/users/{username}"
    try:
        response = requests.get(url, headers=headers, timeout=15)
    except requests.exceptions.RequestException as e:
        print(f"[Ошибка сети]: Не удалось подключиться к GitHub API: {e}", file=sys.stderr)
        sys.exit(1)

    if response.status_code == 404:
        print(f"[Ошибка]: Пользователь '{username}' не найден на GitHub (404).", file=sys.stderr)
        sys.exit(1)
    elif response.status_code == 401:
        print("[Ошибка]: Неверный токен авторизации (401 Unauthorized). Проверьте ваш GITHUB_TOKEN.", file=sys.stderr)
        sys.exit(1)
    elif response.status_code == 403:
        remaining = response.headers.get("x-ratelimit-remaining", "0")
        if remaining == "0":
            reset_time = response.headers.get("x-ratelimit-reset", "")
            reset_str = ""
            if reset_time.isdigit():
                reset_dt = datetime.fromtimestamp(int(reset_time))
                reset_str = f" Сброс лимита: {reset_dt.strftime('%H:%M:%S')}."
            print(
                f"[Ошибка]: Превышен лимит запросов GitHub API (Rate Limit Exceeded).{reset_str}\n"
                "Рекомендуется указать personal access token через переменную окружения GITHUB_TOKEN.",
                file=sys.stderr,
            )
        else:
            print(f"[Ошибка]: Доступ ограничен (403 Forbidden): {response.text}", file=sys.stderr)
        sys.exit(1)
    elif not response.ok:
        print(f"[Ошибка]: API вернуло статус {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)

    return response.json()


def fetch_all_repositories(username: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
    """Получает все публичные репозитории пользователя с учётом пагинации."""
    repos: List[Dict[str, Any]] = []
    url: Optional[str] = f"https://api.github.com/users/{username}/repos?per_page=100&type=owner"

    while url:
        try:
            response = requests.get(url, headers=headers, timeout=15)
        except requests.exceptions.RequestException as e:
            print(f"[Ошибка сети при получении репозиториев]: {e}", file=sys.stderr)
            break

        if not response.ok:
            print(f"[Предупреждение]: Не удалось загрузить часть репозиториев (HTTP {response.status_code}).", file=sys.stderr)
            break

        page_repos = response.json()
        if not isinstance(page_repos, list):
            break

        repos.extend(page_repos)

        # Обработка пагинации через заголовок Link
        next_link = response.links.get("next")
        if next_link and "url" in next_link:
            url = next_link["url"]
        else:
            url = None

    return repos


def calculate_stats(repos: List[Dict[str, Any]]) -> Tuple[int, Optional[str], int]:
    """
    Вычисляет:
    1. Суммарное количество звёзд.
    2. Самый популярный язык (по числу репозиториев).
    3. Количество репозиториев, использующих этот язык.
    """
    total_stars = 0
    language_counter: Counter[str] = Counter()

    for repo in repos:
        total_stars += repo.get("stargazers_count", 0)
        lang = repo.get("language")
        if lang:
            language_counter[lang] += 1

    if language_counter:
        most_popular_lang, count = language_counter.most_common(1)[0]
    else:
        most_popular_lang, count = None, 0

    return total_stars, most_popular_lang, count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CLI-утилита для отображения статистики пользователя GitHub."
    )
    parser.add_argument(
        "username",
        help="Имя пользователя (login) GitHub",
    )
    parser.add_argument(
        "--token",
        "-t",
        default=None,
        help="Personal access token (если не указан, берется из переменной окружения GITHUB_TOKEN или GH_TOKEN)",
    )

    args = parser.parse_args()

    headers = get_auth_headers(token=args.token)
    has_token = "Authorization" in headers

    print(
        f"Поиск информации для пользователя '{args.username}'... "
        f"(Авторизация: {'Включена' if has_token else 'Отключена'})",
        flush=True,
    )

    # 1. Получение данных профиля
    user_data = fetch_user_data(args.username, headers)

    # 2. Получение репозиториев пользователя
    repos = fetch_all_repositories(args.username, headers)

    # 3. Подсчёт статистики
    total_stars, top_language, top_language_repos = calculate_stats(repos)

    public_repos_count = user_data.get("public_repos", len(repos))
    created_at_raw = user_data.get("created_at", "")
    created_at_formatted = format_date(created_at_raw) if created_at_raw else "Не указана"

    if top_language:
        top_language_display = f"{top_language} (в {top_language_repos} репозитори{'ях' if top_language_repos > 1 else 'и'})"
    else:
        top_language_display = "Не определен / Нет исходного кода"

    name_str = f" ({user_data.get('name')})" if user_data.get("name") else ""

    # Вывод результатов
    print("\n" + "=" * 55)
    print(f"  Статистика GitHub: {user_data.get('login', args.username)}{name_str}")
    print("=" * 55)
    print(f"  Дата регистрации:                 {created_at_formatted}")
    print(f"  Количество публичных репозиториев: {public_repos_count}")
    print(f"  Общее число звёзд:                ⭐ {total_stars}")
    print(f"  Самый популярный язык:            {top_language_display}")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
