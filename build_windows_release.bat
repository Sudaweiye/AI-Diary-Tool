@echo off
setlocal
cd /d "%~dp0"

echo [1/3] Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [2/3] Building Windows executable with PyInstaller...
pyinstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --onedir ^
  --name CodexDiaryTool ^
  --collect-all faster_whisper ^
  --hidden-import tkinter ^
  --hidden-import tkinter.ttk ^
  --hidden-import tkinter.scrolledtext ^
  app.py

if errorlevel 1 (
  echo Build failed.
  pause
  exit /b 1
)

echo [3/3] Ensuring runtime output directory exists...
if not exist "dist\\CodexDiaryTool\\outputs" mkdir "dist\\CodexDiaryTool\\outputs"

echo.
echo Build completed:
echo   %cd%\\dist\\CodexDiaryTool\\CodexDiaryTool.exe
pause
