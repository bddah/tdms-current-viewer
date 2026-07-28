# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files


datas = collect_data_files('pyqtgraph')


a = Analysis(
    ['src/app.py'],
    pathex=['src'],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'nptdms',
        'scipy.signal',
        'scipy.integrate',
        'pyqtgraph',
        'pyqtgraph.exporters',
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TdmsViewer',
)
