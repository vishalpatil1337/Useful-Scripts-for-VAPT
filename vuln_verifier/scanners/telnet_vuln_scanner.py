# scanners/telnet_vuln_scanner.py
# Telnet vulnerability scanning

import os
from config.settings import TOOL_DIR
from core.file_manager import create_poc_folder
from scanners.base_scanner import BaseScanner
from utils.logger import logger
from utils.exceptions import ScannerError

class TelnetVulnScanner(BaseScanner):
    def verify(self, vuln):
        ip, port = vuln["ip"], vuln["port"]
        vuln_name = vuln["vulnerability"].lower()
        output_dir = create_poc_folder("Verified", "telnet", vuln)
        telnet_output = os.path.join(output_dir, "telnet_output.txt")

        try:
            cmd = f"echo QUIT | telnet {ip} {port}"
            self._run_command(cmd, cwd=TOOL_DIR, output_file=telnet_output)
            
            with open(telnet_output, "r") as f:
                output = f.read().lower()
                if "connected" in output or "login" in output:
                    return "Verified", output_dir
            return "False Positive", output_dir
        except ScannerError as e:
            with open(os.path.join(output_dir, "manual_steps.txt"), "w") as f:
                f.write(f"Manual Check Required: Run 'telnet {ip} {port}' and check for {vuln_name}.")
            logger.error(f"\033[91mTelnet scan failed for {ip}:{port}: {e}\033[0m")
            return "Manual Check Required", output_dir