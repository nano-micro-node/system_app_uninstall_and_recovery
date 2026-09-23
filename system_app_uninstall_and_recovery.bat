@echo off
setlocal enabledelayedexpansion

:: ============================================================
:: Protected packages (NEVER uninstall)
:: ============================================================
set "PROTECTED=com.android.systemui com.android.settings com.google.android.gms com.android.phone com.android.providers.settings com.android.providers.telephony com.google.android.packageinstaller com.android.providers.media com.android.providers.contacts"

:: Check if ADB is available
where adb >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] ADB not found. Add ADB to PATH or install platform-tools.
    pause
    exit /b
)

:: Check device connection
adb devices | findstr /v "List" | findstr /v "^$" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] No device connected. Connect your phone and authorize USB debugging.
    pause
    exit /b
)

:menu
cls
echo ============================================
echo Android System App Manager (ADB)
echo ============================================
echo.
echo 1. Uninstall System App
echo 2. Recover (Restore) System App
echo 3. Exit
echo.
set /p choice="Select option: "

if "%choice%"=="1" goto :uninstall
if "%choice%"=="2" goto :recover
if "%choice%"=="3" goto :cleanup
echo Invalid choice.
timeout /t 2 >nul
goto :menu

:: ============================================================
:: UNINSTALL MODE
:: ============================================================
:uninstall
echo.
echo Fetching system packages...
adb shell pm list packages -s > "%TEMP%\sys_pkgs_raw.txt"

echo.
set /p filter="Enter keyword to filter (e.g., google, camera) or press [ENTER] to show ALL: "

set /a count=0
type nul > "%TEMP%\pkgs_numbered.txt"

:: Parse packages and apply filter
for /f "tokens=2 delims=:" %%p in ('type "%TEMP%\sys_pkgs_raw.txt"') do (
    set "skip=0"
    for %%x in (%PROTECTED%) do (
        if "%%p"=="%%x" set "skip=1"
    )
    if !skip!==0 (
        set "match=1"
        if not "!filter!"=="" (
            echo %%p | findstr /i /c:"!filter!" >nul 2>&1
            if !errorlevel! neq 0 set "match=0"
        )
        if !match!==1 (
            set /a count+=1
            echo !count! %%p >> "%TEMP%\pkgs_numbered.txt"
        )
    )
)

if !count! equ 0 (
    echo.
    echo [!] No matching packages found for "!filter!".
    timeout /t 3 >nul
    goto :menu
)

echo.
echo Total matching system packages: !count!
echo (Protected system apps are hidden)
echo.

echo +------+------------------------------------------+
echo ^| #   ^| Package Name                             ^|
echo +------+------------------------------------------+
for /f "usebackq tokens=1,2 delims= " %%a in ("%TEMP%\pkgs_numbered.txt") do (
    echo ^| %%a ^| %%b
)
echo +------+------------------------------------------+
echo.

set /p uchoice="Enter serial numbers to uninstall (comma separated, e.g. 1,3,5): "

if "%uchoice%"=="" (
    echo No selection made.
    timeout /t 2 >nul
    goto :menu
)

echo.
echo Starting uninstall...
echo.

for %%n in (%uchoice%) do (
    set "pkg="
    for /f "usebackq tokens=1,2 delims= " %%a in ("%TEMP%\pkgs_numbered.txt") do (
        if "%%a"=="%%n" set "pkg=%%b"
    )
    
    if defined pkg (
        set "is_protected=0"
        for %%x in (%PROTECTED%) do (
            if "!pkg!"=="%%x" set "is_protected=1"
        )
        if "!is_protected!"=="1" (
            echo [BLOCKED] !pkg! is a protected system app. Skipped.
        ) else (
            echo Uninstalling [%%n]: !pkg!
            adb shell pm uninstall -k --user 0 !pkg!
        )
    ) else (
        echo [WARN] Serial %%n not found.
    )
    echo.
)

echo ============================================
echo Uninstall Complete.
echo ============================================
echo.
timeout /t 2 >nul
goto :menu

:: ============================================================
:: RECOVER MODE
:: ============================================================
:recover
echo.
echo Scanning for uninstalled (hidden) system apps...
echo.

adb shell pm list packages -u -s > "%TEMP%\all_sys.txt"
adb shell pm list packages -s > "%TEMP%\inst_sys.txt"

type nul > "%TEMP%\all_pkgs.txt"
for /f "tokens=2 delims=:" %%p in ('type "%TEMP%\all_sys.txt"') do (
    echo %%p >> "%TEMP%\all_pkgs.txt"
)

type nul > "%TEMP%\inst_pkgs.txt"
for /f "tokens=2 delims=:" %%p in ('type "%TEMP%\inst_sys.txt"') do (
    echo %%p >> "%TEMP%\inst_pkgs.txt"
)

type nul > "%TEMP%\uninst_pkgs.txt"
for /f "usebackq delims=" %%p in ("%TEMP%\all_pkgs.txt") do (
    findstr /c:"%%p" "%TEMP%\inst_pkgs.txt" >nul 2>&1
    if !errorlevel! neq 0 (
        echo %%p >> "%TEMP%\uninst_pkgs.txt"
    )
)

echo.
set /p rfilter="Enter keyword to filter (e.g., xiaomi, chrome) or press [ENTER] to show ALL: "

set /a count=0
type nul > "%TEMP%\uninst_numbered.txt"
for /f "usebackq delims=" %%p in ("%TEMP%\uninst_pkgs.txt") do (
    set "match=1"
    if not "!rfilter!"=="" (
        echo %%p | findstr /i /c:"!rfilter!" >nul 2>&1
        if !errorlevel! neq 0 set "match=0"
    )
    if !match!==1 (
        set /a count+=1
        echo !count! %%p >> "%TEMP%\uninst_numbered.txt"
    )
)

if !count! equ 0 (
    echo.
    echo No matching uninstalled system apps found.
    echo.
    timeout /t 3 >nul
    goto :menu
)

echo.
echo Found !count! matching uninstalled system app(s):
echo.
echo +------+------------------------------------------+
echo ^| #   ^| Package Name                             ^|
echo +------+------------------------------------------+
for /f "usebackq tokens=1,2 delims= " %%a in ("%TEMP%\uninst_numbered.txt") do (
    echo ^| %%a ^| %%b
)
echo +------+------------------------------------------+
echo.

echo Options:
echo - Enter specific serial numbers (e.g. 1,3,5)
echo - Type "all" to restore ALL listed items
echo.
set /p rchoice="Your choice: "

if /i "%rchoice%"=="all" (
    echo.
    echo Restoring ALL listed apps...
    echo.
    for /f "usebackq tokens=1,2 delims= " %%a in ("%TEMP%\uninst_numbered.txt") do (
        echo Restoring [%%a]: %%b
        adb shell cmd package install-existing %%b
        echo.
    )
) else (
    if "%rchoice%" his=="" (
        echo No selection made.
        timeout /t 2 >nul
        goto :menu
    )
    echo.
    echo Restoring selected apps...
    echo.
    
    for %%n in (%rchoice%) do (
        set "pkg="
        for /f "usebackq tokens=1,2 delims= " %%a in ("%TEMP%\uninst_numbered.txt") do (
            if "%%a"=="%%n" set "pkg=%%b"
        )
        if defined pkg (
            echo Restoring [%%n]: !pkg!
            adb shell cmd package install-existing !pkg!
            echo.
        ) else (
            echo [WARN] Serial %%n not found.
            echo.
        )
    )
)

echo ============================================
echo Recovery Complete.
echo ============================================
echo.
timeout /t 2 >nul
goto :menu

:: ============================================================
:: CLEANUP
:: ============================================================
:cleanup
del "%TEMP%\sys_pkgs_raw.txt" 2>nul
del "%TEMP%\pkgs_numbered.txt" 2>nul
del "%TEMP%\all_sys.txt" 2>nul
del "%TEMP%\inst_sys.txt" 2>nul
del "%TEMP%\all_pkgs.txt" 2>nul
del "%TEMP%\inst_pkgs.txt" 2>nul
del "%TEMP%\uninst_pkgs.txt" 2>nul
del "%TEMP%\uninst_numbered.txt" 2>nul
endlocal
exit /b