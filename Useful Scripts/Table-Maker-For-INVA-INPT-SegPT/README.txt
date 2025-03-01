# Subnet Processing and Excel Report Generator (VBScript)

## Overview
This VBScript processes a `scope.txt` file containing subnet information, extracts relevant data, and generates an Excel report. The script organizes the subnets into structured sections, provides statistics, and distributes IP addresses across multiple columns for better readability and analysis.

## Features
- Reads subnets from `scope.txt`
- Processes and categorizes subnet information
- Generates an Excel report with structured sections
- Distributes IP addresses across multiple columns
- Provides subnet statistics
- Automates the entire workflow

## Requirements
- Windows OS
- Microsoft Excel installed
- `scope.txt` file with subnet information

## Installation & Usage
1. Place the `scope.txt` file in the script directory.
2. Run the VBScript by double-clicking or executing via `cscript`:
   ```sh
   cscript script.vbs
   ```
3. The script will generate an Excel report in the same directory.

## File Structure
```
/project-directory
 ├── script.vbs         # Main VBScript
 ├── scope.txt          # Input file with subnet data
 ├── report.xlsx        # Generated output Excel file
```

## Input Format
`scope.txt` should contain subnets in the following format:
```
192.168.1.0/24
10.0.0.0/16
172.16.0.0/12
```

## Output Structure
The generated Excel report includes:
- **Subnet Summary**: A list of all processed subnets.
- **IP Distribution**: Categorized distribution of IPs.
- **Statistics**: Count of unique subnets, total IPs, and more.

## Customization
Modify `script.vbs` to:
- Change column formatting
- Customize report sections
- Adjust subnet processing logic

## Troubleshooting
- Ensure `scope.txt` follows the correct format.
- Check if Microsoft Excel is installed.
- Run the script using `cscript` if double-clicking does not work.

## License
This project is open-source and free to use.
