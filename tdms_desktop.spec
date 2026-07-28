# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas_pg, binaries_pg, hiddenimports_pg = collect_all('pyqtgraph')

a = Analysis(
    ['src/app.py'],
    pathex=['src'],
    binaries=binaries_pg,
    datas=datas_pg,
    hiddenimports=hiddenimports_pg + [
        # pyqtgraph Qt backend -- imported dynamically so PyInstaller misses it
        'pyqtgraph.Qt.PySide6',
        'pyqtgraph.exporters',
        # PySide6 optional modules used by pyqtgraph exporters / widgets
        'PySide6.QtSvg',
        'PySide6.QtPrintSupport',
        'PySide6.QtOpenGL',
        'PySide6.QtOpenGLWidgets',
        # nptdms and its internal modules
        'nptdms',
        'nptdms.tdms',
        'nptdms.tdms_file',
        'nptdms.read_file',
        'nptdms.common',
        'nptdms.types',
        'nptdms.export',
        # scipy sub-modules
        'scipy.signal',
        'scipy.integrate',
        'scipy.special._ufuncs',
        'scipy.special._ufuncs_cxx',
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
