## Общие сведения

Программа предназначена для импорта TDMS файлов с построением графиков из импортированных данных и их минимальной обработкой. Программа распространяется в виде python-модуля, содержащего виджет для использования в среде jupyter lab.

---

## Нативное Windows-приложение (Desktop GUI)

Полноценное настольное приложение на PySide6 + pyqtgraph. Не требует браузера и интернета.

### Возможности

- Открытие `.tdms`-файлов через диалог (Ctrl+O) с отображением прогресса загрузки
- Дерево групп и каналов с чекбоксами для множественного выбора
- Построение графиков: одиночный канал (двойной клик) или несколько выбранных каналов
- Параметры обработки: усреднение (Savitzky-Golay), интегрирование, вычитание среднего
- Интерактивный график: зум, панорамирование, сброс (pyqtgraph)
- Отображение координат курсора в строке состояния
- Экспорт данных в CSV (Ctrl+E)
- Сохранение графика в PNG (Ctrl+S)
- Запоминание последней открытой директории

### Установка зависимостей

```bash
pip install -r requirements_desktop.txt
```

### Запуск

```bash
python src/app.py
```

### Сборка EXE-файла для Windows (PyInstaller)

```bat
build_windows.bat
```

Или вручную:

```bash
pip install -r requirements_desktop.txt
pyinstaller tdms_desktop.spec
```

Готовый каталог появится в `dist\TdmsViewer\`. Запустите `dist\TdmsViewer\TdmsViewer.exe`.

### Структура проекта (desktop)

```
src/
  app.py                        # Точка входа
  ui/
    main_window.py              # Главное окно (меню, тулбар, сплиттер)
    channel_tree.py             # Дерево групп/каналов
    plot_panel.py               # Панель с графиком и элементами управления
    dialogs.py                  # Диалоги ошибок и прогресса
  services/
    tdms_reader.py              # Чтение TDMS-файлов
    exporter.py                 # Экспорт CSV и PNG
  plotting/
    plot_widget.py              # Виджет графика (pyqtgraph)
requirements_desktop.txt
tdms_desktop.spec               # Конфигурация PyInstaller
build_windows.bat               # Скрипт сборки
```

### Известные ограничения

- Ось X использует числовые значения; для временнóй оси datetime64 значения конвертируются в секунды (Unix epoch)
- Сборка EXE тестировалась с PyInstaller 6.x на Python 3.11+
- Для работы на Windows без Python запустите `dist\TdmsViewer\TdmsViewer.exe`

---

## Локальное web-приложение

Также доступен локально хостируемый web-интерфейс для чтения и построения графиков по TDMS файлам.

Запуск из Python:

```python
import tdms_plot
tdms_plot.run_local_web_app(host='127.0.0.1', port=8000)
```

Запуск из командной строки с возможностью изменить хост и порт:

```bash
python tdms_plot.py --host 127.0.0.1 --port 8000
# или на другом порту:
python tdms_plot.py --port 9090
```

После запуска откройте в браузере:

`http://127.0.0.1:8000`

## Создание исполняемого EXE-файла (Windows)

Для запуска приложения без установки Python используйте [PyInstaller](https://pyinstaller.org/).

### 1. Установите зависимости

```bash
pip install pyinstaller nptdms numpy plotly scipy ipywidgets
```

### 2. Создайте точку входа

Создайте файл `tdms_server.py` рядом с `tdms_plot.py`:

```python
import tdms_plot
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='TDMS local web viewer')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    print(f'Opening http://{args.host}:{args.port} ...')
    import webbrowser, threading
    threading.Timer(1.0, lambda: webbrowser.open(f'http://{args.host}:{args.port}')).start()
    tdms_plot.run_local_web_app(host=args.host, port=args.port)
```

### 3. Соберите EXE

```bash
pyinstaller --onefile --name tdms_viewer tdms_server.py
```

Готовый файл появится в папке `dist/tdms_viewer.exe`.

### 4. Запуск

Просто дважды щёлкните `tdms_viewer.exe` — сервер запустится, и браузер откроется автоматически по адресу `http://127.0.0.1:8000`.

Для изменения порта запустите из командной строки:

```bash
tdms_viewer.exe --port 9090
```
