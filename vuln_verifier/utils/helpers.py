# utils/helpers.py
# Professional utility functions for the vulnerability verifier tool

import os
import re
import json
import requests
import subprocess
from pathlib import Path
from utils.logger import logger
from config.settings import CONFIG_DIR

def sanitize_filename(name):
    """
    Convert a string to a valid filename by removing invalid characters
    and replacing them with underscores.
    
    Args:
        name (str): The input string to sanitize
        
    Returns:
        str: A sanitized filename string
    """
    # Replace characters that are invalid in filenames
    invalid_chars = r'[\\/*?:"<>|]'
    sanitized = re.sub(invalid_chars, '_', name)
    
    # Replace multiple spaces or underscores with a single underscore
    sanitized = re.sub(r'[\s_]+', '_', sanitized)
    
    # Limit filename length to 200 characters to avoid path length issues
    if len(sanitized) > 200:
        sanitized = sanitized[:197] + "..."
    
    # Ensure filename is not empty
    sanitized = sanitized.strip() or "unnamed"
    
    return sanitized

def check_url_status(url):
    """
    Check if a URL is valid and accessible.
    
    Args:
        url (str): The URL to check
        
    Returns:
        bool: True if the URL is valid and accessible, False otherwise
    """
    try:
        # Make a HEAD request to the URL
        response = requests.head(url, timeout=5, allow_redirects=True)
        
        # Check if the response is successful (2xx status code)
        if response.status_code >= 200 and response.status_code < 300:
            return True
        else:
            logger.warning(f"\033[93mURL {url} returned status code {response.status_code}\033[0m")
            return False
    except requests.RequestException as e:
        logger.warning(f"\033[93mFailed to check URL {url}: {e}\033[0m")
        return False

def check_nmap_script_exists(script_name):
    """
    Check if an Nmap script exists on the system.
    
    Args:
        script_name (str): The name of the Nmap script to check
        
    Returns:
        bool: True if the script exists, False otherwise
    """
    try:
        # Load tool configuration
        tool_config_path = os.path.join(CONFIG_DIR, "tool_path_config.json")
        if os.path.exists(tool_config_path):
            with open(tool_config_path, 'r') as f:
                config = json.load(f)
                
                # Check if script is in available scripts list
                if script_name.endswith('*'):
                    for available_script in config['nmap_scripts']['available']:
                        if script_name.replace('*', '') in available_script:
                            return True
                    
                    # Check if there's a fallback for this script
                    if script_name in config['nmap_scripts']['fallback']:
                        fallback = config['nmap_scripts']['fallback'][script_name]
                        logger.info(f"\033[93mUsing fallback script '{fallback}' for '{script_name}'\033[0m")
                        return True
                    
                    return False
                else:
                    return script_name in config['nmap_scripts']['available']
        
        # If no configuration file, try to run a command to list available scripts
        nmap_path = get_tool_path('nmap')
        if not nmap_path:
            return False
            
        # Use --script-help to check if the script exists
        cmd = f"{nmap_path} --script-help {script_name}"
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Check if the output contains information about the script
        return "Categories:" in result.stdout.decode() and "SCRIPT LIBRARY" in result.stdout.decode()
    except Exception as e:
        logger.warning(f"\033[93mError checking Nmap script {script_name}: {e}\033[0m")
        return False

def get_tool_path(tool_name):
    """
    Get the path to a tool from the configuration, or find it on the system.
    
    Args:
        tool_name (str): The name of the tool to find
        
    Returns:
        str: The path to the tool, or None if not found
    """
    # First, check if there's a configuration file with tool paths
    tool_config_path = os.path.join(CONFIG_DIR, "tool_path_config.json")
    if os.path.exists(tool_config_path):
        try:
            with open(tool_config_path, 'r') as f:
                config = json.load(f)
                if config['tool_paths'][tool_name]['path']:
                    # If the path is defined in the config, use it
                    path = config['tool_paths'][tool_name]['path']
                    
                    # Verify the tool exists at the specified path
                    if os.path.isfile(path):
                        return path
        except (KeyError, json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"\033[93mError reading tool path from config: {e}\033[0m")
            pass
    
    # If we get here, the tool wasn't in the config or wasn't where we expected
    # Try to find it on the system
    try:
        # Check if the tool is in the PATH
        which_cmd = "where" if os.name == "nt" else "which"
        result = subprocess.run([which_cmd, tool_name], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               text=True)
        
        if result.returncode == 0:
            # The tool was found, return the path
            return result.stdout.strip().split('\n')[0]
    except Exception as e:
        logger.warning(f"\033[93mError finding tool {tool_name} on the system: {e}\033[0m")
        
    # If we get here, the tool wasn't found
    return None

def get_fallback_nmap_script(script_name):
    """
    Get a fallback script name for an Nmap script that doesn't exist.
    
    Args:
        script_name (str): The name of the Nmap script to find a fallback for
        
    Returns:
        str: The name of a fallback script, or None if no fallback is available
    """
    # Load tool configuration
    tool_config_path = os.path.join(CONFIG_DIR, "tool_path_config.json")
    if os.path.exists(tool_config_path):
        try:
            with open(tool_config_path, 'r') as f:
                config = json.load(f)
                
                # Check if there's a fallback for this script
                if script_name in config['nmap_scripts']['fallback']:
                    return config['nmap_scripts']['fallback'][script_name]
        except (KeyError, json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"\033[93mError reading nmap script fallbacks from config: {e}\033[0m")
    
    # Default fallbacks for common script types
    fallbacks = {
        "postgres-vuln*": "banner-grab",
        "mysql-vuln*": "banner-grab",
        "ssh-vuln-cve*": "ssh-auth-methods",
        "http-traversal": "http-vuln-*",
        "http-xss": "http-vuln-*",
        "http-sql-injection": "http-vuln-*"
    }
    
    if script_name in fallbacks:
        return fallbacks[script_name]
    
    # For other scripts, default to a basic banner grab
    return "banner-grab"