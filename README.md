# GitHub User Statistics CLI

Консольная утилита на Python для получения базовой аналитики профиля GitHub:
- Количество публичных репозиториев
- Суммарное число звёзд по всем репозиториям
- Самый популярный язык программирования
- Дата регистрации аккаунта

## 🚀 Установка

Установите зависимости:
```bash
pip install -r requirements.txt
```

## 🔑 Авторизация через Personal Access Token

GitHub ограничивает неавторизованные запросы до 60 в час. С персональным токеном лимит увеличивается до 5000 запросов в час.

Вы можете передать токен одним из трёх способов:

1. **Через переменную окружения `GITHUB_TOKEN`**:
   - **Windows (PowerShell)**:
     ```powershell
     $env:GITHUB_TOKEN="ghp_ваш_токен"
     ```
   - **Linux / macOS (Bash/Zsh)**:
     ```bash
     export GITHUB_TOKEN="ghp_ваш_токен"
     ```
2. **Через файл `.env`**:
   Скопируйте пример:
   ```bash
   cp .env.example .env
   ```
   и укажите значение `GITHUB_TOKEN` внутри файла.
3. **Через флаг командной строки `--token`**:
   ```bash
   python github_stats.py octocat --token ghp_ваш_токен
   ```

## 💻 Использование

Запуск основной версии (на базе `requests`):
```bash
python github_stats.py <username>
```

Пример:
```bash
python github_stats.py torvalds
```

Также доступна альтернативная реализация на `PyGithub` в файле `github_stats_pygithub.py`:
```bash
pip install PyGithub
python github_stats_pygithub.py torvalds
```
