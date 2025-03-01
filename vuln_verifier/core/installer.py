# core/installer.py
# Professional tool installation management with retries

import os
import json
import subprocess
import requests
import zipfile
import time
import sys
from pathlib import Path
from config.settings import TOOL_DIR, CONFIG_DIR
from utils.logger import logger
from utils.exceptions import ScannerError

MAX_RETRIES = 3
SKIP_INSTALL = os.environ.get('SKIP_TOOL_INSTALL', 'False').lower() in ('true', '1', 't')

def download_file(url, filepath, retries=MAX_RETRIES):
    """Download a file with retry logic"""
    for attempt in range(retries):
        try:
            logger.info(f"\033[93mAttempt {attempt + 1}/{retries}: Downloading {url}...\033[0m")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Create parent directories if they don't exist
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"\033[92mDownload successful: {url}\033[0m")
            return
        except requests.RequestException as e:
            logger.error(f"\033[91mDownload failed: {e}\033[0m")
            if attempt < retries - 1:
                wait_time = 2 * (attempt + 1)  # Exponential backoff
                logger.info(f"\033[93mWaiting {wait_time} seconds before retry...\033[0m")
                time.sleep(wait_time)
            else:
                raise ScannerError(f"Failed to download {url} after {retries} attempts")

def extract_zip(zip_path, extract_to):
    """Extract a zip file to the specified directory"""
    try:
        logger.info(f"\033[93mExtracting {zip_path} to {extract_to}...\033[0m")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)
        logger.info(f"\033[92mExtraction successful\033[0m")
    except zipfile.BadZipFile as e:
        logger.error(f"\033[91mBad zip file: {e}\033[0m")
        raise ScannerError(f"Failed to extract {zip_path}: Bad zip file")
    except Exception as e:
        logger.error(f"\033[91mExtraction failed: {e}\033[0m")
        raise ScannerError(f"Failed to extract {zip_path}: {e}")

def install_tools():
    """Install the required security tools"""
    os.makedirs(TOOL_DIR, exist_ok=True)
    
    # Add tools directory to PATH
    tools_path = os.path.abspath(TOOL_DIR)
    if tools_path not in os.environ["PATH"]:
        os.environ["PATH"] = f"{tools_path}{os.pathsep}{os.environ['PATH']}"
    
    if SKIP_INSTALL:
        logger.info("\033[93mSkipping tool installation (SKIP_TOOL_INSTALL=True)\033[0m")
        return

    try:
        with open(os.path.join(CONFIG_DIR, "tool_config.json"), "r") as f:
            tool_config = json.load(f)["tools"]
    except FileNotFoundError:
        logger.error(f"\033[91mtool_config.json not found in {CONFIG_DIR}\033[0m")
        raise ScannerError(f"tool_config.json not found in {CONFIG_DIR}")
    except json.JSONDecodeError:
        logger.error(f"\033[91mInvalid JSON in tool_config.json\033[0m")
        raise ScannerError("Invalid JSON in tool_config.json")

    for tool, config in tool_config.items():
        # Check if tool is already installed
        try:
            if "check_cmd" in config:
                logger.info(f"\033[93mChecking if {tool} is already installed...\033[0m")
                subprocess.check_output(config["check_cmd"], shell=True, cwd=TOOL_DIR, stderr=subprocess.STDOUT)
                logger.info(f"\033[92m{tool} already installed\033[0m")
                continue
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.info(f"\033[93m{tool} not found, proceeding with installation...\033[0m")
        
        # Install the tool
        try:
            if "url" in config:
                # Determine file extension
                is_msi = config["url"].endswith(".msi")
                is_exe = config["url"].endswith(".exe")
                extension = ".msi" if is_msi else ".exe" if is_exe else ".zip"
                
                filepath = os.path.join(TOOL_DIR, f"{tool}{extension}")
                download_file(config["url"], filepath)
                
                if "install_cmd" in config:
                    logger.info(f"\033[93mRunning installer for {tool}...\033[0m")
                    subprocess.run(config["install_cmd"], shell=True, check=True, cwd=TOOL_DIR)
                    # Only remove the installer file if installation succeeded
                    if os.path.exists(filepath):
                        os.remove(filepath)
                elif "extract_to" in config:
                    extract_dir = os.path.join(TOOL_DIR, config["extract_to"]) if "tools" not in config["extract_to"] else config["extract_to"]
                    extract_zip(filepath, extract_dir)
                    # Only remove the zip file if extraction succeeded
                    if os.path.exists(filepath):
                        os.remove(filepath)
            
            elif "pip_install" in config:
                logger.info(f"\033[93mInstalling {tool} using pip...\033[0m")
                subprocess.run([sys.executable, "-m", "pip", "install", config["pip_install"]], check=True)
            
            logger.info(f"\033[92m{tool} installed successfully\033[0m")
            
            # Verify installation
            if "check_cmd" in config:
                subprocess.check_output(config["check_cmd"], shell=True, cwd=TOOL_DIR, stderr=subprocess.STDOUT)
                logger.info(f"\033[92m{tool} installation verified\033[0m")
            
        except Exception as e:
            logger.error(f"\033[91mFailed to install {tool}: {e}\033[0m")
            # Continue with other tools instead of stopping completely
            logger.warning(f"\033[93mContinuing with other tools...\033[0m")