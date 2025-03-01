Subnet Inventory Tool
Overview
The Subnet Inventory Tool is a VBScript utility that processes a list of IP subnets from a text file and generates a professionally formatted Excel workbook. The tool organizes subnets by sections, calculates statistics, and creates both standard and copy-paste friendly worksheets.
Prerequisites

Windows operating system
Microsoft Excel installed
Administrative privileges may be required

Files

subnet_inventory.vbs - The main script file
scope.txt - Input file containing subnet data (must be in the same directory as the script)
IP_Inventory.xlsx - Output Excel file (created in the same directory as the script)

Input File Format (scope.txt)
The input file should be formatted as follows:
Copy192.168.1.0/24
192.168.2.0/24
192.168.3.0/24

Section 1:
10.1.1.0/24
10.1.2.0/24
10.1.3.0/24

Section 2:
172.16.1.0/24
172.16.2.0/24

Each line must contain a single subnet in CIDR notation (e.g., 192.168.1.0/24)
Individual IP addresses without CIDR notation will not calculate correctly in statistics
IP ranges or other formats are not supported
Sections are defined by a header ending with a colon (:)
Subnets without a section header are placed in the "Main" section
Blank lines are ignored

Usage

Create a scope.txt file containing your subnet information
Double-click the subnet_inventory.vbs script to run it
Excel will open automatically and process the data
The script will save the generated file as IP_Inventory.xlsx

Example
Here's a simple example of how to run the tool:

Create a file named scope.txt with the following content:
Copy192.168.1.0/24
192.168.2.0/24

Production:
10.10.0.0/16
10.20.0.0/16

Development:
172.16.0.0/24
172.16.1.0/24
172.16.2.0/24

Run the script by double-clicking subnet_inventory.vbs
When prompted to delete the default sheet, click "Delete"
The resulting Excel file will contain three worksheets (Main, Production, Development) with formatted IP data and statistics

Features

Section Organization: Subnets are organized by sections defined in the input file
Balanced Distribution: Subnets are evenly distributed across four columns
Statistical Analysis: Each worksheet includes statistics on:

Subnet counts per column
Total subnet count
Total IP address count (calculated from CIDR notation)
Section name


Professional Formatting:

Alternating row colors
Proper headers and borders
Auto-sized columns
Consistent formatting


Copy-Paste Worksheets: Each section includes a dedicated worksheet with bullet-pointed subnets for easy copy-pasting into documentation

Expected Messages

Confirmation Dialog: When the script runs successfully, you'll receive a message: "Excel file created with professional formatting and statistics."
Sheet Deletion Dialog: If the script creates multiple worksheets, it will attempt to delete the default sheet. When prompted "Microsoft Excel will permanently delete this sheet. Do you want to continue?", click "Delete" to proceed.

Troubleshooting

"scope.txt not found": Ensure the input file exists in the same directory as the script
Script Errors: Make sure Excel is properly installed and accessible
Empty Results: Check that your scope.txt file is properly formatted with valid IP addresses in CIDR notation

Advanced Customization
The script can be modified to:

Change column headers
Adjust formatting preferences
Modify the statistics calculation
Alter the distribution algorithm

Limitations

Maximum sheet name length is 31 characters
The script does not validate IP address formats - only processes CIDR notation (e.g., 192.168.1.0/24)
Individual IP addresses without CIDR notation (e.g., 192.168.1.1) will not be properly counted in statistics
IP address ranges in non-CIDR formats will not work correctly
Limited error handling for malformed input
