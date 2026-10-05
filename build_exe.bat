@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

title MultiGitHubGUI - Build

echo ============================================================
echo   MultiGitHubGUI - 1-Datei-EXE Build
echo ============================================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (
    set "PY=py"
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo [FEHLER] Python wurde auf DIESEM BUILD-PC nicht gefunden.
        echo.
        echo Python wird nur zum Erstellen der EXE benoetigt.
        echo Auf dem Ziel-PC ist spaeter KEIN Python erforderlich.
        pause
        exit /b 1
    )
    set "PY=python"
)

echo [1/7] Build-Pakete installieren/aktualisieren...
%PY% -m pip install --upgrade pip
if errorlevel 1 goto :fail
%PY% -m pip install --upgrade pyinstaller customtkinter
if errorlevel 1 goto :fail

echo.
echo [2/7] Build-Verzeichnisse vorbereiten...

if not exist "build_tmp" mkdir "build_tmp"

if exist "vendor" rmdir /s /q "vendor"
mkdir "vendor\gh"
mkdir "vendor\mingit"

echo.
echo [3/7] GitHub CLI vorbereiten...

set "USE_GH_CACHE=N"

if exist "build_tmp\gh.zip" (
    echo.
    echo Vorhandener GitHub-CLI-Download gefunden:
    echo   build_tmp\gh.zip
    choice /C JN /N /M "Vorhandene Datei verwenden? [J/N]: "
    if errorlevel 2 (
        set "USE_GH_CACHE=N"
    ) else (
        set "USE_GH_CACHE=J"
    )
)

if /I "!USE_GH_CACHE!"=="N" (
    echo.
    echo Aktuelle stabile GitHub CLI herunterladen...
    if exist "build_tmp\gh.zip" del /q "build_tmp\gh.zip"

    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
      "$ErrorActionPreference='Stop';" ^
      "$arch=$env:PROCESSOR_ARCHITECTURE;" ^
      "if ($arch -eq 'ARM64') {$ghArch='arm64'} else {$ghArch='amd64'};" ^
      "$headers=@{'User-Agent'='MultiGitHubGUI-Build'};" ^
      "$rel=Invoke-RestMethod -Headers $headers -Uri 'https://api.github.com/repos/cli/cli/releases/latest';" ^
      "$asset=$rel.assets | Where-Object {$_.name -match ('^gh_.*_windows_' + $ghArch + '\.zip$')} | Select-Object -First 1;" ^
      "if (-not $asset) {throw 'Passendes GitHub-CLI ZIP nicht gefunden.'};" ^
      "Write-Host ('      ' + $asset.name);" ^
      "Invoke-WebRequest -Headers $headers -Uri $asset.browser_download_url -OutFile 'build_tmp\gh.zip';"

    if errorlevel 1 goto :fail
) else (
    echo Vorhandener GitHub-CLI-Download wird verwendet.
)

if exist "build_tmp\gh" rmdir /s /q "build_tmp\gh"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "Expand-Archive -Force 'build_tmp\gh.zip' 'build_tmp\gh';" ^
  "$exe=Get-ChildItem 'build_tmp\gh' -Recurse -Filter 'gh.exe' | Select-Object -First 1;" ^
  "if (-not $exe) {throw 'gh.exe wurde im Archiv nicht gefunden.'};" ^
  "Copy-Item $exe.FullName 'vendor\gh\gh.exe' -Force;"

if errorlevel 1 (
    echo.
    echo [HINWEIS] Der vorhandene GitHub-CLI-Cache scheint unbrauchbar zu sein.
    echo Bitte Build erneut starten und beim Cache "N" waehlen.
    goto :fail
)

echo.
echo [4/7] MinGit vorbereiten...

set "USE_MINGIT_CACHE=N"

if exist "build_tmp\mingit.zip" (
    echo.
    echo Vorhandener MinGit-Download gefunden:
    echo   build_tmp\mingit.zip
    choice /C JN /N /M "Vorhandene Datei verwenden? [J/N]: "
    if errorlevel 2 (
        set "USE_MINGIT_CACHE=N"
    ) else (
        set "USE_MINGIT_CACHE=J"
    )
)

if /I "!USE_MINGIT_CACHE!"=="N" (
    echo.
    echo Aktuelles stabiles MinGit herunterladen...
    if exist "build_tmp\mingit.zip" del /q "build_tmp\mingit.zip"

    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
      "$ErrorActionPreference='Stop';" ^
      "$arch=$env:PROCESSOR_ARCHITECTURE;" ^
      "if ($arch -eq 'ARM64') {$pattern='^MinGit-.*-arm64\.zip$'} else {$pattern='^MinGit-.*-64-bit\.zip$'};" ^
      "$headers=@{'User-Agent'='MultiGitHubGUI-Build'};" ^
      "$rel=Invoke-RestMethod -Headers $headers -Uri 'https://api.github.com/repos/git-for-windows/git/releases/latest';" ^
      "$asset=$rel.assets | Where-Object {$_.name -match $pattern -and $_.name -notmatch 'busybox'} | Select-Object -First 1;" ^
      "if (-not $asset) {throw 'Passendes MinGit ZIP nicht gefunden.'};" ^
      "Write-Host ('      ' + $asset.name);" ^
      "Invoke-WebRequest -Headers $headers -Uri $asset.browser_download_url -OutFile 'build_tmp\mingit.zip';"

    if errorlevel 1 goto :fail
) else (
    echo Vorhandener MinGit-Download wird verwendet.
)

if exist "build_tmp\mingit_extract" rmdir /s /q "build_tmp\mingit_extract"
mkdir "build_tmp\mingit_extract"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "Expand-Archive -Force 'build_tmp\mingit.zip' 'build_tmp\mingit_extract';" ^
  "if (-not (Test-Path 'build_tmp\mingit_extract\cmd\git.exe')) {throw 'git.exe wurde im MinGit-Archiv nicht gefunden.'};" ^
  "Copy-Item 'build_tmp\mingit_extract\*' 'vendor\mingit' -Recurse -Force;"

if errorlevel 1 (
    echo.
    echo [HINWEIS] Der vorhandene MinGit-Cache scheint unbrauchbar zu sein.
    echo Bitte Build erneut starten und beim Cache "N" waehlen.
    goto :fail
)

echo.
echo [5/7] Python-Datei und Icon pruefen...
if not exist "MultiGitHubGUI.ico" (
    echo [FEHLER] MultiGitHubGUI.ico wurde nicht gefunden.
    goto :fail
)
%PY% -m py_compile MultiGitHubGUI.py
if errorlevel 1 goto :fail

echo.
echo [6/7] Build fuer schnelleren Programmstart vorbereiten...
echo        CustomTkinter-Ressourcen werden nur einmal eingebunden.
echo        Das Laufzeit-Icon steckt bereits als Base64 in MultiGitHubGUI.py.
echo.

echo.
echo [7/7] Einzelne EXE bauen...

if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "MultiGitHubGUI.spec" del /q "MultiGitHubGUI.spec"

%PY% -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --noupx ^
  --name "MultiGitHubGUI" ^
  --icon "MultiGitHubGUI.ico" ^
  --add-data "vendor\gh;vendor\gh" ^
  --add-data "vendor\mingit;vendor\mingit" ^
  --collect-data customtkinter ^
  MultiGitHubGUI.py

if errorlevel 1 goto :fail

echo.
echo ============================================================
echo   FERTIG
echo ============================================================
echo.
echo EXE:
echo   %CD%\dist\MultiGitHubGUI.exe
echo.
echo Download-Cache bleibt erhalten:
echo   %CD%\build_tmp
echo.
echo Auf dem Ziel-PC werden weder Python noch Git noch gh benoetigt.
echo Benutzer-Einstellungen liegen unter %%APPDATA%%\MultiGitHubGUI.
echo GitHub-Zugangsdaten werden nicht von der App gespeichert.
echo.
pause
exit /b 0

:fail
echo.
echo ============================================================
echo   BUILD FEHLGESCHLAGEN
echo ============================================================
echo.
echo Bitte die Fehlermeldung oben pruefen.
echo.
pause
exit /b 1
