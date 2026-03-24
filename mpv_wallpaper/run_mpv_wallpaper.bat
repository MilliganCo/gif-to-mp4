@echo off
:: Запуск MPV как фоновое видео. Плейлист = playlist.m3u рядом со скриптом.

cd /d "%~dp0"
set "PLAYLIST=%~dp0playlist.m3u"

:: Поиск mpv.exe
set "MPV="
where mpv >nul 2>&1 && set "MPV=mpv"
if "%MPV%"=="" if exist "C:\mpv\mpv.exe" set "MPV=C:\mpv\mpv.exe"
if "%MPV%"=="" if exist "%LOCALAPPDATA%\Programs\mpv\mpv.exe" set "MPV=%LOCALAPPDATA%\Programs\mpv\mpv.exe"
if "%MPV%"=="" if exist "%ProgramFiles%\mpv\mpv.exe" set "MPV=%ProgramFiles%\mpv\mpv.exe"
if "%MPV%"=="" if exist "%USERPROFILE%\scoop\shims\mpv.exe" set "MPV=%USERPROFILE%\scoop\shims\mpv.exe"
:: Подпапка C:\mpv\ (если распаковали 7z с папкой внутри)
if "%MPV%"=="" for /d %%D in ("C:\mpv\*") do if exist "%%D\mpv.exe" set "MPV=%%D\mpv.exe"

if "%MPV%"=="" (
    echo MPV не найден.
    echo.
    echo Установи MPV одним из способов:
    echo   1. winget install mpv.mpv
    echo   2. Скачай с https://github.com/shinchiro/mpv-winbuild-cmake/releases
    echo      Распакуй в C:\mpv\ и положи mpv.exe туда.
    echo.
    echo Либо укажи путь в run_mpv_wallpaper.bat: set "MPV=путь\к\mpv.exe"
    timeout /t 8
    exit /b 1
)

if not exist "%PLAYLIST%" (
    echo Плейлист не найден: %PLAYLIST%
    echo 1. Запусти make_playlist.bat для папки с видео
    echo 2. Укажи путь к playlist.m3u в этом файле
    timeout /t 5
    exit /b 1
)

start "" /D "%~dp0" "%MPV%" --loop=inf --fullscreen --player-operation-mode=pseudo-gui --no-ontop "%~dp0playlist.m3u"
