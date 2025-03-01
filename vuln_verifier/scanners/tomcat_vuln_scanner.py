# scanners/tomcat_vuln_scanner.py
# Tomcat vulnerability scanning

import os
from config.settings import TOOL_DIR
from core.file_manager import create_poc_folder
from scanners.base_scanner import BaseScanner
from utils.logger import logger
from utils.exceptions import ScannerError

class TomcatVulnScanner(BaseScanner):
    def verify(self, vuln):
        ip, port = vuln["ip"], vuln["port"]
        vuln_name = vuln["vulnerability"].lower()
        output_dir = create_poc_folder("Verified", "tomcat", vuln)
        nmap_output = os.path.join(output_dir, "nmap_scan")

        try:
            script = "http-tomcat-cve*" if "manager" in vuln_name else "http-default-pages"
            cmd = f"nmap -p {port} --script {script} {ip} -oA {nmap_output}"
            self._run_command(cmd, cwd=TOOL_DIR, output_file=f"{nmap_output}.txt")
            
            with open(f"{nmap_output}.xml", "r") as f:
                output = f.read().lower()
                if vuln_name in output or "vulnerable" in output:
                    return "Verified", output_dir
            return "False Positive", output_dir
        except ScannerError as e:
            with open(os.path.join(output_dir, "manual_steps.txt"), "w") as f:
                f.write(f"Manual Check Required: Run '{cmd}' and check for {vuln_name}.")
            logger.error(f"\033[91mTomcat scan failed for {ip}:{port}: {e}\033[0m")
            return "Manual Check Required", output_dir