@echo off
setlocal enabledelayedexpansion

:: ========================================================
:: Network Scanner & Scope Splitter
:: Version: 1.0
:: ========================================================

:: Configuration
set "INPUT_FILE=scope.txt"
set "OUTPUT_DIR=output"
set "IPS_PER_FILE=20"
set "SUBNETS_PER_FILE=3"

:: Clear screen and show banner
cls
echo ========================================================
echo             Network Scanner & Scope Splitter
echo                     Version 1.0
echo ========================================================
echo.

:: Check if input file exists
if not exist "%INPUT_FILE%" (
    echo [ERROR] scope.txt not found!
    echo.
    echo Create scope.txt with your targets:
    echo Example format:
    echo.
    echo Individual IPs:         Subnets:
    echo 192.168.1.1            192.168.0.0/24
    echo 10.0.0.1               10.0.0.0/16
    echo 172.16.1.1             172.16.0.0/12
    echo.
    echo Note: One entry per line, no separators needed
    echo.
    pause
    exit /b 1
)

:: Create output directory
if not exist "%OUTPUT_DIR%" (
    mkdir "%OUTPUT_DIR%"
    echo [INFO] Created output directory
)

:: Clean previous output files
del /f /q "%OUTPUT_DIR%\*.txt" 2>nul
echo [INFO] Cleaned previous output files

:: Process input file
echo [INFO] Processing scope.txt...

:: Create temporary files for sorting
type nul > "%OUTPUT_DIR%\ips.tmp"
type nul > "%OUTPUT_DIR%\subnets.tmp"

:: Sort IPs and subnets
for /f "tokens=* usebackq" %%a in ("%INPUT_FILE%") do (
    set "line=%%a"
    if "!line!" neq "" (
        echo %%a | findstr /r "^.*/..*$" >nul
        if errorlevel 1 (
            echo %%a >> "%OUTPUT_DIR%\ips.tmp"
        ) else (
            echo %%a >> "%OUTPUT_DIR%\subnets.tmp"
        )
    )
)

:: Count entries
set /a ip_count=0
set /a subnet_count=0
for /f %%a in ('type "%OUTPUT_DIR%\ips.tmp" ^| find /c /v ""') do set /a ip_count=%%a
for /f %%a in ('type "%OUTPUT_DIR%\subnets.tmp" ^| find /c /v ""') do set /a subnet_count=%%a

echo [INFO] Found %ip_count% IP addresses and %subnet_count% subnets

:: Split IPs into files
if %ip_count% gtr 0 (
    echo [INFO] Creating IP files...
    set /a current_count=0
    set /a file_number=1
    type nul > "%OUTPUT_DIR%\scope%file_number%.txt"
    
    for /f "tokens=*" %%a in (%OUTPUT_DIR%\ips.tmp) do (
        echo %%a >> "%OUTPUT_DIR%\scope!file_number!.txt"
        set /a current_count+=1
        
        if !current_count! equ %IPS_PER_FILE% (
            echo [INFO] Created scope!file_number!.txt
            set /a file_number+=1
            set /a current_count=0
            type nul > "%OUTPUT_DIR%\scope!file_number!.txt"
        )
    )
)

:: Split subnets into files
if %subnet_count% gtr 0 (
    echo [INFO] Creating subnet files...
    set /a current_count=0
    set /a file_number=1
    type nul > "%OUTPUT_DIR%\subnet%file_number%.txt"
    
    for /f "tokens=*" %%a in (%OUTPUT_DIR%\subnets.tmp) do (
        echo %%a >> "%OUTPUT_DIR%\subnet!file_number!.txt"
        set /a current_count+=1
        
        if !current_count! equ %SUBNETS_PER_FILE% (
            echo [INFO] Created subnet!file_number!.txt
            set /a file_number+=1
            set /a current_count=0
            type nul > "%OUTPUT_DIR%\subnet!file_number!.txt"
        )
    )
)

:: Clean up empty files
for %%f in ("%OUTPUT_DIR%\*.txt") do (
    for /f %%A in ('type "%%f" ^| find "" /v /c') do (
        if %%A equ 0 del "%%f"
    )
)

:: Remove temporary files
del /f /q "%OUTPUT_DIR%\*.tmp" 2>nul

:: Find Nmap installation
echo [INFO] Looking for Nmap installation...
set "NMAP_PATH="

:: Check common Nmap locations
if exist "C:\Program Files\Nmap\nmap.exe" (
    set "NMAP_PATH=C:\Program Files\Nmap\nmap.exe"
) else if exist "C:\Program Files (x86)\Nmap\nmap.exe" (
    set "NMAP_PATH=C:\Program Files (x86)\Nmap\nmap.exe"
)

:: If Nmap not found in common locations, ask user
if not defined NMAP_PATH (
    echo [WARN] Nmap not found in common locations
    echo Please enter the full path to nmap.exe
    echo Example: C:\Program Files\Nmap\nmap.exe
    echo.
    set /p "NMAP_PATH=Path to nmap.exe: "
)

:: Verify Nmap exists and is executable
if not exist "%NMAP_PATH%" (
    echo [ERROR] Could not find nmap.exe at specified location
    pause
    exit /b 1
)

:: Start Nmap scans
echo [INFO] Starting Nmap scans...
echo.

for %%f in ("%OUTPUT_DIR%\scope*.txt" "%OUTPUT_DIR%\subnet*.txt") do (
    if exist "%%f" (
        echo [INFO] Starting scan for %%~nxf
        start cmd /k "echo Starting scan for %%~nxf && "%NMAP_PATH%" -sS -Pn -p- -T4 -iL "%%f" -oA "%OUTPUT_DIR%\scan_%%~nf" --max-rtt-timeout 100ms --max-retries 3 --min-rate 450 --max-rate 15000 && echo Scan completed for %%~nxf"
        timeout /t 2 >nul
    )
)

:: Final status
echo.
echo ========================================================
echo                    Scan Status
echo ========================================================
echo All scans have been initiated
echo.
echo Scan files will be saved as:
echo - Normal output: %OUTPUT_DIR%\scan_*.nmap
echo - XML output:    %OUTPUT_DIR%\scan_*.xml
echo - Greppable:    %OUTPUT_DIR%\scan_*.gnmap
echo.
echo [INFO] Script completed successfully
echo.
pause
