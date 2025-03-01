# core/file_manager.py
# Professional file and directory operations with logging

import os
from config.settings import OUTPUT_DIR, TOOL_DIR
from utils.logger import logger
from utils.exceptions import ScannerError

def setup_directories():
    categories = ["apache", "db", "dns", "ftp", "ike", "nginx", "rdp", "smb", "smtp", "ssh", "ssl", "telnet", "tomcat", "web"]
    try:
        for status in ["verified", "false_positive"]:
            for cat in categories:
                os.makedirs(os.path.join(OUTPUT_DIR, status, cat), exist_ok=True)
        os.makedirs(TOOL_DIR, exist_ok=True)
        logger.info("\033[92mOutput directories set up successfully\033[0m")
    except OSError as e:
        logger.error(f"\033[91mFailed to create directories: {e}\033[0m")
        raise ScannerError(f"Failed to create directories: {e}")
        
# Updated file_manager.py function

def create_poc_folder(status, category, vuln):
    """
    Create a Proof of Concept folder for a vulnerability with proper sanitization.
    
    Args:
        status (str): Verification status (e.g., "Verified", "False Positive")
        category (str): Vulnerability category (e.g., "apache", "ssl")
        vuln (dict): Vulnerability information
        
    Returns:
        str: The path to the created folder
    """
    try:
        # Sanitize vulnerability name to create a valid folder name
        vulnerability_name = sanitize_filename(vuln['vulnerability'])
        ip_address = sanitize_filename(vuln['ip'])
        port = sanitize_filename(vuln['port'])
        
        # Create a folder name with sanitized components
        folder_name = f"{vulnerability_name}_{ip_address}_{port}"
        
        # Ensure the folder name isn't too long (Windows has a 260 character path limit)
        if len(folder_name) > 200:
            folder_name = folder_name[:197] + "..."
        
        # Ensure category is lowercase and valid
        category_lower = category.lower()
        
        # Create the full path
        path = os.path.join(OUTPUT_DIR, status, category_lower, folder_name)
        
        # Create all necessary directories
        os.makedirs(path, exist_ok=True)
        
        # Create a metadata file with the full vulnerability information
        with open(os.path.join(path, "vulnerability_info.json"), "w") as f:
            json.dump(vuln, f, indent=2)
            
        logger.info(f"\033[92mCreated PoC folder: {path}\033[0m")
        return path
    except OSError as e:
        logger.error(f"\033[91mFailed to create PoC folder for {vuln.get('vulnerability', 'Unknown')}: {e}\033[0m")
        
        # Try with a more aggressive sanitization
        try:
            simple_name = f"vuln_{hash(vuln.get('vulnerability', '') + vuln.get('ip', '') + vuln.get('port', ''))}"
            simple_path = os.path.join(OUTPUT_DIR, status, category.lower(), simple_name)
            os.makedirs(simple_path, exist_ok=True)
            
            # Create a metadata file with the full vulnerability information
            with open(os.path.join(simple_path, "vulnerability_info.json"), "w") as f:
                json.dump(vuln, f, indent=2)
                
            logger.warning(f"\033[93mUsed fallback folder name: {simple_path}\033[0m")
            return simple_path
        except OSError as e2:
            # If even the fallback fails, raise an error
            raise ScannerError(f"Failed to create PoC folder: {e2}")

def create_poc_folder(status, category, vuln):
    try:
        folder_name = f"{vuln['vulnerability'].replace(' ', '_')}_{vuln['ip']}_{vuln['port']}"
        path = os.path.join(OUTPUT_DIR, status, category.lower(), folder_name)
        os.makedirs(path, exist_ok=True)
        logger.info(f"\033[92mCreated PoC folder: {path}\033[0m")
        return path
    except OSError as e:
        logger.error(f"\033[91mFailed to create PoC folder for {vuln['vulnerability']}: {e}\033[0m")
        raise ScannerError(f"Failed to create PoC folder: {e}")