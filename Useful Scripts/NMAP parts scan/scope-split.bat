@echo off
setlocal enabledelayedexpansion
cls

:: =============================================================================
:: Script: Advanced Scope Splitter and Nmap Scanner
:: Author: Improved version
:: Created: February 2024
:: =============================================================================

:: Configuration Variables
set "CONFIG_IPS_PER_FILE=20"
set "CONFIG_SUBNETS_PER_FILE=3"
set "CONFIG_INPUT_FILE=scope.txt"
set "CONFIG_OUTPUT_DIR=output"
set "CONFIG_TEMP_DIR=temp"
set "CONFIG_LOG_FILE=scan_log.txt"

:: Color codes for Windows console
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "MAGENTA=[95m"
set "CYAN=[96m"
set "RESET=[0m"

:: =============================================================================
::                           Function Definitions
:: =============================================================================
:printBanner
    echo %CYAN%===============================================================================%RESET%
    echo %CYAN%                     Advanced Scope Splitter and Nmap Scanner%RESET%
    echo %CYAN%                              Version 2.0%RESET%
    echo %CYAN%===============================================================================%RESET%
    echo.
    goto :eof

:logMessage
    echo %~1 >> "%CONFIG_OUTPUT_DIR%\%CONFIG_LOG_FILE%"
    echo %~1
    goto :eof

:checkPrerequisites
    call :logMessage "[*] Checking prerequisites..."
    
    if not exist "%CONFIG_INPUT_FILE%" (
        call :logMessage "%RED%[!] Error: %CONFIG_INPUT_FILE% not found!%RESET%"
        call :logMessage "[i] Please create %CONFIG_INPUT_FILE% with your target scope."
        call :showInputFormat
        exit /b 1
    )
    
    :: Create necessary directories
    if not exist "%CONFIG_OUTPUT_DIR%" mkdir "%CONFIG_OUTPUT_DIR%"
    if not exist "%CONFIG_TEMP_DIR%" mkdir "%CONFIG_TEMP_DIR%"
    
    goto :eof

:showInputFormat
    echo.
    echo Example Input Format for scope.txt:
    echo   IP Addresses:        Subnets:
    echo   192.168.1.1         192.168.0.0/24
    echo   10.0.0.1            10.0.0.0/16
    echo   172.16.1.1          172.16.0.0/12
    echo.
    goto :eof

:processScopeFile
    call :logMessage "[*] Processing scope file..."
    
    :: Clear previous temp files if they exist
    del /f /q "%CONFIG_TEMP_DIR%\*.txt" 2>nul
    
    :: Use PowerShell for better text processing
    powershell -Command "Get-Content '%CONFIG_INPUT_FILE%' | ForEach-Object { if ($_ -match '/') { Add-Content '%CONFIG_TEMP_DIR%\temp_subnets.txt' $_ } else { Add-Content '%CONFIG_TEMP_DIR%\temp_ips.txt' $_ } }"
    
    :: Remove duplicates using PowerShell
    powershell -Command "Get-Content '%CONFIG_TEMP_DIR%\temp_ips.txt' | Sort-Object -Unique | Set-Content '%CONFIG_TEMP_DIR%\unique_ips.txt'"
    powershell -Command "Get-Content '%CONFIG_TEMP_DIR%\temp_subnets.txt' | Sort-Object -Unique | Set-Content '%CONFIG_TEMP_DIR%\unique_subnets.txt'"
    
    :: Count entries
    for /f %%a in ('type "%CONFIG_TEMP_DIR%\unique_ips.txt" ^| find /c /v ""') do set "unique_ips=%%a"
    for /f %%a in ('type "%CONFIG_TEMP_DIR%\unique_subnets.txt" ^| find /c /v ""') do set "unique_subnets=%%a"
    
    call :logMessage "[+] Found %GREEN%%unique_ips%%RESET% unique IP addresses"
    call :logMessage "[+] Found %GREEN%%unique_subnets%%RESET% unique subnets"
    
    goto :eof

:splitFiles
    call :logMessage "[*] Splitting files based on configuration..."
    
    :: Split IPs
    powershell -Command "$i=1; $count=0; Get-Content '%CONFIG_TEMP_DIR%\unique_ips.txt' | ForEach-Object { if ($count -eq %CONFIG_IPS_PER_FILE%) { $i++; $count=0 }; Add-Content '%CONFIG_OUTPUT_DIR%\scope$i.txt' $_; $count++ }"
    
    :: Split Subnets
    powershell -Command "$i=1; $count=0; Get-Content '%CONFIG_TEMP_DIR%\unique_subnets.txt' | ForEach-Object { if ($count -eq %CONFIG_SUBNETS_PER_FILE%) { $i++; $count=0 }; Add-Content '%CONFIG_OUTPUT_DIR%\subnet$i.txt' $_; $count++ }"
    
    goto :eof

:configureNmap
    call :logMessage "[*] Configuring Nmap..."
    
    :: Check common Nmap locations
    set "nmap_locations=C:\Program Files\Nmap\nmap.exe C:\Program Files (x86)\Nmap\nmap.exe"
    
    for %%n in (%nmap_locations%) do (
        if exist "%%n" (
            set "nmap_path=%%n"
            call :logMessage "[+] Found Nmap at: %GREEN%%%n%RESET%"
            goto :nmapFound
        )
    )
    
    :nmapPrompt
    call :logMessage "%YELLOW%[!] Nmap not found in common locations%RESET%"
    set /p "custom_path=Enter path to nmap.exe: "
    
    if exist "!custom_path!" (
        set "nmap_path=!custom_path!"
        goto :nmapFound
    ) else (
        call :logMessage "%RED%[!] Invalid path%RESET%"
        goto :nmapPrompt
    )
    
    :nmapFound
    goto :eof

:runScans
    call :logMessage "[*] Initiating Nmap scans..."
    
    for %%f in ("%CONFIG_OUTPUT_DIR%\scope*.txt" "%CONFIG_OUTPUT_DIR%\subnet*.txt") do (
        if exist "%%f" (
            call :logMessage "[+] Starting scan for: %%~nxf"
            start cmd /c ""%nmap_path%" -sS -Pn -p- -T4 -iL "%%f" -oA "%CONFIG_OUTPUT_DIR%\scan_%%~nf" --max-rtt-timeout 100ms --max-retries 3 --defeat-rst-ratelimit --min-rate 450 --max-rate 15000 && echo Scan completed for %%~nxf > "%CONFIG_OUTPUT_DIR%\%%~nf_completed.txt""
            timeout /t 2 /nobreak >nul
        )
    )
    
    goto :eof

:: =============================================================================
::                           Main Execution
:: =============================================================================
:main
    call :printBanner
    call :checkPrerequisites || exit /b 1
    call :processScopeFile
    call :splitFiles
    call :configureNmap
    call :runScans
    
    call :logMessage "%GREEN%[+] All operations completed successfully%RESET%"
    call :logMessage "[i] Check the output directory for results"
    
    timeout /t 5
exit /b 0
