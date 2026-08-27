import PyInstaller.__main__
import os

if __name__ == '__main__':
    PyInstaller.__main__.run([
        'app.py',
        '--name=DC4Tool',
        '--onefile',
        '--add-data=templates;templates',
        '--add-data=static;static',
        '--hidden-import=uvicorn',
        '--hidden-import=pandas',
        '--hidden-import=openpyxl',
        '--hidden-import=engineio.async_drivers.asgi',  # Sometimes needed for uvicorn/starlette
        '--icon=adsdad.ico',
        '--noconfirm',
        '--clean',
    ])
