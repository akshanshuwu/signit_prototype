# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — SIGNIT single-file Windows .exe (Phase 0 skeleton).

Build on Windows:  pyinstaller production/signit.spec
Output: dist/SIGNIT.exe (console-less GUI).
Phase 8 hardens this (hidden imports for pyqtgraph/onnx/scipy, data files,
version info, icon). Phase 0 only needs a valid, building spec.
"""
import os

SPEC_DIR = os.path.dirname(os.path.abspath(SPEC))
PROD_DIR = SPEC_DIR  # spec lives in production/
ENTRY = os.path.join(PROD_DIR, "app", "main.py")

a = Analysis(
    [ENTRY],
    pathex=[PROD_DIR],
    binaries=[],
    datas=[],
    hiddenimports=["app.mainwindow", "pyqtgraph"],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="SIGNIT",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
