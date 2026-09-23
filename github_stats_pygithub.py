#!/usr/bin/env python3
"""
Альтернативная реализация через библиотеку PyGithub.
Для работы требуется: pip install PyGithub python-dotenv
"""

import argparse
from collections import Counter
import os
import sys

# Обеспечиваем корректный вывод UTF-8 в Windows-консоли
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CLI-утилита для отображения статистики пользователя GitHub (на базе PyGithub)."
    )
    parser.add_argument("username", help="Имя пользователя (login) GitHub")
    parser.add_argument(
        "--token",
        "-t",
        default=None,
        help="Personal access token (по умолчанию из GITHUB_TOKEN или GH_TOKEN)",
    )
    args = parser.parse_args()

    token = args.token or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")

    try:
        from github import Auth, Github, GithubException
    except ImportError:
        print(
            "[Ошибка]: Библиотека PyGithub не установлена. Установите её командой:\n"
            "pip install PyGithub python-dotenv\n"
            "или используйте скрипт github_stats.py (на базе requests).",
            file=sys.stderr,
        )
        sys.exit(1)

    auth = Auth.Token(token) if token else None
    g = Github(auth=auth)

    has_token = token is not None
    print(
        f"Поиск информации для пользователя '{args.username}'... "
        f"(Авторизация: {'Включена' if has_token else 'Отключена'})",
        flush=True,
    )

    try:
        user = g.get_user(args.username)
        login = user.login
        name = f" ({user.name})" if user.name else ""
        created_at_str = user.created_at.strftime("%d.%m.%Y %H:%M:%S UTC") if user.created_at else "Не указана"
        public_repos_count = user.public_repos

        total_stars = 0
        lang_counter: Counter[str] = Counter()

        # user.get_repos() автоматически выполняет пагинацию
        for repo in user.get_repos(type="owner"):
            total_stars += repo.stargazers_count
            if repo.language:
                lang_counter[repo.language] += 1

        if lang_counter:
            top_lang, lang_count = lang_counter.most_common(1)[0]
            top_lang_display = f"{top_lang} (в {lang_count} репозитори{'ях' if lang_count > 1 else 'и'})"
        else:
            top_lang_display = "Не определен / Нет исходного кода"

        print("\n" + "=" * 55)
        print(f"  Статистика GitHub: {login}{name}")
        print("=" * 55)
        print(f"  Дата регистрации:                 {created_at_str}")
        print(f"  Количество публичных репозиториев: {public_repos_count}")
        print(f"  Общее число звёзд:                ⭐ {total_stars}")
        print(f"  Самый популярный язык:            {top_lang_display}")
        print("=" * 55 + "\n")

    except GithubException as e:
        if e.status == 404:
            print(f"[Ошибка]: Пользователь '{args.username}' не найден на GitHub (404).", file=sys.stderr)
        elif e.status == 401:
            print("[Ошибка]: Неверный токен авторизации (401 Unauthorized).", file=sys.stderr)
        elif e.status == 403:
            print("[Ошибка]: Превышен лимит запросов API или доступ запрещен (403).", file=sys.stderr)
        else:
            print(f"[Ошибка GitHub API]: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[Непредвиденная ошибка]: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
