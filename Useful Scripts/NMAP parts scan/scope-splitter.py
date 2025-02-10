#!/usr/bin/env python3

import argparse
import asyncio
import ipaddress
import logging
import os
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Set, Tuple
import json
import shutil
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.logging import RichHandler
from rich.panel import Panel

class NetworkScanner:
    def __init__(self, config_file: str = "scanner_config.json"):
        self.console = Console()
        self.setup_logging()
        self.config = self.load_config(config_file)
        self.setup_directories()
        
    def setup_logging(self):
        """Configure logging with rich formatting"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(rich_tracebacks=True)]
        )
        self.logger = logging.getLogger("network_scanner")

    def load_config(self, config_file: str) -> dict:
        """Load configuration from JSON file or create default"""
        default_config = {
            "ips_per_file": 20,
            "subnets_per_file": 3,
            "output_dir": "output",
            "temp_dir": "temp",
            "nmap_options": {
                "basic": "-sS -Pn -p- -T4",
                "timing": "--max-rtt-timeout 100ms --max-retries 3",
                "rate": "--min-rate 450 --max-rate 15000"
            },
            "excluded_ports": [],
            "scan_delay": 2
        }

        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return {**default_config, **json.load(f)}
            except json.JSONDecodeError:
                self.logger.warning(f"Invalid config file, using defaults")
                return default_config
        else:
            # Save default config
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config

    def setup_directories(self):
        """Create necessary directories"""
        for directory in [self.config['output_dir'], self.config['temp_dir']]:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def find_nmap(self) -> str:
        """Locate nmap executable"""
        if platform.system() == "Windows":
            common_paths = [
                r"C:\Program Files\Nmap\nmap.exe",
                r"C:\Program Files (x86)\Nmap\nmap.exe"
            ]
            for path in common_paths:
                if os.path.exists(path):
                    return path
            return "nmap.exe"  # Rely on PATH
        else:
            nmap_path = shutil.which("nmap")
            if nmap_path:
                return nmap_path
            return "nmap"  # Rely on PATH

    async def validate_nmap(self, nmap_path: str) -> bool:
        """Validate nmap installation"""
        try:
            process = await asyncio.create_subprocess_exec(
                nmap_path, "-V",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return process.returncode == 0
        except Exception as e:
            self.logger.error(f"Error validating Nmap: {e}")
            return False

    def validate_ip(self, ip: str) -> bool:
        """Validate IP address or subnet"""
        try:
            if '/' in ip:
                ipaddress.ip_network(ip, strict=False)
            else:
                ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    def parse_scope_file(self, scope_file: str) -> Tuple[Set[str], Set[str]]:
        """Parse scope file and validate IP addresses/networks"""
        ips = set()
        subnets = set()
        
        try:
            with open(scope_file, 'r') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
                
            for line in lines:
                if self.validate_ip(line):
                    if '/' in line:
                        subnets.add(line)
                    else:
                        ips.add(line)
                else:
                    self.logger.warning(f"Invalid entry skipped: {line}")
                    
        except FileNotFoundError:
            self.logger.error(f"Scope file '{scope_file}' not found")
            sys.exit(1)
            
        return ips, subnets

    def split_targets(self, ips: Set[str], subnets: Set[str]) -> List[str]:
        """Split targets into separate files"""
        output_files = []
        
        # Split IPs
        ip_list = list(ips)
        for i in range(0, len(ip_list), self.config['ips_per_file']):
            chunk = ip_list[i:i + self.config['ips_per_file']]
            filename = f"{self.config['output_dir']}/scope_{i//self.config['ips_per_file'] + 1}.txt"
            with open(filename, 'w') as f:
                f.write('\n'.join(chunk))
            output_files.append(filename)

        # Split subnets
        subnet_list = list(subnets)
        for i in range(0, len(subnet_list), self.config['subnets_per_file']):
            chunk = subnet_list[i:i + self.config['subnets_per_file']]
            filename = f"{self.config['output_dir']}/subnet_{i//self.config['subnets_per_file'] + 1}.txt"
            with open(filename, 'w') as f:
                f.write('\n'.join(chunk))
            output_files.append(filename)

        return output_files

    async def run_scan(self, target_file: str, nmap_path: str):
        """Run Nmap scan for a target file"""
        output_base = f"{self.config['output_dir']}/scan_{Path(target_file).stem}"
        
        cmd = [
            nmap_path,
            *self.config['nmap_options']['basic'].split(),
            *self.config['nmap_options']['timing'].split(),
            *self.config['nmap_options']['rate'].split(),
            "-iL", target_file,
            "-oA", output_base
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            self.logger.info(f"Started scan for {target_file}")
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self.logger.info(f"Completed scan for {target_file}")
            else:
                self.logger.error(f"Scan failed for {target_file}: {stderr.decode()}")
                
        except Exception as e:
            self.logger.error(f"Error running scan for {target_file}: {e}")

    async def main(self, scope_file: str):
        """Main execution flow"""
        self.console.print(Panel.fit(
            "[bold blue]Advanced Network Scanner[/bold blue]\n"
            "Version 2.0",
            title="Welcome"
        ))

        # Find and validate Nmap
        nmap_path = self.find_nmap()
        if not await self.validate_nmap(nmap_path):
            self.logger.error("Nmap not found or not working properly")
            sys.exit(1)

        # Parse scope file
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Parsing scope file...", total=None)
            ips, subnets = self.parse_scope_file(scope_file)
            progress.update(task, completed=True)

        self.logger.info(f"Found {len(ips)} IPs and {len(subnets)} subnets")

        # Split targets
        target_files = self.split_targets(ips, subnets)
        self.logger.info(f"Created {len(target_files)} target files")

        # Run scans
        self.console.print("\n[bold green]Starting scans...[/bold green]")
        scan_tasks = [self.run_scan(tf, nmap_path) for tf in target_files]
        await asyncio.gather(*scan_tasks)

        self.console.print(Panel.fit(
            "[bold green]Scanning completed![/bold green]\n"
            f"Results saved in: {self.config['output_dir']}",
            title="Scan Status"
        ))

def create_example_scope():
    """Create an example scope file if it doesn't exist"""
    if not os.path.exists("scope.txt"):
        example_content = """# Example scope file
# Individual IPs:
192.168.1.1
10.0.0.1
172.16.1.1

# Subnets:
192.168.0.0/24
10.0.0.0/16
172.16.0.0/12"""
        with open("scope.txt", "w") as f:
            f.write(example_content)
        print("Created example scope.txt file")

def main():
    parser = argparse.ArgumentParser(description="Advanced Network Scanner")
    parser.add_argument("scope_file", nargs="?", default="scope.txt",
                      help="File containing IPs and subnets to scan (default: scope.txt)")
    parser.add_argument("--config", default="scanner_config.json", 
                      help="Path to configuration file")
    parser.add_argument("--create-example", action="store_true",
                      help="Create an example scope.txt file")
    args = parser.parse_args()

    if args.create_example:
        create_example_scope()
        return

    if not os.path.exists(args.scope_file):
        print(f"Error: {args.scope_file} not found!")
        print("Use --create-example to create an example scope file")
        return

    scanner = NetworkScanner(args.config)
    asyncio.run(scanner.main(args.scope_file))

if __name__ == "__main__":
    main()
