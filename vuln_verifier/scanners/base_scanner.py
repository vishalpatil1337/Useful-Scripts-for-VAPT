# scanners/base_scanner.py
# Enhanced abstract base scanner class with improved error handling

import os
import subprocess
from abc import ABC, abstractmethod
from utils.exceptions import ScannerError
from utils.helpers import get_tool_path, check_nmap_script_exists, get_fallback_nmap_script
from utils.logger import logger

class BaseScanner(ABC):
    @abstractmethod
    def verify(self, vuln):
        """
        Verify a vulnerability.
        
        Args:
            vuln (dict): Vulnerability information
            
        Returns:
            tuple: (status, poc_path) where status is one of "Verified", "False Positive", or "Manual Check Required"
        """
        pass

    def _run_command(self, cmd, cwd=None, output_file=None, timeout=300):
        """
        Run a shell command with improved error handling.
        
        Args:
            cmd (str): Command to run
            cwd (str, optional): Working directory
            output_file (str, optional): File to write command output to
            timeout (int, optional): Timeout in seconds
            
        Returns:
            bool: True if the command was successful
            
        Raises:
            ScannerError: If the command fails
        """
        try:
            # Check for tool paths in the command and replace them
            cmd_parts = cmd.split()
            if cmd_parts:
                tool = cmd_parts[0]
                tool_path = get_tool_path(tool)
                if tool_path:
                    cmd = cmd.replace(tool, f'"{tool_path}"', 1)
            
            # Check for nmap script and use fallback if needed
            if "nmap" in cmd and "--script" in cmd:
                script_parts = cmd.split("--script")
                if len(script_parts) > 1:
                    script_name = script_parts[1].strip().split()[0]
                    if not check_nmap_script_exists(script_name):
                        fallback = get_fallback_nmap_script(script_name)
                        if fallback:
                            cmd = cmd.replace(f"--script {script_name}", f"--script {fallback}")
                            logger.info(f"\033[93mReplaced script {script_name} with fallback {fallback}\033[0m")
            
            logger.info(f"\033[93mRunning command: {cmd}\033[0m")
            
            if output_file:
                with open(output_file, "w") as f:
                    result = subprocess.run(
                        cmd, 
                        shell=True, 
                        check=True, 
                        cwd=cwd, 
                        stdout=f, 
                        stderr=subprocess.STDOUT,
                        timeout=timeout
                    )
            else:
                result = subprocess.run(
                    cmd, 
                    shell=True, 
                    check=True, 
                    cwd=cwd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT,
                    timeout=timeout
                )
            
            return True
        except subprocess.CalledProcessError as e:
            # Log the error with the command output if available
            error_msg = f"Command failed: {cmd}"
            if e.output:
                error_msg += f" - {e.output.decode('utf-8', errors='replace')}"
            
            # Write error output to file if requested
            if output_file:
                try:
                    with open(output_file, "a") as f:
                        f.write(f"\n\nERROR: {error_msg}")
                except:
                    pass
            
            # If this is a nmap script error, try to provide more context
            if "nmap" in cmd and "NSE: failed to initialize" in str(e.output):
                error_msg += " (Nmap script not found or failed to initialize)"
            
            raise ScannerError(error_msg)
        except subprocess.TimeoutExpired:
            logger.warning(f"\033[93mCommand timed out after {timeout} seconds: {cmd}\033[0m")
            
            # Write timeout message to file if requested
            if output_file:
                try:
                    with open(output_file, "a") as f:
                        f.write(f"\n\nERROR: Command timed out after {timeout} seconds")
                except:
                    pass
            
            raise ScannerError(f"Command timed out after {timeout} seconds: {cmd}")
        except Exception as e:
            raise ScannerError(f"Command failed: {cmd} - {str(e)}")