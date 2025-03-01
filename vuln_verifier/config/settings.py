# config/settings.py
# Global settings and configurations

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TOOL_DIR = os.path.join(BASE_DIR, "tools")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
REPORT_FILE = os.path.join(BASE_DIR, "verification_report.xlsx")
LOG_FILE = os.path.join(BASE_DIR, "vuln_verifier.log")