#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nessus Credential Validator v4.0
Description: Enhanced version with key-based authentication and flexible credential management
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
    print(Fore.YELLOW + "Nessus Pre-Scan Credential Validator v4.0\n" + Style.RESET_ALL)

def get_user_preferences():
    """Get user preferences for validation method"""
    print(Fore.GREEN + "[+] Configuration Options" + Style.RESET_ALL)
    
    # Authentication method choice
    print("\nChoose authentication method:")
    print("1. Username/Password credentials")
    print("2. SSH Key authentication")
    
    while True:
        auth_choice = input(Fore.YELLOW + "Enter choice (1 or 2): " + Style.RESET_ALL).strip()
        if auth_choice in ['1', '2']:
            break
        print(Fore.RED + "Invalid choice. Please enter 1 or 2." + Style.RESET_ALL)
    
    # Credential management choice
    print("\nChoose credential management:")
    print("1. Single credential set per system type (from credentials.txt)")
    print("2. Individual credentials per IP (from linux-credentials.txt/windows-credentials.txt)")
    
    while True:
        cred_choice = input(Fore.YELLOW + "Enter choice (1 or 2): " + Style.RESET_ALL).strip()
        if cred_choice in ['1', '2']:
            break
        print(Fore.RED + "Invalid choice. Please enter 1 or 2." + Style.RESET_ALL)
    
    return {
        'auth_method': 'key' if auth_choice == '2' else 'password',
        'cred_management': 'individual' if cred_choice == '2' else 'single'
    }

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

def parse_individual_credentials(system_type):
    """Parse individual credential files for specific system types"""
    filename = f"{system_type}-credentials.txt"
    ip_creds = {}
    
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Format: ip:"username":"password"
                parts = line.split(':', 1)
                if len(parts) == 2:
                    ip = parts[0].strip()
                    cred_part = parts[1].strip()
                    
                    # Parse credentials - expecting "username":"password"
                    cred_parts = cred_part.split('":"')
                    if len(cred_parts) == 2:
                        username = cred_parts[0].strip('"')
                        password = cred_parts[1].strip('"')
                        ip_creds[ip] = {'username': username, 'password': password}
    except FileNotFoundError:
        print(Fore.YELLOW + f"Warning: {filename} not found, using default credentials" + Style.RESET_ALL)
    
    return ip_creds

def get_ssh_keys():
    """Get available SSH keys from the key folder"""
    keys = {}
    
    if not os.path.exists(KEY_FOLDER):
        print(Fore.RED + f"Error: Key folder '{KEY_FOLDER}' not found!" + Style.RESET_ALL)
        return keys
    
    # Look for .pem and .ppk files
    for filename in os.listdir(KEY_FOLDER):
        if filename.endswith(('.pem', '.ppk')):
            key_path = os.path.join(KEY_FOLDER, filename)
            keys[filename] = key_path
            print(Fore.CYAN + f"Found key: {filename}" + Style.RESET_ALL)
    
    return keys

def validate_ssh_with_password(host, username, password):
    """Validate SSH credentials with password"""
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

def validate_ssh_with_key(host, username, key_path):
    """Validate SSH credentials with private key"""
    try:
        print(f"  {Fore.BLUE}[*]{Style.RESET_ALL} Testing SSH key connection to {host}...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Load private key
        try:
            if key_path.endswith('.pem'):
                private_key = paramiko.RSAKey.from_private_key_file(key_path)
            elif key_path.endswith('.ppk'):
                # For .ppk files, we need to handle differently
                # Note: paramiko doesn't directly support .ppk files
                # You might need to convert .ppk to .pem first
                print(f"  {Fore.YELLOW}[!]{Style.RESET_ALL} .ppk files need to be converted to .pem format")
                return False, "PPK format not directly supported, please convert to PEM"
            else:
                return False, "Unsupported key format"
                
        except Exception as e:
            return False, f"Key loading error: {str(e)}"
        
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
            return True, "Success"
        else:
            return False, "Command execution failed"
            
    except paramiko.AuthenticationException:
        return False, "Authentication failed (wrong key or username)"
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

def validate_system(system_type, ip, credentials, preferences, ssh_keys=None):
    """Validate a single system based on preferences"""
    if system_type == "windows":
        # Windows systems use SMB
        if 'username' in credentials and 'password' in credentials:
            username = credentials['username']
            password = credentials['password']
            domain = credentials.get('domain', '')
            return validate_smb(ip, username, password, domain)
        else:
            return False, "Missing credentials"
    
    else:
        # Linux and Others use SSH
        if preferences['auth_method'] == 'key':
            if ssh_keys and 'username' in credentials:
                username = credentials['username']
                # Use the first available key for now
                # In a more advanced version, you could allow key selection per IP
                key_name = list(ssh_keys.keys())[0]
                key_path = ssh_keys[key_name]
                print(f"  {Fore.BLUE}[*]{Style.RESET_ALL} Using SSH key: {key_name}")
                return validate_ssh_with_key(ip, username, key_path)
            else:
                return False, "Missing SSH keys or username"
        else:
            if 'username' in credentials and 'password' in credentials:
                username = credentials['username']
                password = credentials['password']
                return validate_ssh_with_password(ip, username, password)
            else:
                return False, "Missing credentials"

def main():
    print_banner()
    
    # Get user preferences
    preferences = get_user_preferences()
    
    # Get SSH keys if using key authentication
    ssh_keys = {}
    if preferences['auth_method'] == 'key':
        ssh_keys = get_ssh_keys()
        if not ssh_keys:
            print(Fore.RED + "No SSH keys found! Please add keys to the 'key' folder." + Style.RESET_ALL)
            exit(1)
    
    # Check if script has access to create files
    try:
        initialize_result_file()
    except PermissionError:
        print(Fore.RED + f"Error: Permission denied when writing to {RESULTS_FILE}!" + Style.RESET_ALL)
        exit(1)
    except Exception as e:
        print(Fore.RED + f"Error initializing result file: {str(e)}" + Style.RESET_ALL)
        exit(1)
    
    # Parse input files
    print(Fore.GREEN + "\n[+] Parsing configuration files" + Style.RESET_ALL)
    scopes = parse_scope()
    
    # Load credentials based on management preference
    if preferences['cred_management'] == 'single':
        credentials = parse_credentials()
        linux_ip_creds = {}
        windows_ip_creds = {}
    else:
        credentials = {"linux": {}, "windows": {}, "others": {}}
        linux_ip_creds = parse_individual_credentials('linux')
        windows_ip_creds = parse_individual_credentials('windows')
    
    # Track validation statistics
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
    print(Fore.GREEN + "\n[+] Validating Linux Credentials" + Style.RESET_ALL)
    print(Fore.CYAN + "╔═════════════════════════════════════════════════════════════╗")
    print(Fore.CYAN + "║                     LINUX VALIDATION                        ║")
    print(Fore.CYAN + "╚═════════════════════════════════════════════════════════════╝" + Style.RESET_ALL)
    
    for ip in scopes['linux']:
        stats["linux"]["total"] += 1
        time.sleep(0.5)  # Brief pause between attempts to avoid aggressive scanning
        
        # Get credentials for this IP
        if preferences['cred_management'] == 'individual' and ip in linux_ip_creds:
            creds = linux_ip_creds[ip]
        else:
            creds = credentials['linux']
        
        success, message = validate_system("linux", ip, creds, preferences, ssh_keys)
        
        if success:
            stats["linux"]["successful"] += 1
            print(Fore.GREEN + f"  [✓] {ip}: Validation successful" + Style.RESET_ALL)
            log_result("Linux", ip, "SSH", "Success", message)
            results_table["linux"].append([ip, "SSH", "✓", message])
        else:
            stats["linux"]["failed"] += 1
            print(Fore.RED + f"  [✗] {ip}: Validation failed - {message}" + Style.RESET_ALL)
            log_result("Linux", ip, "SSH", "Failed", message)
            results_table["linux"].append([ip, "SSH", "✗", message])
    
    # Windows validation
    print(Fore.GREEN + "\n[+] Validating Windows Credentials" + Style.RESET_ALL)
    print(Fore.CYAN + "╔═════════════════════════════════════════════════════════════╗")
    print(Fore.CYAN + "║                     WINDOWS VALIDATION                      ║")
    print(Fore.CYAN + "╚═════════════════════════════════════════════════════════════╝" + Style.RESET_ALL)
    
    for ip in scopes['windows']:
        stats["windows"]["total"] += 1
        time.sleep(0.5)  # Brief pause between attempts
        
        # Get credentials for this IP
        if preferences['cred_management'] == 'individual' and ip in windows_ip_creds:
            creds = windows_ip_creds[ip]
        else:
            creds = credentials['windows']
        
        success, message = validate_system("windows", ip, creds, preferences)
        
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

    # Others validation - use Linux and Windows credentials
    print(Fore.GREEN + "\n[+] Validating Other Systems" + Style.RESET_ALL)
    print(Fore.CYAN + "╔═════════════════════════════════════════════════════════════╗")
    print(Fore.CYAN + "║                     OTHERS VALIDATION                       ║")
    print(Fore.CYAN + "╚═════════════════════════════════════════════════════════════╝" + Style.RESET_ALL)
    
    for ip in scopes['others']:
        stats["others"]["total"] += 1
        time.sleep(0.5)  # Brief pause between attempts
        validated = False
        
        # Try SSH with Linux credentials first
        linux_creds = credentials['linux']
        if linux_creds and ('username' in linux_creds):
            print(f"  {Fore.BLUE}[*]{Style.RESET_ALL} Trying SSH with Linux credentials for {ip}...")
            ssh_success, ssh_message = validate_system("linux", ip, linux_creds, preferences, ssh_keys)
            
            if ssh_success:
                stats["others"]["successful"] += 1
                validated = True
                print(Fore.GREEN + f"  [✓] {ip}: SSH validation successful" + Style.RESET_ALL)
                log_result("Others", ip, "SSH", "Success", ssh_message)
                results_table["others"].append([ip, "SSH", "✓", ssh_message])
            else:
                print(Fore.RED + f"  [✗] {ip}: SSH validation failed - {ssh_message}" + Style.RESET_ALL)
        
        # If SSH failed, try SMB with Windows credentials
        if not validated:
            windows_creds = credentials['windows']
            if windows_creds and ('username' in windows_creds):
                print(f"  {Fore.BLUE}[*]{Style.RESET_ALL} Trying SMB with Windows credentials for {ip}...")
                smb_success, smb_message = validate_system("windows", ip, windows_creds, preferences)
                
                if smb_success:
                    stats["others"]["successful"] += 1
                    validated = True
                    print(Fore.GREEN + f"  [✓] {ip}: SMB validation successful" + Style.RESET_ALL)
                    log_result("Others", ip, "SMB", "Success", smb_message)
                    results_table["others"].append([ip, "SMB", "✓", smb_message])
                else:
                    print(Fore.RED + f"  [✗] {ip}: SMB validation failed - {smb_message}" + Style.RESET_ALL)
        
        if not validated:
            stats["others"]["failed"] += 1
            log_result("Others", ip, "Both", "Failed", "Both SSH and SMB failed")
            results_table["others"].append([ip, "Both", "✗", "Both SSH and SMB failed"])

    # Print summary table for each section
    print(Fore.GREEN + "\n[+] Validation Results Summary" + Style.RESET_ALL)
    
    # Linux Summary
    if results_table["linux"]:
        print(Fore.CYAN + "\nLinux Systems:" + Style.RESET_ALL)
        print(tabulate(results_table["linux"], 
                       headers=["IP Address", "Protocol", "Status", "Details"], 
                       tablefmt="grid"))
    
    # Windows Summary
    if results_table["windows"]:
        print(Fore.CYAN + "\nWindows Systems:" + Style.RESET_ALL)
        print(tabulate(results_table["windows"], 
                       headers=["IP Address", "Protocol", "Status", "Details"], 
                       tablefmt="grid"))
    
    # Others Summary
    if results_table["others"]:
        print(Fore.CYAN + "\nOther Systems:" + Style.RESET_ALL)
        print(tabulate(results_table["others"], 
                       headers=["IP Address", "Protocol", "Status", "Details"], 
                       tablefmt="grid"))
    
    # Overall statistics
    total_systems = sum(stats[s]["total"] for s in stats)
    total_successful = sum(stats[s]["successful"] for s in stats)
    total_failed = sum(stats[s]["failed"] for s in stats)
    
    print(Fore.CYAN + "\n[+] Overall Validation Statistics:" + Style.RESET_ALL)
    stats_table = [
        ["Linux", stats["linux"]["total"], stats["linux"]["successful"], stats["linux"]["failed"]],
        ["Windows", stats["windows"]["total"], stats["windows"]["successful"], stats["windows"]["failed"]],
        ["Others", stats["others"]["total"], stats["others"]["successful"], stats["others"]["failed"]],
        ["TOTAL", total_systems, total_successful, total_failed]
    ]
    
    print(tabulate(stats_table, 
                   headers=["System Type", "Total", "Successful", "Failed"], 
                   tablefmt="grid"))
    
    success_rate = (total_successful / total_systems) * 100 if total_systems > 0 else 0
    print(f"\nOverall Success Rate: {success_rate:.1f}%")

    print(Fore.CYAN + f"\n[+] Validation complete! Results saved to {RESULTS_FILE}" + Style.RESET_ALL)

if __name__ == "__main__":
    main()
