#!/usr/bin/env python3
"""
Автоматическая генерация TODO.md на основе анализа кода, результатов бэктестов и тестов.

Источники задач:
- Маркеры TODO/FIXME/NOTE в коде
- Анализ CSV результатов бэктестов
- JUnit отчёты тестов
"""

import csv
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def scan_code_markers(project_root: Path) -> List[Tuple[str, int, str]]:
    """
    Сканирует все файлы проекта на наличие маркеров TODO/FIXME/NOTE.
    
    Args:
        project_root: Корневая папка проекта
        
    Returns:
        Список кортежей (файл, строка, текст)
    """
    markers = []
    extensions = {'.py', '.md', '.yml', '.yaml', '.sh'}
    
    # Паттерн для поиска маркеров
    pattern = re.compile(r'(TODO|FIXME|NOTE):\s*(.+)', re.IGNORECASE)
    
    for file_path in project_root.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in extensions:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        match = pattern.search(line)
                        if match:
                            marker_type = match.group(1).upper()
                            text = match.group(2).strip()
                            relative_path = file_path.relative_to(project_root)
                            markers.append((str(relative_path), line_num, f"{marker_type}: {text}"))
            except Exception as e:
                print(f"Ошибка чтения файла {file_path}: {e}")
                continue
    
    return markers


def find_backtest_csvs(project_root: Path) -> List[Path]:
    """
    Находит все CSV файлы с результатами бэктестов.
    
    Args:
        project_root: Корневая папка проекта
        
    Returns:
        Список путей к CSV файлам
    """
    csv_files = []
    search_paths = [
        project_root / "artifacts" / "backtests",
        project_root / "results" / "backtests", 
        project_root / "artifacts",
        project_root / "user_data"  # Добавляем папку с результатами
    ]
    
    for search_path in search_paths:
        if search_path.exists():
            for csv_file in search_path.glob("*.csv"):
                csv_files.append(csv_file)
    
    # Сортируем по времени модификации (новые сначала)
    csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    return csv_files


def analyze_backtests(csv_files: List[Path]) -> Tuple[List[Dict], List[Dict]]:
    """
    Анализирует CSV файлы с результатами бэктестов.
    
    Args:
        csv_files: Список путей к CSV файлам
        
    Returns:
        Кортеж (алерты, лучшие результаты)
    """
    alerts = []
    best_results = []
    
    for csv_file in csv_files:
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Пропускаем строки без данных
                    if not row.get('mode') or not row.get('trades'):
                        continue
                    
                    # Извлекаем метрики
                    try:
                        trades = int(row.get('trades', 0))
                        equity = float(row.get('final_equity', 0))
                        winrate = float(row.get('win_rate', 0)) if row.get('win_rate') else 0
                        pf = float(row.get('pf', 0)) if row.get('pf') else 0
                        dd = float(row.get('max_dd', 0)) if row.get('max_dd') else 0
                        return_pct = float(row.get('return_pct', 0)) if row.get('return_pct') else 0
                        
                        # Проверяем условия для алертов
                        if pf < 1.1 and pf > 0:
                            alerts.append({
                                'file': csv_file.name,
                                'mode': row.get('mode', 'unknown'),
                                'pf': pf,
                                'reason': f'Низкий PF: {pf:.3f}'
                            })
                        
                        if winrate < 0.45 and winrate > 0:
                            alerts.append({
                                'file': csv_file.name,
                                'mode': row.get('mode', 'unknown'),
                                'winrate': winrate,
                                'reason': f'Низкая win rate: {winrate:.1%}'
                            })
                        
                        if dd > 0.3:
                            alerts.append({
                                'file': csv_file.name,
                                'mode': row.get('mode', 'unknown'),
                                'dd': dd,
                                'reason': f'Высокий drawdown: {dd:.1%}'
                            })
                        
                        if trades == 0:
                            alerts.append({
                                'file': csv_file.name,
                                'mode': row.get('mode', 'unknown'),
                                'trades': trades,
                                'reason': 'Нет сделок'
                            })
                        
                        # Собираем лучшие результаты по PF
                        if pf > 1.0:
                            best_results.append({
                                'file': csv_file.name,
                                'mode': row.get('mode', 'unknown'),
                                'pf': pf,
                                'equity': equity,
                                'trades': trades,
                                'winrate': winrate,
                                'dd': dd,
                                'return_pct': return_pct
                            })
                    
                    except (ValueError, TypeError) as e:
                        print(f"Ошибка парсинга строки в {csv_file}: {e}")
                        continue
        
        except Exception as e:
            print(f"Ошибка чтения CSV файла {csv_file}: {e}")
            continue
    
    # Сортируем лучшие результаты по PF
    best_results.sort(key=lambda x: x['pf'], reverse=True)
    
    return alerts, best_results


def parse_junit(junit_path: Path) -> List[Dict]:
    """
    Парсит JUnit XML файл и извлекает ошибки и фейлы.
    
    Args:
        junit_path: Путь к JUnit XML файлу
        
    Returns:
        Список ошибок и фейлов
    """
    failures: list[dict] = []
    
    if not junit_path.exists():
        return failures
    
    try:
        tree = ET.parse(junit_path)
        root = tree.getroot()
        
        # Обрабатываем тест-кейсы
        for testcase in root.findall('.//testcase'):
            name = testcase.get('name', 'unknown')
            classname = testcase.get('classname', 'unknown')
            
            # Проверяем на ошибки
            error = testcase.find('error')
            if error is not None:
                message = error.get('message', 'Ошибка')
                failures.append({
                    'type': 'ERROR',
                    'test': f"{classname}.{name}",
                    'message': message
                })
            
            # Проверяем на фейлы
            failure = testcase.find('failure')
            if failure is not None:
                message = failure.get('message', 'Фейл')
                failures.append({
                    'type': 'FAILURE',
                    'test': f"{classname}.{name}",
                    'message': message
                })
    
    except Exception as e:
        print(f"Ошибка парсинга JUnit файла {junit_path}: {e}")
    
    return failures


def render_markdown(
    code_markers: List[Tuple[str, int, str]],
    backtest_alerts: List[Dict],
    best_results: List[Dict],
    test_failures: List[Dict]
) -> str:
    """
    Генерирует Markdown содержимое для TODO.md.
    
    Args:
        code_markers: Маркеры из кода
        backtest_alerts: Алерты из бэктестов
        best_results: Лучшие результаты
        test_failures: Ошибки тестов
        
    Returns:
        Markdown содержимое
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    lines = [
        f"# TODO (auto-generated) — {timestamp}",
        "",
        "## 🚨 Test Failures",
        ""
    ]
    
    if test_failures:
        for failure in test_failures:
            lines.append(f"- [ ] **{failure['type']}**: {failure['test']} — {failure['message']}")
    else:
        lines.append("- [ ] Нет ошибок тестов")
    
    lines.extend([
        "",
        "## 📉 Backtest Alerts",
        ""
    ])
    
    if backtest_alerts:
        for alert in backtest_alerts:
            lines.append(f"- [ ] **{alert['mode']}** ({alert['file']}): {alert['reason']}")
    else:
        lines.append("- [ ] Нет алертов бэктестов")
    
    lines.extend([
        "",
        "## 📈 Suggestions from Results",
        ""
    ])
    
    if best_results:
        # Показываем топ-3 лучших результата
        for i, result in enumerate(best_results[:3], 1):
            lines.append(f"- [ ] **#{i}** {result['mode']} (PF: {result['pf']:.3f}, Equity: {result['equity']:.0f}, Trades: {result['trades']})")
    else:
        lines.append("- [ ] Нет данных для анализа")
    
    lines.extend([
        "",
        "## 🛠 Code Markers (TODO/FIXME/NOTE)",
        ""
    ])
    
    if code_markers:
        for file_path, line_num, text in code_markers:
            lines.append(f"- [ ] `{file_path}:{line_num}` — {text}")
    else:
        lines.append("- [ ] Нет маркеров в коде")
    
    lines.append("")
    
    return "\n".join(lines)


def main():
    """Основная функция скрипта."""
    # Определяем корневую папку проекта
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print(f"Анализ проекта: {project_root}")
    print("Скрипт запущен успешно")
    
    # 1. Сканируем маркеры в коде
    print("Сканирование маркеров в коде...")
    code_markers = scan_code_markers(project_root)
    print(f"Найдено маркеров: {len(code_markers)}")
    
    # 2. Находим CSV файлы с результатами бэктестов
    print("Поиск CSV файлов с результатами бэктестов...")
    csv_files = find_backtest_csvs(project_root)
    print(f"Найдено CSV файлов: {len(csv_files)}")
    
    # 3. Анализируем результаты бэктестов
    print("Анализ результатов бэктестов...")
    backtest_alerts, best_results = analyze_backtests(csv_files)
    print(f"Найдено алертов: {len(backtest_alerts)}")
    print(f"Найдено лучших результатов: {len(best_results)}")
    
    # 4. Парсим JUnit отчёты
    print("Поиск JUnit отчётов...")
    junit_paths = [
        project_root / "artifacts" / "tests" / "junit.xml",
        project_root / "reports" / "junit.xml"
    ]
    
    test_failures: list[dict] = []
    for junit_path in junit_paths:
        if junit_path.exists():
            print(f"Парсинг JUnit файла: {junit_path}")
            failures: list[dict] = parse_junit(junit_path)
            test_failures.extend(failures)
    
    print(f"Найдено ошибок тестов: {len(test_failures)}")
    
    # 5. Генерируем Markdown
    print("Генерация TODO.md...")
    markdown_content = render_markdown(
        code_markers, backtest_alerts, best_results, test_failures
    )
    
    # 6. Записываем в файл
    todo_path = project_root / "TODO.md"
    try:
        with open(todo_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"TODO.md успешно создан: {todo_path}")
    except Exception as e:
        print(f"Ошибка записи TODO.md: {e}")
        return 1
    
    # 7. Выводим статистику
    print("\n=== Статистика ===")
    print(f"Маркеры в коде: {len(code_markers)}")
    print(f"CSV файлы: {len(csv_files)}")
    print(f"Алерты бэктестов: {len(backtest_alerts)}")
    print(f"Лучшие результаты: {len(best_results)}")
    print(f"Ошибки тестов: {len(test_failures)}")
    
    return 0


if __name__ == "__main__":
    exit(main())