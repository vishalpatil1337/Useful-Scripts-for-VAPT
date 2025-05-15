#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nessus Credential Validator v3.0
Description: Enhanced version with direct validation, better UI, and improved error handling
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
RESULTS_FILE = "validation_results.csv"
TIMEOUT = 5  # Seconds

def print_banner():
    """Display colorful script banner"""
    print(Fore.CYAN + r"""
  _  _  ___  ___  __  __ ___ _   _ ___ 
 | \| |/ _ \/ __| \ \/ /| __| | | / __|
 | .` | (_) \__ \  >  < | _|| |_| \__ \
 |_|\_|\___/|___/ /_/\_\|_|  \___/|___/
    """ + Style.RESET_ALL)
    print(Fore.YELLOW + "Nessus Pre-Scan Credential Validator v3.0\n" + Style.RESET_ALL)

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
    
    # Parse input files
    print(Fore.GREEN + "\n[+] Parsing configuration files" + Style.RESET_ALL)
    scopes = parse_scope()
    credentials = parse_credentials()
    
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
    print(Fore.GREEN + "\n[+] Validating Linux Credentials via SSH" + Style.RESET_ALL)
    print(Fore.CYAN + "╔═════════════════════════════════════════════════════════════╗")
    print(Fore.CYAN + "║                     LINUX VALIDATION                        ║")
    print(Fore.CYAN + "╚═════════════════════════════════════════════════════════════╝" + Style.RESET_ALL)
    
    linux_creds = credentials['linux']
    for ip in scopes['linux']:
        stats["linux"]["total"] += 1
        
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
    
    # Windows validation
    print(Fore.GREEN + "\n[+] Validating Windows Credentials via SMB" + Style.RESET_ALL)
    print(Fore.CYAN + "╔═════════════════════════════════════════════════════════════╗")
    print(Fore.CYAN + "║                     WINDOWS VALIDATION                      ║")
    print(Fore.CYAN + "╚═════════════════════════════════════════════════════════════╝" + Style.RESET_ALL)
    
    windows_creds = credentials['windows']
    for ip in scopes['windows']:
        stats["windows"]["total"] += 1
        
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

    # Others validation - try both protocols
    print(Fore.GREEN + "\n[+] Validating Other Systems" + Style.RESET_ALL)
    print(Fore.CYAN + "╔═════════════════════════════════════════════════════════════╗")
    print(Fore.CYAN + "║                     OTHERS VALIDATION                       ║")
    print(Fore.CYAN + "╚═════════════════════════════════════════════════════════════╝" + Style.RESET_ALL)
    
    other_creds = credentials['others']
    for ip in scopes['others']:
        stats["others"]["total"] += 1
        validated = False
        
        # Try SSH first
        if 'username' in other_creds and 'password' in other_creds:
            username = other_creds['username']
            password = other_creds['password']
            
            # Try SSH
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
                log_result("Others", ip, "SSH", "Failed", ssh_message)
                
                # Try SMB if SSH failed
                print(f"  {Fore.BLUE}[*]{Style.RESET_ALL} Trying SMB for {ip}...")
                domain = other_creds.get('domain', '')
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
        else:
            print(Fore.YELLOW + f"  [!] {ip}: Missing credentials" + Style.RESET_ALL)
            log_result("Others", ip, "Both", "Skipped", "Missing credentials")
            results_table["others"].append([ip, "Both", "!", "Missing credentials"])
        
        if not validated and 'username' in other_creds:
            stats["others"]["failed"] += 1

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