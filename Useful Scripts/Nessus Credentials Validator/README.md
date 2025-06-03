# Nessus Credential Validator v4.0

```
  _  _  ___  ___  __  __ ___ _   _ ___ 
 | \| |/ _ \/ __| \ \/ /| __| | | / __|
 | .` | (_) \__ \  >  < | _|| |_| \__ \
 |_|\_|\___/|___/ /_/\_\|_|  \___/|___/
```

**Enhanced Pre-Scan Credential Validation Tool for Nessus**

A comprehensive Python tool designed to validate SSH and SMB credentials across multiple systems before running Nessus scans. This tool helps ensure credential accuracy, reducing false negatives and improving scan efficiency.

## Features

- **Multi-Protocol Support**: Validates both SSH (Linux/Unix) and SMB (Windows) credentials
- **Flexible Authentication**: Supports both password-based and SSH key-based authentication
- **Credential Management**: Single credential set or individual credentials per IP
- **Comprehensive Reporting**: Detailed CSV output and colorized console results
- **Error Handling**: Robust error handling with descriptive messages
- **Organized Scope Management**: Categorized IP management by system type

## Requirements

### Python Dependencies

```bash
pip install colorama paramiko smbprotocol ipaddress tabulate
```

### System Requirements

- **Python 3.6+**
- **Network connectivity** to target systems
- **SSH access** for Linux/Unix systems
- **SMB access** for Windows systems

## Installation

```bash
# Clone or download the script
git clone <repository-url>
cd nessus-credential-validator

# Make the script executable (Linux/macOS)
chmod +x nessus_validator.py
```

## File Structure

```
nessus-credential-validator/
├── nessus_validator.py          # Main script
├── scope.txt                    # Target IP addresses
├── credentials.txt              # Single credential set
├── linux-credentials.txt       # Individual Linux credentials
├── windows-credentials.txt     # Individual Windows credentials
├── key/                        # SSH private keys folder
│   ├── server1.pem
│   └── server2.pem
├── validation_results.csv      # Output results
└── requirements.txt            # Python dependencies
```

## Configuration Files

### scope.txt

```text
# Nessus Credential Validator - Target Scope
# Format: System type followed by IP addresses

Linux:
192.168.1.10
192.168.1.11
10.0.0.100

Windows:
192.168.1.20
192.168.1.21
10.0.0.200

Others:
192.168.1.30
192.168.1.31
```

### credentials.txt (Single Credential Set)

```text
# Single credential set per system type
# Format: "key" "value"

Linux:
"username" "root"
"password" "SecurePassword123"

Windows:
"username" "administrator"
"password" "WindowsPassword456"
"domain" "COMPANY"

Others:
"username" "admin"
"password" "DefaultPassword789"
```

### linux-credentials.txt (Individual Credentials)

```text
# Individual credentials per Linux system
# Format: ip:"username":"password"

192.168.1.10:"root":"RootPass123"
192.168.1.11:"admin":"AdminPass456"
10.0.0.100:"ubuntu":"UbuntuPass789"
```

### windows-credentials.txt (Individual Credentials)

```text
# Individual credentials per Windows system
# Format: ip:"username":"password"

192.168.1.20:"administrator":"WinPass123"
192.168.1.21:"admin":"LocalAdmin456"
10.0.0.200:"service":"ServicePass789"
```

## Usage

### Basic Usage

```bash
python3 nessus_validator.py
```

### Interactive Configuration

The script will prompt for configuration options:

```bash
[+] Configuration Options

Choose authentication method:
1. Username/Password credentials
2. SSH Key authentication
Enter choice (1 or 2): 1

Choose credential management:
1. Single credential set per system type (from credentials.txt)
2. Individual credentials per IP (from linux-credentials.txt/windows-credentials.txt)
Enter choice (1 or 2): 1
```

### SSH Key Authentication

```bash
# Place SSH private keys in the key/ folder
mkdir key
cp /path/to/private/key.pem key/
cp /path/to/another/key.pem key/

# Supported formats: .pem, .ppk (requires conversion)
```

## Output Examples

### Console Output

```bash
[+] Validating Linux Credentials
╔═════════════════════════════════════════════════════════════╗
║                     LINUX VALIDATION                        ║
╚═════════════════════════════════════════════════════════════╝
  [*] Testing SSH connection to 192.168.1.10...
  [✓] 192.168.1.10: Validation successful
  [*] Testing SSH connection to 192.168.1.11...
  [✗] 192.168.1.11: Validation failed - Authentication failed (wrong credentials)
```

### Results Summary Table

```
┌─────────────────┬──────────┬────────┬─────────────────────────────────────────┐
│ IP Address      │ Protocol │ Status │ Details                                 │
├─────────────────┼──────────┼────────┼─────────────────────────────────────────┤
│ 192.168.1.10    │ SSH      │ ✓      │ Success                                 │
│ 192.168.1.11    │ SSH      │ ✗      │ Authentication failed (wrong credentials) │
└─────────────────┴──────────┴────────┴─────────────────────────────────────────┘
```

### CSV Output (validation_results.csv)

```csv
System Type,IP Address,Protocol,Status,Details
Linux,192.168.1.10,SSH,Success,Success
Linux,192.168.1.11,SSH,Failed,Authentication failed (wrong credentials)
Windows,192.168.1.20,SMB,Success,Success
Windows,192.168.1.21,SMB,Failed,Connection timed out
```

## Advanced Configuration

### SSH Key Authentication Setup

```bash
# Generate SSH key pair (if needed)
ssh-keygen -t rsa -b 4096 -f key/server_key.pem

# Copy public key to target servers
ssh-copy-id -i key/server_key.pem.pub user@target_server

# Ensure proper permissions
chmod 600 key/*.pem
```

### Domain Authentication (Windows)

```text
# In credentials.txt, add domain parameter
Windows:
"username" "administrator"
"password" "WindowsPassword456"
"domain" "COMPANY"
```

### Timeout Configuration

```python
# Modify timeout in script (default: 5 seconds)
TIMEOUT = 10  # Increase for slower networks
```

## Troubleshooting

### Common Issues

#### SSH Connection Failures

```bash
# Check SSH service status
systemctl status ssh

# Verify SSH configuration
sudo nano /etc/ssh/sshd_config

# Common settings to check:
# PasswordAuthentication yes
# PubkeyAuthentication yes
# PermitRootLogin yes
```

#### SMB Connection Failures

```bash
# Check SMB service status (Windows)
net start server

# Verify SMB configuration
# Enable SMB in Windows Features
# Check firewall settings for port 445
```

#### Permission Errors

```bash
# Ensure script has write permissions
chmod 755 nessus_validator.py

# Check file permissions
ls -la *.txt
chmod 644 *.txt
```

### Error Messages

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `Authentication failed (wrong credentials)` | Invalid username/password | Verify credentials in config files |
| `Connection timed out` | Network/firewall issues | Check network connectivity and firewall rules |
| `Connection refused` | Service not running | Start SSH/SMB service on target |
| `Key loading error` | Invalid SSH key format | Verify key format and permissions |

## Best Practices

### Security

```bash
# Protect credential files
chmod 600 credentials.txt
chmod 600 *-credentials.txt

# Use dedicated service accounts
# Implement least privilege access
# Rotate credentials regularly
```

### Performance

```bash
# Adjust timeout for network conditions
TIMEOUT = 10  # Slower networks

# Batch processing for large scopes
# Use individual credentials for better control
```

### Maintenance

```bash
# Regular credential validation
# Update SSH keys before expiration
# Monitor failed authentication attempts
# Keep logs for audit purposes
```

## Integration with Nessus

### Workflow

```bash
1. Run credential validator
2. Review validation results
3. Fix failed credentials
4. Re-run validation
5. Import working credentials to Nessus
6. Configure Nessus scan policies
7. Execute Nessus scans
```

### Nessus Credential Configuration

```text
# Use validated credentials in Nessus:
# Policies → Credentials → SSH/Windows
# Import username/password combinations
# Configure privilege escalation if needed
```

## Logging and Monitoring

### Custom Logging

```python
# Add custom logging to script
import logging

logging.basicConfig(
    filename='validator.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

### Monitoring Integration

```bash
# Example: Send results to SIEM
cat validation_results.csv | logger -t nessus_validator

# Example: Email notifications
python3 send_results.py validation_results.csv
```

## Contributing

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd nessus-credential-validator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt
```

### Code Style

```bash
# Follow PEP 8 standards
flake8 nessus_validator.py

# Format code
black nessus_validator.py
```

## License

```text
This project is licensed under the MIT License.
See LICENSE file for details.
```

## Support

### Issues and Bugs

- Create an issue in the repository
- Provide detailed error messages
- Include configuration files (sanitized)
- Specify Python version and OS

### Feature Requests

- Submit feature requests via GitHub issues
- Describe use case and benefits
- Provide implementation suggestions

## Changelog

### Version 4.0
- Added SSH key authentication support
- Implemented individual credential management
- Enhanced error handling and reporting
- Improved console output with colors and tables
- Added comprehensive CSV logging

### Version 3.0
- Added SMB credential validation
- Implemented multi-protocol support
- Enhanced scope management

### Version 2.0
- Added credential file parsing
- Implemented CSV output
- Enhanced error handling

### Version 1.0
- Initial SSH credential validation
- Basic console output
