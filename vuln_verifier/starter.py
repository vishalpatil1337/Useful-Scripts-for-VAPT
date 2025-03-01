# starter.py
# Main entry point for the vulnerability verifier tool with enhanced logging
# Usage: python starter.py <csv_file> [--skip-tools] [--dry-run] [--category CATEGORY]

import sys
import os
import argparse
from core.installer import install_tools
from core.csv_parser import parse_nessus_csv
from core.reporter import generate_report
from core.file_manager import setup_directories
from scanners.apache_vuln_scanner import ApacheVulnScanner
from scanners.db_vuln_scanner import DBVulnScanner
from scanners.dns_vuln_scanner import DNSVulnScanner
from scanners.ftp_vuln_scanner import FTPVulnScanner
from scanners.ike_vuln_scanner import IKEVulnScanner
from scanners.nginx_vuln_scanner import NginxVulnScanner
from scanners.rdp_vuln_scanner import RDPVulnScanner
from scanners.smb_vuln_scanner import SMBVulnScanner
from scanners.smtp_vuln_scanner import SMTPVulnScanner
from scanners.smtp_vuln_scanner2 import SMTPVulnScanner2
from scanners.ssh_vuln_scanner import SSHVulnScanner
from scanners.ssl_vuln_scanner import SSLVulnScanner
from scanners.telnet_vuln_scanner import TelnetVulnScanner
from scanners.tomcat_vuln_scanner import TomcatVulnScanner
from scanners.vulnerability_scanner import VulnerabilityScanner
from scanners.web_vuln_scanner import WebVulnScanner
from utils.logger import logger
from utils.validator import validate_csv_file
from config.settings import OUTPUT_DIR

def parse_arguments():
    parser = argparse.ArgumentParser(description='Vulnerability Verifier Tool')
    parser.add_argument('csv_file', help='Path to the Nessus CSV report file')
    parser.add_argument('--skip-tools', action='store_true', help='Skip tool installation')
    parser.add_argument('--dry-run', action='store_true', help='Parse CSV but do not verify vulnerabilities')
    parser.add_argument('--category', help='Only verify vulnerabilities in this category')
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    logger.info("\033[94m=== Starting Vulnerability Verifier ===\033[0m")
    
    # Set environment variable for tool installation
    if args.skip_tools:
        os.environ['SKIP_TOOL_INSTALL'] = 'True'
        logger.info("\033[93mSkipping tool installation\033[0m")
        
    csv_file = args.csv_file
    try:
        # Validate the CSV file
        validate_csv_file(csv_file)
        logger.info(f"\033[92mProcessing {csv_file}\033[0m")
    except Exception as e:
        logger.error(f"\033[91m{str(e)}\033[0m")
        sys.exit(1)

    # Setup environment
    try:
        setup_directories()
        if not args.skip_tools:
            install_tools()
    except Exception as e:
        logger.error(f"\033[91mSetup failed: {e}\033[0m")
        sys.exit(1)

    # Parse CSV
    try:
        vulnerabilities = parse_nessus_csv(csv_file)
        logger.info(f"\033[92mFound {len(vulnerabilities)} vulnerabilities to verify\033[0m")
    except Exception as e:
        logger.error(f"\033[91mFailed to parse CSV: {e}\033[0m")
        sys.exit(1)
        
    # Filter by category if specified
    if args.category:
        vulnerabilities = [v for v in vulnerabilities if v["category"].lower() == args.category.lower()]
        logger.info(f"\033[92mFiltered to {len(vulnerabilities)} vulnerabilities in category '{args.category}'\033[0m")

    # Skip verification if dry-run is specified
    if args.dry_run:
        logger.info("\033[93mDry run - skipping vulnerability verification\033[0m")
        dummy_results = [("Not Verified (Dry Run)", f"{OUTPUT_DIR}/not_verified") for _ in vulnerabilities]
        generate_report(vulnerabilities, dummy_results)
        logger.info("\033[94m=== Dry Run Complete! Check verification_report.xlsx ===\033[0m")
        sys.exit(0)

    # Initialize scanners
    scanners = {
        "Apache": ApacheVulnScanner(),
        "DB": DBVulnScanner(),
        "DNS": DNSVulnScanner(),
        "FTP": FTPVulnScanner(),
        "IKE": IKEVulnScanner(),
        "Nginx": NginxVulnScanner(),
        "RDP": RDPVulnScanner(),
        "SMB": SMBVulnScanner(),
        "SMTP": SMTPVulnScanner(),
        "SMTP2": SMTPVulnScanner2(),
        "SSH": SSHVulnScanner(),
        "SSL": SSLVulnScanner(),
        "Telnet": TelnetVulnScanner(),
        "Tomcat": TomcatVulnScanner(),
        "General": VulnerabilityScanner(),
        "Web": WebVulnScanner()
    }

    # Verify vulnerabilities
    results = []
    for i, vuln in enumerate(vulnerabilities):
        category = vuln["category"]
        scanner = scanners.get(category, scanners["General"])
        try:
            logger.info(f"\033[93m[{i+1}/{len(vulnerabilities)}] Verifying {vuln['vulnerability']} on {vuln['ip']}:{vuln['port']}\033[0m")
            status, poc_path = scanner.verify(vuln)
            results.append((status, poc_path))
            logger.info(f"\033[92mVerified {vuln['vulnerability']} on {vuln['ip']}:{vuln['port']} - {status}\033[0m")
        except Exception as e:
            logger.error(f"\033[91mError verifying {vuln['vulnerability']}: {e}\033[0m")
            results.append(("Manual Check Required", f"{OUTPUT_DIR}/manual/{vuln['vulnerability'].replace(' ', '_')}_{vuln['ip']}_{vuln['port']}"))

    # Generate report
    try:
        generate_report(vulnerabilities, results)
        logger.info("\033[94m=== Verification Complete! Check output/ and verification_report.xlsx ===\033[0m")
    except Exception as e:
        logger.error(f"\033[91mFailed to generate report: {e}\033[0m")
        sys.exit(1)

if __name__ == "__main__":
    main()