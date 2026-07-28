## Общие сведения

Программа предназначена для импорта TDMS файлов с построением графиков из импортированных данных и их минимальной обработкой. Программа распространяется в виде python-модуля, содержащего виджет для использования в среде jupyter lab.

![widget screenshot](imgs/widget_screenshot.png)

## Установка ПО и зависимостей

- Установить пакет miniforge
https://github.com/conda-forge/miniforge

- Клонировать/скачать данный репозиторий:
    - либо `git clone https://git.labfer.link/akhmatkhanov/TDMS_plot.git`
    - либо "Download ZIP" в доп. меню синей кнопки "<>Code" в верхней части страницы

- Создать и активировать новый environment в conda:
```shell
conda create -n tdms_plot
conda activate tdms_plot
conda install conda
```

- Установить пакеты в новый environment:
```shell
conda install numpy ipython matplotlib jupyterlab ipywidgets plotly nptdms scipy
```

## Использование модуля
1. Импортировать модуль
2. Запустить из него функцию построения основного виджета main_widget()

Минимальный пример для использования:

```python
import tdms_plot
tdms_plot.main_widget()
```

## Локальное web-приложение

Также доступен локально хостируемый web-интерфейс для чтения и построения графиков по TDMS файлам.

Запуск:

```python
import tdms_plot
tdms_plot.run_local_web_app(host='127.0.0.1', port=8000)
```

После запуска откройте в браузере:

`http://127.0.0.1:8000`
