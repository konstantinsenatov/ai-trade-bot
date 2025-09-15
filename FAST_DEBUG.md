# Fast Debug Runs

Этот документ содержит команды для быстрой отладки и тестирования бэктестов.

## 🚀 Быстрые команды

### Smoke тесты (5-30 секунд)

#### Исторические данные
```bash
python3 scripts/backtest.py --mode onebar --strategy optimized --data-source historical --smoke --verbose --out artifacts/backtests/onebar_hist_smoke.csv
```

#### Реальные данные (Binance)
```bash
python3 scripts/backtest.py --mode onebar --strategy optimized --data-source real --pair BTC/USDT --timeframe 15m --limit 1500 --smoke --verbose --out artifacts/backtests/onebar_real_smoke.csv
```

### Ограничение по барам

#### 5000 баров
```bash
python3 scripts/backtest.py --mode onebar --strategy optimized --data-source historical --max-bars 5000 --verbose --out artifacts/backtests/onebar_hist_5k.csv
```

#### 10000 баров
```bash
python3 scripts/backtest.py --mode onebar --strategy optimized --data-source historical --max-bars 10000 --verbose --out artifacts/backtests/onebar_hist_10k.csv
```

### С профилированием

```bash
python3 scripts/backtest.py --mode onebar --strategy optimized --data-source historical --max-bars 5000 --verbose --profile --out artifacts/backtests/onebar_hist_5k_profiled.csv
```

### Close режим (быстрый)

```bash
python3 scripts/backtest.py --mode close --strategy optimized --data-source historical --max-bars 2000 --verbose --out artifacts/backtests/close_hist_2k.csv
```

## 📊 Новые флаги

- `--smoke`: Быстрый прогон на 2000 барах
- `--max-bars N`: Ограничение числа баров (приоритетнее --smoke)
- `--verbose`: Подробные логи этапов и прогресс
- `--profile`: Профилирование с сохранением в artifacts/profile_*.prof

## 🔍 Отладка

### Просмотр профиля
```bash
python -m pstats artifacts/profile_YYYYMMDD_HHMMSS.prof
```

### Проверка данных
```bash
# Тест загрузки реальных данных
python3 -c "
from bot.data.real_source import fetch_binance_ohlcv
df = fetch_binance_ohlcv('BTC/USDT', '15m', 10)
print(f'Loaded {len(df)} bars')
print(df.head())
"
```

### Проверка стратегии
```bash
# Тест оптимизированной стратегии
python3 -c "
from bot.strategy.mean_reversion_optimized import MeanReversionOptimized
strategy = MeanReversionOptimized()
print(f'Strategy: {strategy.name()}')
"
```

## ⚡ Ожидаемые времена выполнения

- **Smoke (2000 баров)**: 5-15 секунд
- **5000 баров**: 15-30 секунд  
- **10000 баров**: 30-60 секунд
- **Полный набор (70k+ баров)**: 2-5 минут

## 🐛 Troubleshooting

### Если бэктест зависает
- Используйте `--verbose` для отслеживания прогресса
- Watchdog будет печатать "still working..." каждые 2 минуты
- Используйте `--max-bars` для ограничения размера данных

### Если данные некорректны
- Engine автоматически пропускает бары с NaN/inf значениями
- Проверьте источник данных с помощью тестовых команд выше

### Если стратегия не работает
- Убедитесь, что все зависимости установлены: `pip install numpy pandas ccxt`
- Проверьте логи с `--verbose` для диагностики фильтров
