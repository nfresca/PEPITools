@echo off
setlocal EnableDelayedExpansion

python --version >nul 2>&1
if not errorlevel 1 goto :launch

echo Instalando Python (solo la primera vez)...
winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements >nul 2>&1

for /f "usebackq tokens=2,*" %%A in (
    `reg query "HKCU\Environment" /v Path 2^>nul`
) do set "USERPATH=%%B"
for /f "usebackq tokens=2,*" %%A in (
    `reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul`
) do set "SYSPATH=%%B"
set "PATH=!USERPATH!;!SYSPATH!"

python --version >nul 2>&1
if errorlevel 1 (
    powershell -NoProfile -Command ^
        "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Python no pudo instalarse. Instalalo desde python.org y marcá Add to PATH.', 'PEPITools', 'OK', 'Error')"
    exit /b 1
)

:launch
start "" pythonw "%~dp0transmiturf.py" 2>nul
if errorlevel 1 start "" python "%~dp0transmiturf.py"
