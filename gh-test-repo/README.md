# GitHub Actions Dispatch Test Repository

Этот репозиторий создан для тестирования функциональности `workflow_dispatch` в GitHub Actions.

## 🎯 Цель

Проверить, что кнопка "Run workflow" появляется в GitHub UI и workflow можно запускать вручную.

## 📁 Структура

```
gh-test-repo/
├── README.md                    # Этот файл
├── .github/workflows/
│   └── dispatch-test.yml       # Тестовый workflow
└── hello.py                    # Простой Python скрипт
```

## 🚀 Как проверить workflow_dispatch

### 1. Перейти в GitHub UI
- Откройте репозиторий в браузере
- Перейдите в раздел **Actions**

### 2. Найти workflow
- В списке workflow найдите **"Dispatch Test"**
- Нажмите на него

### 3. Запустить вручную
- Нажмите кнопку **"Run workflow"** (справа)
- Выберите ветку (обычно `main`)
- Введите тестовое сообщение (опционально)
- Нажмите **"Run workflow"**

### 4. Проверить выполнение
- Workflow должен появиться в списке запусков
- Статус должен быть **"completed"** со значком ✅
- В логах должно быть сообщение: "Hello from dispatch test!"

## 🔧 Локальное тестирование

```bash
# Запустить Python скрипт
python3 hello.py

# Ожидаемый вывод:
# Hello from test repo!
```

## 📋 Ожидаемые результаты

✅ **Успех**: Кнопка "Run workflow" видна и workflow выполняется  
❌ **Проблема**: Кнопка не появляется или workflow не запускается

## 🐛 Troubleshooting

Если workflow не запускается:
1. Проверьте, что файл `.github/workflows/dispatch-test.yml` существует
2. Убедитесь, что в файле есть блок `workflow_dispatch:`
3. Проверьте синтаксис YAML
4. Подождите 1-2 минуты после push изменений
