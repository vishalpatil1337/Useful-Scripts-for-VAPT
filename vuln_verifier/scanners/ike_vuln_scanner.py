# scanners/ike_vuln_scanner.py
# IKE vulnerability scanning

import os
from config.settings import TOOL_DIR
from core.file_manager import create_poc_folder
from scanners.base_scanner import BaseScanner
from utils.logger import logger
from utils.exceptions import ScannerError

class IKEVulnScanner(BaseScanner):
    def verify(self, vuln):
        ip = vuln["ip"]
        vuln_name = vuln["vulnerability"].lower()
        output_dir = create_poc_folder("Verified", "ike", vuln)
        ike_output = os.path.join(output_dir, "ike-scan_output.txt")

        try:
            cmd = f"ike-scan.exe -M {ip}"
            self._run_command(cmd, cwd=TOOL_DIR, output_file=ike_output)
            
            with open(ike_output, "r") as f:
                output = f.read().lower()
                if "aggressive" in output or "weak" in output:
                    return "Verified", output_dir
            return "False Positive", output_dir
        except ScannerError as e:
            with open(os.path.join(output_dir, "manual_steps.txt"), "w") as f:
                f.write(f"Manual Check Required: Run 'ike-scan -M {ip}' and check for {vuln_name}.")
            logger.error(f"\033[91mIKE scan failed for {ip}: {e}\033[0m")
            return "Manual Check Required", output_dir