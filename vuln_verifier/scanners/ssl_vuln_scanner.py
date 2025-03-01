# scanners/ssl_vuln_scanner.py
# SSL/TLS vulnerability scanning with specific Nessus checks

import os
import subprocess
from config.settings import TOOL_DIR
from core.file_manager import create_poc_folder
from scanners.base_scanner import BaseScanner
from utils.logger import logger
from utils.exceptions import ScannerError

class SSLVulnScanner(BaseScanner):
    def verify(self, vuln):
        ip, port = vuln["ip"], vuln["port"]
        vuln_name = vuln["vulnerability"].lower()
        plugin_id = vuln["plugin_id"]
        status = "Verified" if plugin_id in ["26928", "42873", "15901", "88881", "57582"] else "False Positive"
        output_dir = create_poc_folder(status, "ssl", vuln)
        sslscan_output = os.path.join(output_dir, "sslscan_output.txt")

        try:
            cmd = f"sslscan.exe {ip}:{port}"
            self._run_command(cmd, cwd=TOOL_DIR, output_file=sslscan_output)
            
            with open(sslscan_output, "r") as f:
                output = f.read().lower()
                if "26928" in plugin_id or "42873" in plugin_id:  # SSL/TLS Weak Ciphers
                    if "rc4" in output or "md5" in output or "sha1" in output:
                        return "Verified", output_dir
                elif "15901" in plugin_id:  # SSLv3 Enabled
                    if "sslv3" in output:
                        return "Verified", output_dir
                elif "88881" in plugin_id:  # TLS 1.0 Enabled
                    if "tlsv1.0" in output:
                        return "Verified", output_dir
                elif "57582" in plugin_id:  # Self-Signed Certificate
                    if "self-signed" in output:
                        return "Verified", output_dir
            return "False Positive", output_dir
        except ScannerError as e:
            with open(os.path.join(output_dir, "manual_steps.txt"), "w") as f:
                f.write(f"Manual Check Required: Run 'sslscan {ip}:{port}' and check for {vuln_name}.")
            logger.error(f"\033[91mSSL scan failed for {ip}:{port}: {e}\033[0m")
            return "Manual Check Required", output_dir