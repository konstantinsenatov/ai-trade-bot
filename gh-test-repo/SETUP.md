# Инструкция по настройке тестового репозитория

## 🚀 Шаги для создания нового репозитория

### 1. Создать новый репозиторий на GitHub
```bash
# Перейти в папку тестового репозитория
cd gh-test-repo

# Инициализировать git
git init

# Добавить все файлы
git add .

# Сделать первый коммит
git commit -m "Initial commit: GitHub Actions dispatch test repository"

# Создать репозиторий на GitHub (требует gh CLI)
gh repo create "github-dispatch-test" --public --source=. --remote=origin --push
```

### 2. Альтернативный способ (через веб-интерфейс)
1. Создать новый репозиторий на GitHub.com
2. Скопировать содержимое папки `gh-test-repo/` в новый репозиторий
3. Сделать commit и push

### 3. Проверить workflow_dispatch
1. Открыть репозиторий в браузере
2. Перейти в **Actions**
3. Найти **"Dispatch Test"** workflow
4. Нажать **"Run workflow"**
5. Проверить выполнение

## 📋 Ожидаемые результаты

✅ **Успех**: 
- Кнопка "Run workflow" видна
- Workflow выполняется успешно
- В логах видно сообщение "Hello from dispatch test!"

❌ **Проблема**:
- Кнопка "Run workflow" не появляется
- Workflow не запускается
- Ошибки в логах

## 🔍 Диагностика

Если workflow не работает:
1. Проверить синтаксис YAML
2. Убедиться, что файл находится в `.github/workflows/`
3. Проверить, что есть блок `workflow_dispatch:`
4. Подождать 1-2 минуты после push
