#!/usr/bin/env python3
"""
IP and Subnet Masking Tool
--------------------------
Masks the middle octets of IP addresses and subnets with 'xx'
and saves the results to output.txt
"""

import re
import os
import sys
from datetime import datetime

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_colored(text, color):
    """Print text with specified color"""
    print(f"{color}{text}{Colors.ENDC}")

def print_header():
    """Print a formatted header for the tool"""
    print("\n" + "="*60)
    print_colored(f"  IP MASKING TOOL (Middle Octets)", Colors.BOLD + Colors.HEADER)
    print_colored(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", Colors.CYAN)
    print("="*60 + "\n")

def mask_ip_address(ip_str):
    """
    Masks the middle octets of an IP address with 'xx'
    Example: 202.58.132.56 -> 202.xx.xx.56
    """
    # Check if it's a CIDR notation (has a slash)
    if '/' in ip_str:
        ip_part, cidr_part = ip_str.split('/', 1)
        octets = ip_part.split('.')
        if len(octets) == 4:
            masked_ip = f"{octets[0]}.xx.xx.{octets[3]}/{cidr_part}"
            return masked_ip
        return ip_str  # Return unchanged if not in expected format
    
    # Handle regular IP address
    octets = ip_str.split('.')
    if len(octets) == 4:
        masked_ip = f"{octets[0]}.xx.xx.{octets[3]}"
        return masked_ip
    
    # If not recognized as an IP, return unchanged
    return ip_str

def process_file(input_file, output_file):
    """Process the input file and write masked IPs to output file"""
    try:
        # Check if input file exists
        if not os.path.exists(input_file):
            print_colored(f"Error: Input file '{input_file}' not found!", Colors.RED)
            return False, {}, 0
        
        # Read the input file
        with open(input_file, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
        
        print_colored(f"Found {len(lines)} entries in {input_file}", Colors.BLUE)
        
        # Process each line and mask IPs
        masked_entries = []
        stats = {"masked": 0, "unchanged": 0, "empty": 0}
        
        for i, line in enumerate(lines, 1):
            if not line:
                stats["empty"] += 1
                continue
                
            original = line
            masked = mask_ip_address(line)
            
            if masked == original:
                stats["unchanged"] += 1
            else:
                stats["masked"] += 1
            
            masked_entries.append(masked)
            
            # Show progress for large files
            if i % 1000 == 0 or i == len(lines):
                sys.stdout.write(f"\rProcessing: {i}/{len(lines)} entries")
                sys.stdout.flush()
        
        print("\n")
        
        # Write to output file
        with open(output_file, 'w') as f:
            f.write('\n'.join(entry for entry in masked_entries if entry))
        
        return True, stats, len(masked_entries)
    
    except Exception as e:
        print_colored(f"Error: {str(e)}", Colors.RED)
        return False, {}, 0

def main():
    """Main function"""
    print_header()
    
    # Default filenames
    input_file = 'scope.txt'
    output_file = 'output.txt'
    
    # Allow command-line arguments to override defaults
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    print_colored(f"Input file:  {input_file}", Colors.CYAN)
    print_colored(f"Output file: {output_file}", Colors.CYAN)
    print()
    
    # Process the file
    success, stats, total_written = process_file(input_file, output_file)
    
    if success:
        print_colored("\nSUMMARY:", Colors.BOLD)
        print(f"  - Entries processed:     {sum(stats.values())}")
        print_colored(f"  - IPs masked:            {stats['masked']} entries", Colors.GREEN)
        print(f"  - Unchanged entries:     {stats['unchanged']} entries")
        print(f"  - Empty/comment lines:   {stats['empty']} entries")
        print_colored(f"\nResults written to {output_file} ({total_written} entries)", Colors.GREEN + Colors.BOLD)
    else:
        print_colored("\nOperation failed. No output file was created.", Colors.RED)
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()