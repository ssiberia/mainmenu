#!/usr/bin/env python3
"""
IP Information Tool
Gather comprehensive information about IPv4 and IPv6 addresses from various sources.
"""

import requests
import json
import time
import os
import socket
import ipaddress
from ipwhois import IPWhois
from termcolor import colored
from datetime import datetime

# API rate limiting
API_WAIT_TIME = 0.5  # seconds between API calls

class IPInfoTool:
    """Comprehensive IP information gathering tool"""
    
    def __init__(self):
        """Initialize the IP info tool"""
        self.results = []
        self.headers = {
            'User-Agent': 'IPInfoTool/1.0 (Network Troubleshooting Utility)'
        }
    
    def is_valid_ip(self, ip):
        """Validate if string is a valid IP address (v4 or v6)"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def get_rdap_info(self, ip):
        """Get comprehensive RDAP information for an IP"""
        try:
            ipwhois = IPWhois(ip)
            result = ipwhois.lookup_rdap(depth=2)
            return result
        except Exception as e:
            return f"RDAP lookup error: {e}"
    
    def get_bgp_info(self, ip):
        """Query BGP.tools API for routing information"""
        try:
            response = requests.get(f"https://api.bgpview.io/ip/{ip}", headers=self.headers)
            time.sleep(API_WAIT_TIME)  # Rate limiting
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    return data.get('data', {})
            
            return {}
        except Exception:
            return {}
    
    def get_geo_info(self, ip):
        """Get detailed geolocation information"""
        try:
            response = requests.get(f"https://ipinfo.io/{ip}/json", headers=self.headers)
            time.sleep(API_WAIT_TIME)  # Rate limiting
            
            if response.status_code == 200:
                return response.json()
            
            return {}
        except Exception:
            return {}
    
    def get_ripe_stat(self, ip):
        """Query RIPE Stat API for additional network information"""
        try:
            response = requests.get(
                f"https://stat.ripe.net/data/prefix-overview/data.json?resource={ip}", 
                headers=self.headers
            )
            time.sleep(API_WAIT_TIME)  # Rate limiting
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('data', {})
                
                # Default values to prevent NoneType errors
                result.setdefault('allocations', [])
                
                # Get abuse contact if possible
                try:
                    abuse_response = requests.get(
                        f"https://stat.ripe.net/data/abuse-contact-finder/data.json?resource={ip}",
                        headers=self.headers
                    )
                    if abuse_response.status_code == 200:
                        abuse_data = abuse_response.json().get('data', {})
                        result['abuse_contacts'] = abuse_data.get('abuse_contacts', [])
                except Exception:
                    result['abuse_contacts'] = []
                
                return result
            
            return {'allocations': [], 'abuse_contacts': []}
        except Exception:
            return {'allocations': [], 'abuse_contacts': []}
    
    def get_dns_info(self, ip):
        """Get reverse DNS information"""
        try:
            hostname, _, _ = socket.gethostbyaddr(ip)
            return hostname
        except (socket.herror, socket.gaierror):
            return None
    
    def process_ip(self, ip):
        """Process a single IP address with all lookups"""
        if not self.is_valid_ip(ip):
            return {
                'ip': ip,
                'error': "Invalid IP address format"
            }
        
        result = {'ip': ip, 'timestamp': datetime.now().isoformat()}
        
        try:
            # Get RDAP information (this includes basic network info)
            rdap_result = self.get_rdap_info(ip)
            if isinstance(rdap_result, str):  # Error message
                result['error'] = rdap_result
                return result
            
            # Extract key information from RDAP (with defaults to avoid None)
            result['asn'] = rdap_result.get('asn')
            result['asn_description'] = rdap_result.get('asn_description')
            result['network'] = rdap_result.get('network', {})
            result['entities'] = rdap_result.get('entities', [])
            result['objects'] = rdap_result.get('objects', {})
            
            # Get BGP information
            result['bgp_info'] = self.get_bgp_info(ip)
            
            # Get geolocation information
            result['geo_info'] = self.get_geo_info(ip)
            
            # Get RIPE Stat information
            result['ripe_info'] = self.get_ripe_stat(ip)
            
            # Get reverse DNS
            reverse_dns = self.get_dns_info(ip)
            if reverse_dns:
                result['reverse_dns'] = reverse_dns
            
            return result
        except Exception as e:
            return {
                'ip': ip,
                'error': f"Error processing IP: {str(e)}"
            }
    
    def display_ip_info(self, result):
        """Display IP information in a simple table format"""
        ip = result.get('ip')
        
        # Print IP header
        print("\n")
        print(colored(f"IP: {ip}", "cyan"))
        
        if 'error' in result:
            print(colored(f"Error: {result['error']}", "red"))
            return
        
        try:
            # Build table header
            table_width = 90
            print("+" + "-" * table_width + "+")
            property_col_width = 25
            value_col_width = table_width - property_col_width - 3  # 3 for the borders and space
            print(f"| {'Property':{property_col_width}} | {'Value':{value_col_width}} |")
            print("+" + "-" * table_width + "+")
            
            # Helper function to print a row
            def print_row(name, value):
                if value is None:
                    value = ""
                value_str = str(value)
                # Handle long values by truncating or word-wrapping
                if len(value_str) > value_col_width:
                    print(f"| {name:{property_col_width}} | {value_str[:value_col_width-3]}... |")
                else:
                    print(f"| {name:{property_col_width}} | {value_str:{value_col_width}} |")
            
            # Reverse DNS
            if 'reverse_dns' in result:
                print_row("Reverse DNS", result['reverse_dns'])
            
            # ASN information
            asn = result.get('asn')
            asn_description = result.get('asn_description')
            if asn and asn_description:
                print_row("ASN", f"{asn} - {asn_description}")
                print_row("PeeringDB URL", f"https://www.peeringdb.com/asn/{asn}")
            
            # Network information
            network = result.get('network', {})
            if network:
                prefix = network.get('cidr')
                if prefix:
                    print_row("Prefix", prefix)
                    print_row("BGP Tools URL", f"https://bgp.tools/prefix/{prefix}")
                
                if 'name' in network:
                    print_row("Network Name", network['name'])
                
                if 'country' in network:
                    print_row("Country", network['country'])
                
                if 'start_address' in network and 'end_address' in network:
                    print_row("IP Range", f"{network['start_address']} - {network['end_address']}")
            
            # Geolocation Information
            geo_info = result.get('geo_info', {})
            if geo_info:
                if 'city' in geo_info:
                    print_row("City", geo_info['city'])
                if 'region' in geo_info:
                    print_row("Region", geo_info['region'])
                if 'country' in geo_info:
                    print_row("Country Code", geo_info['country'])
                if 'loc' in geo_info:
                    print_row("Coordinates", geo_info['loc'])
                if 'timezone' in geo_info:
                    print_row("Timezone", geo_info['timezone'])
            
            # BGP Information 
            bgp_info = result.get('bgp_info', {})
            prefixes = bgp_info.get('prefixes', [])
            
            if prefixes and isinstance(prefixes, list):
                for i, prefix in enumerate(prefixes[:2]):  # Limit to first 2 prefixes
                    if not isinstance(prefix, dict):
                        continue
                        
                    prefix_str = prefix.get('prefix', '')
                    name = prefix.get('name', '')
                    desc = prefix.get('description', '')
                    
                    value = prefix_str
                    if name:
                        value += f" ({name})"
                    if desc:
                        value += f" - {desc}"
                    
                    print_row(f"BGP Prefix {i+1}", value)
                    
                    rir = prefix.get('rir_allocation', {})
                    if isinstance(rir, dict):
                        rir_name = rir.get('rir_name', '')
                        date = rir.get('date_allocated', '')
                        if rir_name and date:
                            print_row("RIR Allocation", f"{rir_name} ({date})")
            
            # Close table
            print("+" + "-" * table_width + "+")
            
        except Exception as e:
            print(colored(f"Error displaying information: {str(e)}", "red"))
            print("+" + "-" * table_width + "+")  # Close the table
    
    def display_comparison_table(self):
        """Display a simple comparison table of all IPs"""
        if not self.results:
            return
        
        try:
            print(colored("\nIP Comparison Summary:", "cyan"))
            
            # Define columns and widths
            columns = [
                ("IP", 15), 
                ("ASN", 8), 
                ("Organization", 20), 
                ("Prefix", 18), 
                ("Country", 10), 
                ("City", 15), 
                ("Reverse DNS", 20)
            ]
            
            # Calculate total width
            total_width = sum(width for _, width in columns) + (len(columns) + 1)
            
            # Print header line
            print("+" + "-" * total_width + "+")
            
            # Print column headers
            header = "|"
            for name, width in columns:
                header += f" {name:{width}} |"
            print(header)
            
            # Print separator
            print("+" + "-" * total_width + "+")
            
            # Print each row
            for result in self.results:
                if 'error' in result:
                    row = f"| {result['ip']:{columns[0][1]}} "
                    row += f"| {'Error':{columns[1][1]}} "
                    
                    error_text = result['error']
                    if len(error_text) > columns[2][1]:
                        error_text = error_text[:columns[2][1]-3] + "..."
                    
                    row += f"| {error_text:{columns[2][1]}} "
                    row += f"| {'':{columns[3][1]}} "
                    row += f"| {'':{columns[4][1]}} "
                    row += f"| {'':{columns[5][1]}} "
                    row += f"| {'':{columns[6][1]}} |"
                    
                    print(row)
                else:
                    # Extract data with safe defaults
                    asn = str(result.get('asn', ''))
                    org = result.get('asn_description', '')
                    prefix = result.get('network', {}).get('cidr', '')
                    country = result.get('network', {}).get('country', '')
                    city = result.get('geo_info', {}).get('city', '')
                    rdns = result.get('reverse_dns', '')
                    
                    # Truncate if needed
                    if len(org) > columns[2][1]:
                        org = org[:columns[2][1]-3] + "..."
                    if len(city) > columns[5][1]:
                        city = city[:columns[5][1]-3] + "..."
                    if len(rdns) > columns[6][1]:
                        rdns = rdns[:columns[6][1]-3] + "..."
                    
                    # Build row
                    row = f"| {result['ip']:{columns[0][1]}} "
                    row += f"| {asn:{columns[1][1]}} "
                    row += f"| {org:{columns[2][1]}} "
                    row += f"| {prefix:{columns[3][1]}} "
                    row += f"| {country:{columns[4][1]}} "
                    row += f"| {city:{columns[5][1]}} "
                    row += f"| {rdns:{columns[6][1]}} |"
                    
                    print(row)
            
            # Print footer line
            print("+" + "-" * total_width + "+")
            
        except Exception as e:
            print(colored(f"Error displaying comparison table: {str(e)}", "red"))
    
    def save_results_to_file(self):
        """Save detailed results to a JSON file"""
        if not self.results:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ip_info_results_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            print(colored(f"\nDetailed results saved to {filename}", "green"))
        except Exception as e:
            print(colored(f"Error saving results: {str(e)}", "red"))
    
    def process_ips(self, ips):
        """Process multiple IPs with error handling"""
        print(colored("\nProcessing IP addresses...", "green"))
        
        # Remove duplicates but preserve order
        unique_ips = []
        for ip in ips:
            if ip not in unique_ips:
                unique_ips.append(ip)
        
        # Process each IP
        for ip in unique_ips:
            try:
                result = self.process_ip(ip)
                self.results.append(result)
                self.display_ip_info(result)
            except Exception as e:
                print(colored(f"Error processing {ip}: {str(e)}", "red"))
                self.results.append({
                    'ip': ip,
                    'error': f"Processing error: {str(e)}"
                })
        
        # Ask to save results
        try:
            save_choice = input(colored("\nSave detailed results to file? (y/n): ", "yellow"))
            if save_choice.lower() == 'y':
                self.save_results_to_file()
        except Exception as e:
            print(colored(f"Error with save prompt: {str(e)}", "red"))

def main():
    """Main function to run the IP info tool"""
    try:
        # Initialize the IP info tool
        ip_tool = IPInfoTool()
        
        # Collect IPs from user
        ips = []
        print(colored("Please paste your IPs (one per line) and press Ctrl+C when you're done:", "blue"))
        try:
            while True:
                ip = input().strip()
                if ip:  # Skip empty lines
                    ips.append(ip)
        except KeyboardInterrupt:
            print("")  # Add a newline after Ctrl+C
        
        # Process the IPs
        if ips:
            ip_tool.process_ips(ips)
        else:
            print(colored("No IP addresses provided.", "red"))
        
        # Exit prompt
        try:
            input(colored('\nPress ENTER to exit', 'blue'))
        except:
            pass
    except Exception as e:
        print(colored(f"\nUnexpected error: {str(e)}", "red"))
    finally:
        # Always return to the main menu
        try:
            os.system("python mainmenu.py")
        except:
            os.system("python3 mainmenu.py")  # Try alternative command if first fails

if __name__ == "__main__":
    main()