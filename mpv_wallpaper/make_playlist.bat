@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: Создаёт playlist.m3u из всех видео/GIF в выбранной папке
:: Запуск: перетащи папку на make_playlist.bat или укажи путь

set "FOLDER=%~1"
if "%FOLDER%"=="" (
    echo Выбери папку с видео/GIF...
    set "FOLDER=%cd%"
)

if not exist "%FOLDER%" (
    echo Папка не найдена: %FOLDER%
    pause
    exit /b 1
)

set "OUT=%FOLDER%\playlist.m3u"
echo #EXTM3U > "%OUT%"

for %%F in ("%FOLDER%\*.mp4" "%FOLDER%\*.webm" "%FOLDER%\*.gif" "%FOLDER%\*.mkv" "%FOLDER%\*.avi") do (
    echo %%~fF >> "%OUT%"
)

echo Создан: %OUT%
echo.
echo Запуск: mpv --loop --fullscreen --player-operation-mode=pseudo-gui "%OUT%"
pause
