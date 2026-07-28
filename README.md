## Общие сведения

Программа предназначена для импорта TDMS файлов с построением графиков из импортированных данных и их минимальной обработкой. Программа распространяется в виде python-модуля, содержащего виджет для использования в среде jupyter lab.

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
