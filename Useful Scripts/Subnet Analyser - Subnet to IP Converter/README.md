# Subnet Analysis Tool

A professional tool for analyzing IP subnet ranges and generating detailed Excel reports with formatting and metadata.

## Overview

This Python-based script helps network engineers and security professionals analyze subnets listed in a `scope.txt` file and outputs structured details in an Excel file.

It performs the following:

- Parses subnets and validates format
- Calculates network information such as:
  - Network ID
  - Broadcast Address
  - Usable IPs
  - Network Class
- Outputs results into an Excel file with three sheets:
  - Overall Summary
  - Subnet Summary
  - IP Details

## Features

- 📊 Excel report with three structured sheets
- 📌 Includes network metadata and validation
- ✅ IPv4 and IPv6 support
- ⚠️ Highlights invalid subnets and errors in red
- 📅 Timestamped report generation
- 🧾 Summary statistics of subnet health and total IPs

## Requirements

- Python 3.6+
- Required packages:
  ```bash
  pip install pandas openpyxl
  ```

## Input File

**scope.txt**

A simple text file listing subnets (one per line):

```
192.168.1.0/24
10.0.0.0/8
2001:db8::/32
```

## Output

**subnet_ranges_detailed.xlsx**

This Excel file includes:
- Overall summary of stats (e.g., total subnets, usable IPs)
- Detailed information per subnet
- Complete list of IPs with metadata

## Usage

```bash
python subnet_analysis_tool.py
```

Ensure `scope.txt` is in the same directory.

## Sample Output Preview

- **Overall Summary** – Shows total/valid/invalid subnets and IP counts
- **Subnet Summary** – Each subnet’s info: version, class, broadcast, netmask, etc.
- **IP Details** – Lists every IP, and metadata appended at the bottom

## Troubleshooting

- ❌ *"Error: Input file 'scope.txt' not found."* – Ensure the file exists in the script directory
- ❌ *"Warning: Invalid subnet..."* – Check subnet formatting
- 🔒 *PermissionError on Excel write* – Close the Excel file if already open

## License

MIT License. Use responsibly for auditing, documentation, and network planning.
