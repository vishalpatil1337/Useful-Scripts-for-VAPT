Nessus Credential Validator
A robust tool for validating SSH and SMB credentials across multiple systems prior to running Nessus vulnerability scans.
Overview
This utility helps security professionals verify that provided credentials work properly before initiating a Nessus scan. It directly validates Linux systems via SSH, Windows systems via SMB, and attempts both protocols for other systems.
Features

Direct Authentication Testing: Skips port scanning and directly tries authentication
Multi-Platform Support: Validates Linux (SSH), Windows (SMB), and mixed environments
Detailed Error Reporting: Shows specific authentication failures with actionable information
Color-Coded Output: Visual indicators of success/failure for easy interpretation
Comprehensive Reporting: Creates CSV output of all validation attempts
Custom Credential Format: Simple configuration for different system types

Requirements

Python 3.6+
Required Python packages:
pip install colorama paramiko smbprotocol tabulate


Quick Start

Clone the repository or download the script
Create your configuration files (see below)
Run the validator:
python credential_validator.py


Configuration Files
scope.txt
This file contains the target IP addresses, organized into sections:
Linux:
192.168.1.10
192.168.1.11

Windows:
192.168.10.20
192.168.10.21

Others:
10.0.0.50
10.0.0.51
credentials.txt
This file contains the credentials for each system type:
linux:
username "your_linux_user"
password "your_linux_password"

windows:
username "your_windows_user"
password "your_windows_password"
domain "DOMAIN"  # Optional

others:
username "your_user"
password "your_password"
domain "WORKGROUP"  # Optional
Important: Do not include colons after the key names - use the exact format shown above.
Output
The script produces two types of output:

Terminal Output: Color-coded, tabulated results showing validation status
CSV Report: A file named validation_results.csv containing all validation details

Troubleshooting
If you encounter "Missing credentials" errors:

Check that your credentials.txt file follows the exact format shown above
Ensure there are no colons after key names (e.g., use username "value" not username: "value")
Verify that the section headers (linux:, windows:, others:) are correctly spelled

For connection failures:

Verify that target systems are reachable on the network
Ensure firewall rules allow SSH (port 22) or SMB (port 445) connections
Verify that the credentials are correct and have sufficient permissions

Use Cases

Pre-scan validation for Nessus vulnerability assessments
Credential verification before automated deployments
Network access auditing
Privilege escalation testing

Notes

The script does not store or transmit credentials to external systems
All validation is performed directly between the host running the script and target systems
For large networks, expect the script to take some time to complete all validations
Domain is optional for Windows/SMB authentication

License
This tool is provided for professional use in security assessments.
