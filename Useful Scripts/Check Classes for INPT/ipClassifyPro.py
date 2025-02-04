#!/usr/bin/env python3
"""
Comprehensive IP Address and Subnet Classification Analyzer
"""

import ipaddress
import logging
from typing import List, Dict, Tuple

class IPSubnetClassifier:
    def __init__(self, scope_file: str):
        """Initialize classifier with input file path."""
        self.scope_file = scope_file
        self.classification = {
            'A': {'total_ips': 0, 'networks': []},
            'B': {'total_ips': 0, 'networks': []},
            'C': {'total_ips': 0, 'networks': []},
            'Invalid': {'total_ips': 0, 'networks': []}
        }
        self.total_input_lines = 0

        logging.basicConfig(
            level=logging.INFO, 
            format='%(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _clean_network_str(self, network_str: str) -> str:
        """Clean network string by removing special characters."""
        return network_str.strip().rstrip('Â').rstrip()

    def _determine_class(self, network: ipaddress.IPv4Network) -> str:
        """Determine network class based on first octet."""
        first_octet = int(str(network.network_address).split('.')[0])

        if 0 <= first_octet <= 127:
            return 'A'
        elif 128 <= first_octet <= 191:
            return 'B'
        elif 192 <= first_octet <= 223:
            return 'C'
        return 'Invalid'

    def process_network(self, network_str: str):
        """Process and classify network/IP."""
        # Increment total input lines
        self.total_input_lines += 1

        # Clean the network string first
        cleaned_network_str = self._clean_network_str(network_str)

        try:
            # Handle both IP and network notations
            network = ipaddress.ip_network(cleaned_network_str, strict=False)

            # Determine network class
            net_class = self._determine_class(network)

            # Store network and update counts
            if net_class != 'Invalid':
                self.classification[net_class]['networks'].append(cleaned_network_str)
                self.classification[net_class]['total_ips'] += 1
            else:
                self.classification['Invalid']['networks'].append(cleaned_network_str)
                self.classification['Invalid']['total_ips'] += 1

        except ValueError:
            self.classification['Invalid']['networks'].append(cleaned_network_str)
            self.classification['Invalid']['total_ips'] += 1

    def analyze_scope(self):
        """Read and analyze scope file."""
        with open(self.scope_file, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    self.process_network(line)

    def print_report(self):
        """Generate comprehensive classification report."""
        total_classified_ips = (
            self.classification['A']['total_ips'] + 
            self.classification['B']['total_ips'] + 
            self.classification['C']['total_ips']
        )

        # Print Network Classification
        print("Network Classification:")
        for cls in ['A', 'B', 'C']:
            print(f"\n{cls} Class:")
            print(f"Total IPs/Networks: {self.classification[cls]['total_ips']}")

            print("\nNetworks:")
            for network in self.classification[cls]['networks']:
                print(f"  {network}")

        # Print Invalid entries if any
        if self.classification['Invalid']['total_ips'] > 0:
            print("\nInvalid Entries:")
            for invalid in self.classification['Invalid']['networks']:
                print(f"  {invalid}")

        # Final Summary
        print("\nClassification Summary:")
        print(f"Class A total IPs/Subnets: {self.classification['A']['total_ips']}")
        print(f"Class B total IPs/Subnets: {self.classification['B']['total_ips']}")
        print(f"Class C total IPs/Subnets: {self.classification['C']['total_ips']}")
        print(f"Total IPs/Subnets in Scope File: {self.total_input_lines}")

        # Verification
        print("\nVerification:")
        print(f"Total Classified IPs (A+B+C): {total_classified_ips}")
        if total_classified_ips == self.total_input_lines - self.classification['Invalid']['total_ips']:
            print("\u2713 All Valid IPs/Subnets Covered")
        else:
            print("\u2717 Not All IPs/Subnets Covered")
            print(f"  Unclassified: {self.total_input_lines - total_classified_ips - self.classification['Invalid']['total_ips']}")

def main():
    """Main execution function."""
    try:
        classifier = IPSubnetClassifier("scope.txt")
        classifier.analyze_scope()
        classifier.print_report()
    except Exception as e:
        print(f"Error processing file: {e}")

if __name__ == "__main__":
    main()
