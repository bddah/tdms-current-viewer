# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas_pg, binaries_pg, hiddenimports_pg = collect_all('pyqtgraph')
datas_scipy, binaries_scipy, hiddenimports_scipy = collect_all('scipy')
datas_nptdms, binaries_nptdms, hiddenimports_nptdms = collect_all('nptdms')

a = Analysis(
    ['src/app.py'],
    pathex=['src'],
    binaries=binaries_pg + binaries_scipy + binaries_nptdms,
    datas=datas_pg + datas_scipy + datas_nptdms,
    hiddenimports=hiddenimports_pg + hiddenimports_scipy + hiddenimports_nptdms + [
        # pyqtgraph Qt backend -- imported dynamically so PyInstaller misses it
        'pyqtgraph.Qt.PySide6',
        'pyqtgraph.exporters',
        # PySide6 optional modules used by pyqtgraph exporters / widgets
        'PySide6.QtSvg',
        'PySide6.QtPrintSupport',
        'PySide6.QtOpenGL',
        'PySide6.QtOpenGLWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TdmsViewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    windowed=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TdmsViewer',
)
