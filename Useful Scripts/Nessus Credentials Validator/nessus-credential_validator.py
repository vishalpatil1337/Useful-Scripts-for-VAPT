#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nessus Credential Validator v3.1
Description: Enhanced version with PEM key support, multiple credential options, and improved validation
"""

from colorama import Fore, Style, init
import paramiko
import uuid
from smbprotocol.connection import Connection
from smbprotocol.session import Session
import ipaddress
import csv
import socket
import time
import os
import sys
from tabulate import tabulate

# Initialize colorama
init(autoreset=True)

# Configuration
SCOPE_FILE = "scope.txt"
CREDENTIALS_FILE = "credentials.txt"
LINUX_CREDS_FILE = "linux-credentials.txt"
WINDOWS_CREDS_FILE = "windows-credentials.txt"
RESULTS_FILE = "validation_results.csv"
KEY_FOLDER = "key"
TIMEOUT = 5  # Seconds

def print_banner():
    """Display colorful script banner"""
    print(Fore.CYAN + r"""
  _  _  ___  ___  __  __ ___ _   _ ___ 
 | \| |/ _ \/ __| \ \/ /| __| | | / __|
 | .` | (_) \__ \  >  < | _|| |_| \__ \
 |_|\_|\___/|___/ /_/\_\|_|  \___/|___/
    """ + Style.RESET_ALL)
    print(Fore.YELLOW + "Nessus Pre-Scan Credential Validator v3.1\n" + Style.RESET_ALL)

def get_credential_management_choice():
    """Get user choice for credential management"""
    print(Fore.GREEN + "Choose credential management:" + Style.RESET_ALL)
    print("1. Single credential set per system type (from credentials.txt)")
    print("2. Individual credentials per IP (from linux-credentials.txt/windows-credentials.txt)")
    
    while True:
        choice = input(Fore.YELLOW + "\nEnter your choice (1 or 2): " + Style.RESET_ALL).strip()
        if choice in ['1', '2']:
            return int(choice)
        print(Fore.RED + "Invalid choice. Please enter 1 or 2." + Style.RESET_ALL)

def get_validation_method():
    """Get user choice for validation method"""
    print(Fore.GREEN + "\nChoose validation method:" + Style.RESET_ALL)
    print("1. Use credentials (username/password)")
    print("2. Use PEM key authentication")
    
    while True:
        choice = input(Fore.YELLOW + "\nEnter your choice (1 or 2): " + Style.RESET_ALL).strip()
        if choice in ['1', '2']:
            return int(choice)
        print(Fore.RED + "Invalid choice. Please enter 1 or 2." + Style.RESET_ALL)

def parse_scope():
    """Parse scope.txt file into structured format"""
    scopes = {"linux": [], "windows": [], "others": []}
    current_section = None
    
    try:
        with open(SCOPE_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):  # Skip empty lines and comments
                    continue
                    
                line_lower = line.lower()
                if line_lower.startswith("linux:"):
                    current_section = "linux"
                elif line_lower.startswith("windows:"):
                    current_section = "windows"
                elif line_lower.startswith("others:"):
                    current_section = "others"
                elif current_section:
                    try:
                        # Strip any comments from the line
                        ip_str = line.split('#')[0].strip()
                        ip = ipaddress.ip_address(ip_str)
                        scopes[current_section].append(str(ip))
                    except ValueError:
                        print(Fore.RED + f"Invalid IP: {line}" + Style.RESET_ALL)
    except FileNotFoundError:
        print(Fore.RED + f"Error: {SCOPE_FILE} not found!" + Style.RESET_ALL)
        exit(1)
    
    # Print summary of loaded scope
    for section, ips in scopes.items():
        print(Fore.CYAN + f"Loaded {len(ips)} {section} IPs" + Style.RESET_ALL)
    
    return scopes

def parse_credentials():
    """Parse credentials.txt file using the "key" "value" format"""
    creds = {"linux": {}, "windows": {}, "others": {}}
    current_section = None
    
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):  # Skip empty lines and comments
                    continue
                    
                line_lower = line.lower()
                if line_lower.startswith("linux:"):
                    current_section = "linux"
                elif line_lower.startswith("windows:"):
                    current_section = "windows"
                elif line_lower.startswith("others:"):
                    current_section = "others"
                elif current_section:
                    parts = line.split(" ", 1)
                    if len(parts) == 2:
                        key = parts[0].strip('"')
                        value = parts[1].strip('"')
                        creds[current_section][key.lower()] = value
    except FileNotFoundError:
        print(Fore.RED + f"Error: {CREDENTIALS_FILE} not found!" + Style.RESET_ALL)
        exit(1)
    
    # Validate credential sections
    for section, section_creds in creds.items():
        if 'username' not in section_creds or 'password' not in section_creds:
            print(Fore.YELLOW + f"Warning: {section} credentials incomplete (missing username or password)" + Style.RESET_ALL)
    
    return creds

def parse_individual_credentials(filename):
    """Parse individual credentials file with format: ip:"username":"password" """
    creds = {}
    
    if not os.path.exists(filename):
        return None
        
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Parse format: ip:"username":"password"
                parts = line.split(':', 1)
                if len(parts) == 2:
                    ip = parts[0].strip()
                    cred_part = parts[1].strip()
                    
                    # Extract username and password from "username":"password"
                    if cred_part.startswith('"') and '":"' in cred_part:
                        cred_parts = cred_part.split('":"')
                        if len(cred_parts) == 2:
                            username = cred_parts[0].strip('"')
                            password = cred_parts[1].strip('"')
                            
                            try:
                                ip_obj = ipaddress.ip_address(ip)
                                creds[str(ip_obj)] = {"username": username, "password": password}
                            except ValueError:
                                print(Fore.RED + f"Invalid IP in {filename}: {ip}" + Style.RESET_ALL)
                        else:
                            print(Fore.RED + f"Invalid credential format in {filename}: {line}" + Style.RESET_ALL)
                    else:
                        print(Fore.RED + f"Invalid credential format in {filename}: {line}" + Style.RESET_ALL)
                else:
                    print(Fore.RED + f"Invalid line format in {filename}: {line}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"Error reading {filename}: {str(e)}" + Style.RESET_ALL)
        return None
    
    return creds

def get_pem_keys():
    """Get available PEM keys from the key folder"""
    pem_keys = []
    
    if not os.path.exists(KEY_FOLDER):
        print(Fore.RED + f"Key folder '{KEY_FOLDER}' not found!" + Style.RESET_ALL)
        return pem_keys
    
    for file in os.listdir(KEY_FOLDER):
        if file.endswith('.pem'):
            pem_keys.append(os.path.join(KEY_FOLDER, file))
    
    if not pem_keys:
        print(Fore.RED + f"No PEM keys found in '{KEY_FOLDER}' folder!" + Style.RESET_ALL)
    else:
        print(Fore.CYAN + f"Found {len(pem_keys)} PEM key(s) in '{KEY_FOLDER}' folder" + Style.RESET_ALL)
    
    return pem_keys

def validate_ssh_with_key(host, username, key_path):
    """Validate SSH connection using PEM key"""
    try:
        print(f"  {Fore.BLUE}[*]{Style.RESET_ALL} Testing SSH key connection to {host}...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Load the private key
        try:
            private_key = paramiko.RSAKey.from_private_key_file(key_path)
        except paramiko.PasswordRequiredException:
            return False, "Key requires passphrase (not supported)"
        except paramiko.SSHException:
            try:
                private_key = paramiko.Ed25519Key.from_private_key_file(key_path)
            except paramiko.SSHException:
                try:
                    private_key = paramiko.ECDSAKey.from_private_key_file(key_path)
                except paramiko.SSHException:
                    return False, "Unsupported key format"
        
        client.connect(host, 
                     username=username, 
                     pkey=private_key,
                     timeout=TIMEOUT,
                     banner_timeout=TIMEOUT)
        
        # Try executing a simple command to verify access
        stdin, stdout, stderr = client.exec_command('echo "Connection successful"')
        result = stdout.read().decode().strip()
        client.close()
        
        if result == "Connection successful":
            return True, f"Success with key: {os.path.basename(key_path)}"
        else:
            return False, "Command execution failed"
            
    except paramiko.AuthenticationException:
        return False, f"Key authentication failed: {os.path.basename(key_path)}"
    except paramiko.SSHException as e:
        return False, f"SSH error with key: {str(e)}"
    except socket.timeout:
        return False, "Connection timed out"
    except socket.error as e:
        return False, f"Network error: {str(e)}"
    except Exception as e:
        return False, f"Error with key: {str(e)}"

def validate_ssh(host, username, password):
    """Validate SSH credentials with improved error handling"""
    try:
        print(f"  {Fore.BLUE}[*]{Style.RESET_ALL} Testing SSH connection to {host}...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, 
                     username=username, 
                     password=password, 
                     timeout=TIMEOUT,
                     banner_timeout=TIMEOUT)
        
        # Try executing a simple command to verify access
        stdin, stdout, stderr = client.exec_command('echo "Connection successful"')
        result = stdout.read().decode().strip()
        client.close()
        
        if result == "Connection successful":
            return True, "Success"
        else:
            return False, "Command execution failed"
            
    except paramiko.AuthenticationException:
        return False, "Authentication failed (wrong credentials)"
    except paramiko.SSHException as e:
        return False, f"SSH error: {str(e)}"
    except socket.timeout:
        return False, "Connection timed out"
    except socket.error as e:
        return False, f"Network error: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def validate_smb(host, username, password, domain=""):
    """Validate SMB credentials with improved error handling"""
    try:
        print(f"  {Fore.BLUE}[*]{Style.RESET_ALL} Testing SMB connection to {host}...")
        connection = Connection(uuid.uuid4(), host, 445)
        connection.connect(timeout=TIMEOUT)
        
        # Format username with domain if provided
        user_id = f"{domain}\\{username}" if domain else username
        
        session = Session(connection, user_id, password)
        session.connect()
        
        session.disconnect()
        connection.disconnect()
        return True, "Success"
    except Exception as e:
        error_msg = str(e).lower()
        if "access denied" in error_msg:
            return False, "Authentication failed (wrong credentials)"
        elif "timed out" in error_msg:
            return False, "Connection timed out"
        elif "connection refused" in error_msg:
            return False, "Connection refused"
        else:
            return False, f"SMB error: {str(e)}"

def initialize_result_file():
    """Initialize the results CSV file with headers"""
    with open(RESULTS_FILE, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            'System Type', 
            'IP Address', 
            'Protocol', 
            'Status', 
            'Details'
        ])

def log_result(system_type, ip, protocol, status, details):
    """Log validation result to CSV file"""
    with open(RESULTS_FILE, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([system_type, ip, protocol, status, details])

def validate_with_single_credentials(scopes, credentials, use_key_auth, pem_keys):
    """Validate using single credential set per system type"""
    stats = {
        "linux": {"total": 0, "successful": 0, "failed": 0},
        "windows": {"total": 0, "successful": 0, "failed": 0}, 
        "others": {"total": 0, "successful": 0, "failed": 0}
    }
    
    results_table = {
        "linux": [],
        "windows": [],
        "others": []
    }
    
    # Linux validation
    print(Fore.GREEN + "\n[+] Validating Linux Systems" + Style.RESET_ALL)
    print(Fore.CYAN + "╔═════════════════════════════════════════════════════════════╗")
    print(Fore.CYAN + "║                     LINUX VALIDATION                        ║")
    print(Fore.CYAN + "╚═════════════════════════════════════════════════════════════╝" + Style.RESET_ALL)
    
    linux_creds = credentials['linux']
    for ip in scopes['linux']:
        stats["linux"]["total"] += 1
        
        if use_key_auth:
            if 'username' in linux_creds and pem_keys:
                username = linux_creds['username']
                success = False
                message = ""
                
                for key_path in pem_keys:
                    success, message = validate_ssh_with_key(ip, username, key_path)
                    if success:
                        break
                
                if success:
                    stats["linux"]["successful"] += 1
                    print(Fore.GREEN + f"  [✓] {ip}: SSH key validation successful" + Style.RESET_ALL)
                    log_result("Linux", ip, "SSH-Key", "Success", message)
                    results_table["linux"].append([ip, "SSH-Key", "✓", message])
                else:
                    stats["linux"]["failed"] += 1
                    print(Fore.RED + f"  [✗] {ip}: SSH key validation failed - {message}" + Style.RESET_ALL)
                    log_result("Linux", ip, "SSH-Key", "Failed", message)
                    results_table["linux"].append([ip, "SSH-Key", "✗", message])
            else:
                print(Fore.YELLOW + f"  [!] {ip}: Missing username or PEM keys" + Style.RESET_ALL)
                log_result("Linux", ip, "SSH-Key", "Skipped", "Missing username or PEM keys")
                results_table["linux"].append([ip, "SSH-Key", "!", "Missing username or PEM keys"])
        else:
            if 'username' in linux_creds and 'password' in linux_creds:
                username = linux_creds['username']
                password = linux_creds['password']
                
                success, message = validate_ssh(ip, username, password)
                
                if success:
                    stats["linux"]["successful"] += 1
                    print(Fore.GREEN + f"  [✓] {ip}: SSH validation successful" + Style.RESET_ALL)
                    log_result("Linux", ip, "SSH", "Success", message)
                    results_table["linux"].append([ip, "SSH", "✓", message])
                else:
                    stats["linux"]["failed"] += 1
                    print(Fore.RED + f"  [✗] {ip}: SSH validation failed - {message}" + Style.RESET_ALL)
                    log_result("Linux", ip, "SSH", "Failed", message)
                    results_table["linux"].append([ip, "SSH", "✗", message])
            else:
                print(Fore.YELLOW + f"  [!] {ip}: Missing Linux credentials" + Style.RESET_ALL)
                log_result("Linux", ip, "SSH", "Skipped", "Missing credentials")
                results_table["linux"].append([ip, "SSH", "!", "Missing credentials"])
    
    # Windows validation (only with credentials, not keys)
    print(Fore.GREEN + "\n[+] Validating Windows Systems" + Style.RESET_ALL)
    print(Fore.CYAN + "╔═════════════════════════════════════════════════════════════╗")
    print(Fore.CYAN + "║                     WINDOWS VALIDATION                      ║")
    print(Fore.CYAN + "╚═════════════════════════════════════════════════════════════╝" + Style.RESET_ALL)
    
    windows_creds = credentials['windows']
    for ip in scopes['windows']:
        stats["windows"]["total"] += 1
        
        if use_key_auth:
            print(Fore.YELLOW + f"  [!] {ip}: Key authentication not supported for Windows" + Style.RESET_ALL)
            log_result("Windows", ip, "SMB", "Skipped", "Key auth not supported for Windows")
            results_table["windows"].append([ip, "SMB", "!", "Key auth not supported"])
        else:
            if 'username' in windows_creds and 'password' in windows_creds:
                username = windows_creds['username']
                password = windows_creds['password']
                domain = windows_creds.get('domain', '')
                
                success, message = validate_smb(ip, username, password, domain)
                
                if success:
                    stats["windows"]["successful"] += 1
                    print(Fore.GREEN + f"  [✓] {ip}: SMB validation successful" + Style.RESET_ALL)
                    log_result("Windows", ip, "SMB", "Success", message)
                    results_table["windows"].append([ip, "SMB", "✓", message])
                else:
                    stats["windows"]["failed"] += 1
                    print(Fore.RED + f"  [✗] {ip}: SMB validation failed - {message}" + Style.RESET_ALL)
                    log_result("Windows", ip, "SMB", "Failed", message)
                    results_table["windows"].append([ip, "SMB", "✗", message])
            else:
                print(Fore.YELLOW + f"  [!] {ip}: Missing Windows credentials" + Style.RESET_ALL)
                log_result("Windows", ip, "SMB", "Skipped", "Missing credentials")
                results_table["windows"].append([ip, "SMB", "!", "Missing credentials"])

    # Others validation - try both Linux and Windows credentials
    print(Fore.GREEN + "\n[+] Validating Other Systems" + Style.RESET_ALL)
    print(Fore.CYAN + "╔═════════════════════════════════════════════════════════════╗")
    print(Fore.CYAN + "║                     OTHERS VALIDATION                       ║")
    print(Fore.CYAN + "╚═════════════════════════════════════════════════════════════╝" + Style.RESET_ALL)
    
    for ip in scopes['others']:
        stats["others"]["total"] += 1
        validated = False
        
        # Try Linux credentials first
        if 'username' in linux_creds and ('password' in linux_creds or use_key_auth):
            username = linux_creds['username']
            
            if use_key_auth and pem_keys:
                print(f"  {Fore.BLUE}[*]{Style.RESET_ALL} Trying SSH key authentication for {ip}...")
                success = False
                message = ""
                
                for key_path in pem_keys:
                    success, message = validate_ssh_with_key(ip, username, key_path)
                    if success:
                        break
                
                if success:
                    stats["others"]["successful"] += 1
                    validated = True
                    print(Fore.GREEN + f"  [✓] {ip}: SSH key validation successful" + Style.RESET_ALL)
                    log_result("Others", ip, "SSH-Key", "Success", message)
                    results_table["others"].append([ip, "SSH-Key", "✓", message])
                else:
                    print(Fore.RED + f"  [✗] {ip}: SSH key validation failed - {message}" + Style.RESET_ALL)
            else:
                if 'password' in linux_creds:
                    password = linux_creds['password']
                    print(f"  {Fore.BLUE}[*]{Style.RESET_ALL} Trying SSH for {ip}...")
                    ssh_success, ssh_message = validate_ssh(ip, username, password)
                    
                    if ssh_success:
                        stats["others"]["successful"] += 1
                        validated = True
                        print(Fore.GREEN + f"  [✓] {ip}: SSH validation successful" + Style.RESET_ALL)
                        log_result("Others", ip, "SSH", "Success", ssh_message)
                        results_table["others"].append([ip, "SSH", "✓", ssh_message])
                    else:
                        print(Fore.RED + f"  [✗] {ip}: SSH validation failed - {ssh_message}" + Style.RESET_ALL)
        
        # If SSH failed and not using key auth, try Windows credentials
        if not validated and not use_key_auth and 'username' in windows_creds and 'password' in windows_creds:
            username = windows_creds['username']
            password = windows_creds['password']
            domain = windows_creds.get('domain', '')
            
            print(f"  {Fore.BLUE}[*]{Style.RESET_ALL} Trying SMB for {ip}...")
            smb_success, smb_message = validate_smb(ip, username, password, domain)
            
            if smb_success:
                stats["others"]["successful"] += 1
                validated = True
                print(Fore.GREEN + f"  [✓] {ip}: SMB validation successful" + Style.RESET_ALL)
                log_result("Others", ip, "SMB", "Success", smb_message)
                results_table["others"].append([ip, "SMB", "✓", smb_message])
            else:
                print(Fore.RED + f"  [✗] {ip}: SMB validation failed - {smb_message}" + Style.RESET_ALL)
                log_result("Others", ip, "SMB", "Failed", smb_message)
                results_table["others"].append([ip, "Both", "✗", "Both SSH and SMB failed"])
        
        if not validated:
            stats["others"]["failed"] += 1
            if not results_table["others"] or results_table["others"][-1][0] != ip:
                log_result("Others", ip, "Both", "Failed", "No suitable credentials found")
                results_table["others"].append([ip, "Both", "✗", "No suitable credentials found"])
    
    return stats, results_table

def validate_with_individual_credentials(use_key_auth, pem_keys):
    """Validate using individual credentials per IP"""
    stats = {
        "linux": {"total": 0, "successful": 0, "failed": 0},
        "windows": {"total": 0, "successful": 0, "failed": 0}
    }
    
    results_table = {
        "linux": [],
        "windows": []
    }
    
    # Linux validation
    linux_creds = parse_individual_credentials(LINUX_CREDS_FILE)
    if linux_creds is not None:
        print(Fore.GREEN + "\n[+] Validating Linux Systems with Individual Credentials" + Style.RESET_ALL)
        print(Fore.CYAN + "╔═════════════════════════════════════════════════════════════╗")
        print(Fore.CYAN + "║                     LINUX VALIDATION                        ║")
        print(Fore.CYAN + "╚═════════════════════════════════════════════════════════════╝" + Style.RESET_ALL)
        
        for ip, cred in linux_creds.items():
            stats["linux"]["total"] += 1
            username = cred['username']
            
            if use_key_auth:
                if pem_keys:
                    success = False
                    message = ""
                    
                    for key_path in pem_keys:
                        success, message = validate_ssh_with_key(ip, username, key_path)
                        if success:
                            break
                    
                    if success:
                        stats["linux"]["successful"] += 1
                        print(Fore.GREEN + f"  [✓] {ip}: SSH key validation successful" + Style.RESET_ALL)
                        log_result("Linux", ip, "SSH-Key", "Success", message)
                        results_table["linux"].append([ip, "SSH-Key", "✓", message])
                    else:
                        stats["linux"]["failed"] += 1
                        print(Fore.RED + f"  [✗] {ip}: SSH key validation failed - {message}" + Style.RESET_ALL)
                        log_result("Linux", ip, "SSH-Key", "Failed", message)
                        results_table["linux"].append([ip, "SSH-Key", "✗", message])
                else:
                    print(Fore.YELLOW + f"  [!] {ip}: No PEM keys available" + Style.RESET_ALL)
                    log_result("Linux", ip, "SSH-Key", "Skipped", "No PEM keys available")
                    results_table["linux"].append([ip, "SSH-Key", "!", "No PEM keys available"])
            else:
                password = cred['password']
                success, message = validate_ssh(ip, username, password)
                
                if success:
                    stats["linux"]["successful"] += 1
                    print(Fore.GREEN + f"  [✓] {ip}: SSH validation successful" + Style.RESET_ALL)
                    log_result("Linux", ip, "SSH", "Success", message)
                    results_table["linux"].append([ip, "SSH", "✓", message])
                else:
                    stats["linux"]["failed"] += 1
                    print(Fore.RED + f"  [✗] {ip}: SSH validation failed - {message}" + Style.RESET_ALL)
                    log_result("Linux", ip, "SSH", "Failed", message)
                    results_table["linux"].append([ip, "SSH", "✗", message])
    else:
        print(Fore.YELLOW + f"Warning: {LINUX_CREDS_FILE} not found or empty, skipping Linux validation" + Style.RESET_ALL)
    
    # Windows validation
    windows_creds = parse_individual_credentials(WINDOWS_CREDS_FILE)
    if windows_creds is not None:
        print(Fore.GREEN + "\n[+] Validating Windows Systems with Individual Credentials" + Style.RESET_ALL)
        print(Fore.CYAN + "╔═════════════════════════════════════════════════════════════╗")
        print(Fore.CYAN + "║                     WINDOWS VALIDATION                      ║")
        print(Fore.CYAN + "╚═════════════════════════════════════════════════════════════╝" + Style.RESET_ALL)
        
        if use_key_auth:
            print(Fore.YELLOW + "  [!] Key authentication not supported for Windows, skipping..." + Style.RESET_ALL)
        else:
            for ip, cred in windows_creds.items():
                stats["windows"]["total"] += 1
                username = cred['username']
                password = cred['password']
                
                success, message = validate_smb(ip, username, password)
                
                if success:
                    stats["windows"]["successful"] += 1
                    print(Fore.GREEN + f"  [✓] {ip}: SMB validation successful" + Style.RESET_ALL)
                    log_result("Windows", ip, "SMB", "Success", message)
                    results_table["windows"].append([ip, "SMB", "✓", message])
                else:
                    stats["windows"]["failed"] += 1
                    print(Fore.RED + f"  [✗] {ip}: SMB validation failed - {message}" + Style.RESET_ALL)
                    log_result("Windows", ip, "SMB", "Failed", message)
                    results_table["windows"].append([ip, "SMB", "✗", message])
    else:
        print(Fore.YELLOW + f"Warning: {WINDOWS_CREDS_FILE} not found or empty, skipping Windows validation" + Style.RESET_ALL)
    
    return stats, results_table

def print_results_summary(stats, results_table):
    """Print validation results summary"""
    print(Fore.GREEN + "\n[+] Validation Results Summary" + Style.RESET_ALL)
    
    # Linux Summary
    if results_table.get("linux") and results_table["linux"]:
        print(Fore.CYAN + "\nLinux Systems:" + Style.RESET_ALL)
        print(tabulate(results_table["linux"], 
                       headers=["IP Address", "Protocol", "Status", "Details"], 
                       tablefmt="grid"))
    
    # Windows Summary
    if results_table.get("windows") and results_table["windows"]:
        print(Fore.CYAN + "\nWindows Systems:" + Style.RESET_ALL)
        print(tabulate(results_table["windows"], 
                       headers=["IP Address", "Protocol", "Status", "Details"], 
                       tablefmt="grid"))
    
    # Others Summary
    if results_table.get("others") and results_table["others"]:
        print(Fore.CYAN + "\nOther Systems:" + Style.RESET_ALL)
        print(tabulate(results_table["others"], 
                       headers=["IP Address", "Protocol", "Status", "Details"], 
                       tablefmt="grid"))
    
    # Overall statistics
    total_systems = sum(stats[s]["total"] for s in stats)
    total_successful = sum(stats[s]["successful"] for s in stats)
    total_failed = sum(stats[s]["failed"] for s in stats)
    
    print(Fore.CYAN + "\n[+] Overall Validation Statistics:" + Style.RESET_ALL)
    stats_table = []
    
    for system_type in stats:
        if stats[system_type]["total"] > 0:
            stats_table.append([
                system_type.capitalize(), 
                stats[system_type]["total"], 
                stats[system_type]["successful"], 
                stats[system_type]["failed"]
            ])
    
    if stats_table:
        stats_table.append(["TOTAL", total_systems, total_successful, total_failed])
        print(tabulate(stats_table, 
                       headers=["System Type", "Total", "Successful", "Failed"], 
                       tablefmt="grid"))
        
        success_rate = (total_successful / total_systems) * 100 if total_systems > 0 else 0
        print(f"\nOverall Success Rate: {success_rate:.1f}%")

def main():
    print_banner()
    
    # Check if script has access to create files
    try:
        initialize_result_file()
    except PermissionError:
        print(Fore.RED + f"Error: Permission denied when writing to {RESULTS_FILE}!" + Style.RESET_ALL)
        exit(1)
    except Exception as e:
        print(Fore.RED + f"Error initializing result file: {str(e)}" + Style.RESET_ALL)
        exit(1)
    
    # Get user choices
    cred_choice = get_credential_management_choice()
    auth_choice = get_validation_method()
    
    use_key_auth = (auth_choice == 2)
    pem_keys = []
    
    if use_key_auth:
        pem_keys = get_pem_keys()
        if not pem_keys:
            print(Fore.RED + "No PEM keys found. Exiting..." + Style.RESET_ALL)
            exit(1)
    
    if cred_choice == 1:
        # Single credential set per system type
        print(Fore.GREEN + "\n[+] Parsing configuration files" + Style.RESET_ALL)
        scopes = parse_scope()
        credentials = parse_credentials()
        
        stats, results_table = validate_with_single_credentials(scopes, credentials, use_key_auth, pem_keys)
    else:
        # Individual credentials per IP
        print(Fore.GREEN + "\n[+] Using individual credentials per IP" + Style.RESET_ALL)
        
        stats, results_table = validate_with_individual_credentials(use_key_auth, pem_keys)
    
    # Print results summary
    print_results_summary(stats, results_table)
    
    print(Fore.CYAN + f"\n[+] Validation complete! Results saved to {RESULTS_FILE}" + Style.RESET_ALL)

if __name__ == "__main__":
    main()
