# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — SIGNIT single-file Windows .exe.

Build on Windows:  pyinstaller production/signit.spec
Output: dist/SIGNIT.exe (console-less GUI).

Bundles the 4 demo captures (assets/demo) so Sample analysis works
offline. ml/models/signit_cnn.onnx is bundled WHEN PRESENT — train it
first (.train-venv, see README) for a live CNN vote in the .exe; the app
falls back to pending-vote when absent.
Hidden imports cover everything PyInstaller cannot see statically
(dynamic voters/backends): Qt, plotting, DSP/ML, FEC optionals.
Proven only via the windows-build CI job; iterate on its artifact.
"""
import glob
import os

SPEC_DIR = os.path.dirname(os.path.abspath(SPEC))
PROD_DIR = SPEC_DIR  # spec lives in production/
ENTRY = os.path.join(PROD_DIR, "app", "main.py")

demo_datas = [(p, "assets/demo") for p in glob.glob(os.path.join(PROD_DIR, "assets", "demo", "*.json"))]
model_datas = [(p, os.path.join("ml", "models")) for p in glob.glob(os.path.join(PROD_DIR, "ml", "models", "*.onnx"))]

a = Analysis(
    [ENTRY],
    pathex=[PROD_DIR],
    binaries=[],
    datas=demo_datas + model_datas,
    hiddenimports=[
        "app.mainwindow",
        "app.demo_store",
        "app.widgets.file_panel",
        "app.widgets.results_tabs",
        "app.widgets.plots",
        "app.widgets.report_card",
        "app.widgets.bits_view",
        "app.widgets.comparator",
        "app.widgets.mission_log",
        "engine.ingest",
        "engine.estimators",
        "engine.demod",
        "engine.fec",
        "ml.cumulants",
        "ml.ensemble",
        "ml.cnn_onnx",
        "ml.synth",
        "pyqtgraph",
        "qt_material",
        "numpy",
        "scipy",
        "scipy.signal",
        "scipy.io.wavfile",
        "sklearn",
        "sklearn.ensemble",
        "onnxruntime",
        "numba",
        "pyfftw",
        "soundfile",
        "matplotlib",
        "galois",
        "commpy",
        "pyldpc",
        "fpdf",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["torch", "torchvision", "torchaudio", "onnx", "pytest", "tkinter"],
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
