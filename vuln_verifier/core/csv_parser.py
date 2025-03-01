# core/csv_parser.py
# Professional Nessus CSV parsing with detailed vulnerability mapping

import csv
import json
import os  # Added missing import
from config.settings import CONFIG_DIR
from utils.logger import logger
from utils.exceptions import ValidationError

def get_field_mapping(reader):
    """Determine the CSV format and return appropriate field mapping"""
    fieldnames = reader.fieldnames
    
    # Check if this is raw_report.csv format (Nessus standard export)
    if "Plugin ID" in fieldnames and "Host" in fieldnames:
        return {
            "ip": "Host",
            "port": "Port",
            "service": "Protocol",  # Using Protocol as service
            "vulnerability": "Name",  # Using Name as vulnerability title
            "plugin_id": "Plugin ID",
            "description": "Description",
            "solution": "Solution"
        }
    # Check if this is report_4.csv format
    elif "Asset IP Address" in fieldnames and "Vulnerability Title" in fieldnames:
        return {
            "ip": "Asset IP Address",
            "port": "Service Port",
            "service": "Service Protocol",
            "vulnerability": "Vulnerability Title",
            "plugin_id": "Vulnerability CVE IDs",  # Using CVE IDs as plugin_id
            "description": "Vulnerability Description",
            "solution": "Vulnerability Solution"
        }
    # Default mapping with expected field names
    else:
        return {
            "ip": "Host",
            "port": "Port",
            "service": "Service",
            "vulnerability": "Vulnerability",
            "plugin_id": "Plugin ID",
            "description": "Description",
            "solution": "Solution"
        }

def categorize_vulnerability(vuln, mappings):
    service = vuln["service"].lower() if vuln["service"] else ""
    vuln_name = vuln["vulnerability"].lower() if vuln["vulnerability"] else ""
    plugin_id = vuln["plugin_id"]
    
    # Try to match by keywords in service or vulnerability name
    for category, data in mappings["categories"].items():
        if category == "General":
            continue
        for keyword in data["keywords"]:
            if keyword in service or keyword in vuln_name:
                logger.info(f"\033[92mCategorized vulnerability as {category} based on keyword: {keyword}\033[0m")
                return category
                
    # Try to match by specific vulnerability mappings
    for category, data in mappings["categories"].items():
        if category == "General":
            continue
        if "vulnerabilities" in data:
            for mapped_vuln, plugin_ids in data["vulnerabilities"].items():
                if mapped_vuln.lower() in vuln_name or any(pid in plugin_id for pid in plugin_ids):
                    logger.info(f"\033[92mCategorized vulnerability as {category} based on vulnerability match\033[0m")
                    return category
    
    logger.info(f"\033[93mCould not categorize vulnerability, using General: {vuln_name}\033[0m")
    return "General"

def parse_nessus_csv(csv_file):
    vulnerabilities = []
    try:
        with open(os.path.join(CONFIG_DIR, "vuln_mappings.json"), "r") as f:
            mappings = json.load(f)

        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            # Get the appropriate field mapping for this CSV format
            field_mapping = get_field_mapping(reader)
            logger.info(f"\033[92mDetected CSV format: {field_mapping}\033[0m")
            
            for row in reader:
                # Skip rows with missing critical fields
                if not all(row.get(field_mapping[key], "") for key in ["ip", "port", "vulnerability"]):
                    logger.warning(f"\033[93mSkipping incomplete row: IP={row.get(field_mapping['ip'], 'N/A')}, Port={row.get(field_mapping['port'], 'N/A')}\033[0m")
                    continue
                
                vuln = {
                    "ip": row.get(field_mapping["ip"], ""),
                    "port": row.get(field_mapping["port"], ""),
                    "service": row.get(field_mapping["service"], ""),
                    "vulnerability": row.get(field_mapping["vulnerability"], ""),
                    "plugin_id": row.get(field_mapping["plugin_id"], ""),
                    "description": row.get(field_mapping["description"], ""),
                    "solution": row.get(field_mapping["solution"], "")
                }
                
                vuln["category"] = categorize_vulnerability(vuln, mappings)
                vulnerabilities.append(vuln)
                
        logger.info(f"\033[92mParsed {len(vulnerabilities)} vulnerabilities from CSV\033[0m")
    except FileNotFoundError:
        logger.error(f"\033[91mCSV file {csv_file} not found\033[0m")
        raise ValidationError(f"CSV file {csv_file} not found")
    except Exception as e:
        logger.error(f"\033[91mError parsing CSV: {e}\033[0m")
        raise ValidationError(f"Error parsing CSV: {e}")
    
    return vulnerabilities