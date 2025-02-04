@echo off
setlocal enabledelayedexpansion
cls

echo ===============================================================================
echo                           Scope Splitter and Nmap Scanner
echo                               Created: January 2025
echo ===============================================================================
echo.

REM ===============================================================================
REM                              Configuration Section
REM ===============================================================================
set "IPS_PER_FILE=20"
set "SUBNETS_PER_FILE=3"
set "INPUT_FILE=scope.txt"

REM Example format to show at the start
echo Example Input Format for scope.txt:
echo   IP Addresses:        Subnets:
echo   192.168.1.1         192.168.0.0/24
echo   10.0.0.1            10.0.0.0/16
echo   172.16.1.1          172.16.0.0/12
echo.

REM ===============================================================================
REM                              Initialization Check
REM ===============================================================================
echo [*] Checking environment...
echo [*] Verifying input file...
if not exist "%INPUT_FILE%" (
    echo [!] Error: %INPUT_FILE% not found!
    echo [!] Please create %INPUT_FILE% with your IPs and subnets.
    echo.
    pause
    exit /b 1
)

REM ===============================================================================
REM                              File Preparation
REM ===============================================================================
echo [*] Initializing temporary files...
echo [+] Creating work directories...
if not exist "output" mkdir output
if not exist "temp" mkdir temp

echo [+] Creating temporary sorting files...
type nul > "temp\temp_ips.txt"
type nul > "temp\temp_subnets.txt"
type nul > "temp\unique_ips.txt"
type nul > "temp\unique_subnets.txt"

REM ===============================================================================
REM                              Duplicate Removal
REM ===============================================================================
echo [*] Removing duplicates and sorting entries...
for /f "tokens=*" %%a in (%INPUT_FILE%) do (
    echo %%a | findstr /r /c:"/" >nul
    if errorlevel 1 (
        echo %%a >> "temp\temp_ips.txt"
    ) else (
        echo %%a >> "temp\temp_subnets.txt"
    )
)

REM Sort and remove duplicates from IPs
sort "temp\temp_ips.txt" /unique > "temp\unique_ips.txt"
sort "temp\temp_subnets.txt" /unique > "temp\unique_subnets.txt"

REM Count unique entries
set /a "unique_ips=0"
for /f %%a in ('type "temp\unique_ips.txt"^|find /c /v ""') do set /a "unique_ips=%%a"
set /a "unique_subnets=0"
for /f %%a in ('type "temp\unique_subnets.txt"^|find /c /v ""') do set /a "unique_subnets=%%a"

echo [+] Found %unique_ips% unique IP addresses
echo [+] Found %unique_subnets% unique subnets
echo.

REM ===============================================================================
REM                              File Generation
REM ===============================================================================
echo [*] Generating split files...

REM Initialize counters
set /a ip_file_count=1
set /a subnet_file_count=1
set /a ip_count=0
set /a subnet_count=0

echo [+] Creating IP files (max %IPS_PER_FILE% IPs per file)...
type nul > "output\scope%ip_file_count%.txt"
for /f "tokens=*" %%a in ('type "temp\unique_ips.txt"') do (
    echo %%a >> "output\scope!ip_file_count!.txt"
    set /a ip_count+=1
    if !ip_count! equ %IPS_PER_FILE% (
        echo     - Created scope!ip_file_count!.txt
        set /a ip_file_count+=1
        set /a ip_count=0
        type nul > "output\scope!ip_file_count!.txt"
    )
)

echo [+] Creating subnet files (max %SUBNETS_PER_FILE% subnets per file)...
type nul > "output\subnet%subnet_file_count%.txt"
for /f "tokens=*" %%a in ('type "temp\unique_subnets.txt"') do (
    echo %%a >> "output\subnet!subnet_file_count!.txt"
    set /a subnet_count+=1
    if !subnet_count! equ %SUBNETS_PER_FILE% (
        echo     - Created subnet!subnet_file_count!.txt
        set /a subnet_file_count+=1
        set /a subnet_count=0
        type nul > "output\subnet!subnet_file_count!.txt"
    )
)

REM ===============================================================================
REM                              Cleanup Section
REM ===============================================================================
echo [*] Cleaning up temporary files...
for %%f in ("output\scope*.txt" "output\subnet*.txt") do (
    for /f %%A in ('type "%%f"^|find "" /v /c') do (
        if %%A equ 0 del "%%f"
    )
)
rd /s /q "temp" 2>nul

REM ===============================================================================
REM                              Nmap Path Check
REM ===============================================================================
echo [*] Configuring Nmap...

:NMAP_PATH_CHECK
set "nmap_found=false"

REM Check common Nmap locations
for %%p in (
    "C:\Program Files\Nmap\nmap.exe"
    "C:\Program Files (x86)\Nmap\nmap.exe"
) do (
    %%p -h >nul 2>&1
    if !errorlevel! equ 0 (
        set "nmap_command=%%p"
        set "nmap_found=true"
        echo [+] Found Nmap at: %%p
        goto NMAP_FOUND
    )
)

:NMAP_INPUT
if "!nmap_found!"=="false" (
    echo [!] Nmap not found in common locations
    echo [?] Please enter the path to the Nmap installation directory
    set /p "nmap_path=Path: "
    
    REM Append nmap.exe to the user-provided path
    set "nmap_command=!nmap_path!\nmap.exe"
    
    if not exist "!nmap_command!" (
        echo [!] Invalid path. nmap.exe not found in the specified directory.
        goto NMAP_INPUT
    )
    
    "!nmap_command!" -h >nul 2>&1
    if !errorlevel! equ 0 (
        echo [+] Nmap path verified.
    ) else (
        echo [!] Invalid nmap executable. Please try again.
        goto NMAP_INPUT
    )
)

:NMAP_FOUND
echo [+] Nmap configuration completed
echo.

REM ===============================================================================
REM                              Scanning Section
REM ===============================================================================
echo [*] Starting Nmap scans...
echo.

for %%f in ("output\scope*.txt" "output\subnet*.txt") do (
    echo [+] Opening a new Command Prompt for %%~nxf scan...
    start cmd /k "!nmap_command! -sS -Pn -p- -T4 -iL %%f -oA output\open_port_%%~nf --max-rtt-timeout 100ms --max-retries 3 --defeat-rst-ratelimit --min-rate 450 --max-rate 15000"
    timeout 2 >nul
)

REM ===============================================================================
REM                              Completion
REM ===============================================================================
echo ===============================================================================
echo                               Scan Summary
echo ===============================================================================
echo [+] All commands have been executed in separate Command Prompts.
echo [+] Review the results in the generated .nmap, .xml, and .gnmap files in the 'output' folder.
echo.
echo Press any key to exit...
pause >nul
