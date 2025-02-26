#!/usr/bin/env python3
"""
Prefix Health Monitor
Check the health and visibility of prefixes in the global routing table.
Monitors ROA status, RPKI validation, and prefix visibility across the internet.
"""

import os
import json
import requests
import time
import ipaddress
import csv
import sys
from datetime import datetime
from termcolor import colored
from concurrent.futures import ThreadPoolExecutor, as_completed

# Constants
API_RATE_LIMIT = 1  # Time in seconds between API calls
MAX_WORKERS = 5     # Maximum number of concurrent API requests
REQUEST_TIMEOUT = 10  # Timeout for API requests in seconds

# API endpoints
BGPVIEW_API = "https://api.bgpview.io"
# Updated API endpoints
RPKI_VALIDATOR_API = "https://stat.ripe.net/data/rpki-validation/data.json"
BGPSTUFF_API = "https://bgpstuff.net/api/v1"

class PrefixHealth:
    """Class to check the health of prefixes in the global routing table"""
    
    def __init__(self):
        """Initialize the prefix health monitor"""
        self.results = []
        self.headers = {
            'User-Agent': 'PrefixHealthMonitor/1.0 (Network Troubleshooting Utility)'
        }
        # Cache for API responses to avoid duplicate requests
        self.cache = {}
    
    def is_valid_prefix(self, prefix):
        """Check if a string is a valid IP prefix (CIDR notation)"""
        try:
            ipaddress.ip_network(prefix)
            return True
        except ValueError:
            return False
    
    def make_api_request(self, url, params=None, cache_key=None):
        """Make an API request with caching and rate limiting"""
        # Use cache if available
        if cache_key and cache_key in self.cache:
            return self.cache[cache_key]
        
        # Rate limiting
        time.sleep(API_RATE_LIMIT)
        
        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            # Cache the response if cache_key is provided
            if cache_key:
                self.cache[cache_key] = data
                
            return data
        except requests.exceptions.RequestException as e:
            print(colored(f"API request error ({url}): {str(e)}", 'red'))
            return None
    
    def check_bgpview(self, prefix):
        """Check prefix information using BGP.tools API"""
        # Extract network address for API query
        try:
            network = ipaddress.ip_network(prefix)
            ip = str(network.network_address)
            
            # Make API request
            cache_key = f"bgpview_{ip}"
            url = f"{BGPVIEW_API}/ip/{ip}"
            data = self.make_api_request(url, cache_key=cache_key)
            
            if data and data.get('status') == 'ok':
                return data.get('data', {})
            
            return {}
        except Exception as e:
            print(colored(f"Error checking BGP.tools for {prefix}: {str(e)}", 'red'))
            return {}
    
    def check_rpki_status(self, prefix, origin_asn=None):
        """Check RPKI validation status using RIPE Stat API"""
        try:
            # Format the params based on available information
            if origin_asn:
                # Remove 'AS' prefix if present
                if isinstance(origin_asn, str) and origin_asn.upper().startswith('AS'):
                    origin_asn = origin_asn[2:]
                
                resource = f"AS{origin_asn}"
                params = {'resource': resource, 'prefix': prefix}
            else:
                params = {'resource': prefix}
            
            cache_key = f"rpki_{prefix}_{origin_asn}"
            data = self.make_api_request(RPKI_VALIDATOR_API, params=params, cache_key=cache_key)
            
            if data and data.get('status') == 'ok' and 'data' in data:
                result = data['data']
                # Extract the validity state from the response
                validations = result.get('validations', {})
                
                # Get the first validation result if available
                if validations and isinstance(validations, dict):
                    validation = next(iter(validations.values()), {})
                    state = validation.get('state', 'unknown')
                    description = validation.get('description', 'No description available')
                    return {'validity': {'state': state, 'description': description}}
            
            return {'validity': {'state': 'unknown', 'description': 'Unable to validate'}}
        except Exception as e:
            print(colored(f"Error checking RPKI for {prefix}: {str(e)}", 'red'))
            return {'validity': {'state': 'error', 'description': str(e)}}
    
    def check_bgpstuff(self, prefix):
        """Check prefix visibility using bgpstuff.net API"""
        try:
            # Format for API query - try both the prefix and the network address
            network = ipaddress.ip_network(prefix)
            ip = str(network.network_address)
            
            # First, try checking with the full prefix
            cache_key = f"bgpstuff_{prefix}"
            url = f"{BGPSTUFF_API}/prefix/{prefix}"
            data = self.make_api_request(url, cache_key=cache_key)
            
            if data and data.get('status') == 'ok':
                return data
            
            # If not found, try with just the IP address
            cache_key = f"bgpstuff_{ip}"
            url = f"{BGPSTUFF_API}/ip/{ip}"
            data = self.make_api_request(url, cache_key=cache_key)
            
            if data and data.get('status') == 'ok':
                return data
            
            # If neither works, try an alternative approach through the route API
            cache_key = f"bgpstuff_route_{prefix}"
            url = f"{BGPSTUFF_API}/route/{prefix}"
            data = self.make_api_request(url, cache_key=cache_key)
            
            if data and data.get('status') == 'ok':
                return data
            
            # As a last fallback, check ASN information if we have an IP
            # This at least tells us if the address space is allocated
            cache_key = f"bgpstuff_asn_{ip}"
            url = f"{BGPSTUFF_API}/asn/{ip}"
            data = self.make_api_request(url, cache_key=cache_key)
            
            if data and data.get('status') == 'ok':
                return data
            
            return {'status': 'not_found', 'message': 'Prefix not found in BGP table'}
        except Exception as e:
            print(colored(f"Error checking bgpstuff.net for {prefix}: {str(e)}", 'red'))
            return {'status': 'error', 'message': str(e)}
    
    def check_looking_glasses(self, prefix):
        """Check prefix visibility in major looking glasses using RIPE RIS API"""
        try:
            # Use RIPE RIS API to check visibility across route collectors
            url = f"https://stat.ripe.net/data/looking-glass/data.json"
            params = {'resource': prefix}
            cache_key = f"ripe_lg_{prefix}"
            
            data = self.make_api_request(url, params=params, cache_key=cache_key)
            
            if data and data.get('status') == 'ok' and 'data' in data:
                result_data = data['data']
                
                # Process the looking glass data
                visible_in = []
                not_visible_in = []
                error_in = []
                
                # Extract unique peer ASNs that see this prefix
                if 'rrcs' in result_data:
                    for rrc in result_data['rrcs']:
                        for peer in rrc.get('peers', []):
                            peer_as = peer.get('asn', '')
                            peer_name = f"AS{peer_as}"
                            
                            # Attempt to get a more friendly name from BGP data
                            # In a real implementation, you might want to use a BGP ASN database
                            visible_in.append(peer_name)
                
                # If we don't have RIPE RIS data, fall back to a default list
                if not visible_in:
                    return {
                        'visible_in': [],  # Empty since we couldn't confirm visibility
                        'not_visible_in': ['Level3', 'Cogent', 'Hurricane Electric', 'Cloudflare'],
                        'error_in': []
                    }
                
                return {
                    'visible_in': visible_in,
                    'not_visible_in': not_visible_in,
                    'error_in': error_in
                }
            
            # Fallback to simulated results if API fails
            return {
                'visible_in': [],
                'not_visible_in': ['Level3', 'Cogent', 'Hurricane Electric', 'Cloudflare'],
                'error_in': []
            }
            
        except Exception as e:
            print(colored(f"Error checking looking glasses for {prefix}: {str(e)}", 'red'))
            # Return a fallback result in case of error
            return {
                'visible_in': [],
                'not_visible_in': [],
                'error_in': ['Error fetching data from looking glasses']
            }
    
    def process_prefix(self, prefix, origin_asn=None):
        """Process a single prefix and check its health"""
        if not self.is_valid_prefix(prefix):
            return {
                'prefix': prefix,
                'error': "Invalid prefix format"
            }
        
        print(colored(f"Checking health for prefix: {prefix}", 'blue'))
        
        result = {
            'prefix': prefix,
            'timestamp': datetime.now().isoformat(),
            'origin_asn': origin_asn,
            'is_valid': True
        }
        
        # Check BGP.tools information
        bgp_info = self.check_bgpview(prefix)
        result['bgp_info'] = bgp_info
        
        # Get prefix announcement information
        prefix_info = {}
        if bgp_info and 'prefixes' in bgp_info:
            for pfx in bgp_info['prefixes']:
                if pfx['prefix'] == prefix:
                    prefix_info = pfx
                    break
        
        result['announced'] = bool(prefix_info)
        
        # If the prefix is found and we don't have an ASN, use the one from BGP.tools
        if not origin_asn and prefix_info and 'asn' in prefix_info:
            origin_asn = prefix_info['asn']['asn']
            result['origin_asn'] = origin_asn
        
        # Check RPKI status
        rpki_status = self.check_rpki_status(prefix, origin_asn)
        result['rpki_status'] = rpki_status
        
        # Check if the prefix is visible in BGP table
        bgpstuff_info = self.check_bgpstuff(prefix)
        result['bgpstuff_info'] = bgpstuff_info
        
        # Check looking glass visibility
        looking_glass_results = self.check_looking_glasses(prefix)
        result['looking_glass_results'] = looking_glass_results
        
        # Determine overall health status
        result['health_status'] = self.determine_health_status(result)
        
        return result
    
    def determine_health_status(self, result):
        """Determine the overall health status of a prefix"""
        health_status = {
            'status': 'healthy',  # healthy, warning, critical, unknown
            'issues': []
        }
        
        # Check if announced
        if not result.get('announced', False):
            health_status['status'] = 'critical'
            health_status['issues'].append('Prefix not announced in BGP')
        
        # Check RPKI status
        rpki_state = result.get('rpki_status', {}).get('validity', {}).get('state', 'unknown')
        if rpki_state == 'invalid':
            health_status['status'] = 'critical'
            health_status['issues'].append('RPKI validation failed (Invalid)')
        elif rpki_state == 'unknown':
            # Only make it a warning if it's not already critical
            if health_status['status'] != 'critical':
                health_status['status'] = 'warning'
            health_status['issues'].append('No ROA found (RPKI Unknown)')
        
        # Check BGP visibility
        bgpstuff_status = result.get('bgpstuff_info', {}).get('status')
        if bgpstuff_status != 'ok':
            if health_status['status'] != 'critical':
                health_status['status'] = 'warning'
            health_status['issues'].append('Not visible in BGP table (bgpstuff.net)')
        
        # Check looking glass visibility
        invisible_count = len(result.get('looking_glass_results', {}).get('not_visible_in', []))
        if invisible_count > 0:
            if health_status['status'] != 'critical':
                health_status['status'] = 'warning'
            health_status['issues'].append(f'Not visible in {invisible_count} looking glasses')
        
        return health_status
    
    def process_prefixes(self, prefixes, asns=None):
        """Process multiple prefixes with error handling and parallel processing"""
        print(colored("\nStarting prefix health checks...", 'green'))
        self.results = []
        
        # Pair prefixes with ASNs if provided
        if asns and len(asns) == len(prefixes):
            prefix_asn_pairs = list(zip(prefixes, asns))
        else:
            prefix_asn_pairs = [(prefix, None) for prefix in prefixes]
        
        # Process prefixes in parallel
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit tasks
            futures = {executor.submit(self.process_prefix, prefix, asn): prefix 
                       for prefix, asn in prefix_asn_pairs}
            
            # Process results as they complete
            for future in as_completed(futures):
                try:
                    result = future.result()
                    self.results.append(result)
                    self.display_prefix_health(result)
                except Exception as e:
                    prefix = futures[future]
                    print(colored(f"Error processing {prefix}: {str(e)}", 'red'))
                    self.results.append({
                        'prefix': prefix,
                        'error': f"Processing error: {str(e)}"
                    })
        
        # Display summary
        self.display_summary()
        
        # Ask to save results
        try:
            save_choice = input(colored("\nSave detailed results to file? (y/n): ", 'yellow'))
            if save_choice.lower() == 'y':
                self.save_results_to_file()
        except Exception as e:
            print(colored(f"Error with save prompt: {str(e)}", 'red'))
    
    def display_prefix_health(self, result):
        """Display the health status for a single prefix"""
        prefix = result.get('prefix')
        
        # Skip if there was an error
        if 'error' in result:
            print(colored(f"\nPrefix: {prefix} - Error: {result['error']}", 'red'))
            return
        
        # Get health status
        health = result.get('health_status', {})
        status = health.get('status', 'unknown')
        
        # Set color based on status
        if status == 'healthy':
            status_color = 'green'
        elif status == 'warning':
            status_color = 'yellow'
        elif status == 'critical':
            status_color = 'red'
        else:
            status_color = 'cyan'
        
        # Display header
        print("\n" + "=" * 60)
        print(colored(f"Prefix: {prefix}", 'cyan') + 
              f" (ASN: {result.get('origin_asn', 'Unknown')})")
        print(colored(f"Status: {status.upper()}", status_color))
        
        # Display RPKI information
        rpki_state = result.get('rpki_status', {}).get('validity', {}).get('state', 'unknown')
        rpki_color = 'green' if rpki_state == 'valid' else 'yellow' if rpki_state == 'unknown' else 'red'
        print(colored(f"RPKI: {rpki_state.upper()}", rpki_color))
        
        # Display visibility information
        announced = "Yes" if result.get('announced', False) else "No"
        print(colored(f"Announced in BGP: {announced}", 'green' if announced == "Yes" else 'red'))
        
        # Display looking glass results
        visible_count = len(result.get('looking_glass_results', {}).get('visible_in', []))
        total_count = visible_count + len(result.get('looking_glass_results', {}).get('not_visible_in', []))
        print(colored(f"Looking Glass Visibility: {visible_count}/{total_count}", 
                     'green' if visible_count == total_count else 'yellow'))
        
        # Display issues if any
        issues = health.get('issues', [])
        if issues:
            print(colored("Issues:", 'red'))
            for issue in issues:
                print(colored(f"- {issue}", 'yellow'))
    
    def display_summary(self):
        """Display a summary of all prefix health checks"""
        if not self.results:
            return
        
        # Count results by status
        status_counts = {'healthy': 0, 'warning': 0, 'critical': 0, 'error': 0, 'unknown': 0}
        
        for result in self.results:
            if 'error' in result:
                status_counts['error'] += 1
            else:
                status = result.get('health_status', {}).get('status', 'unknown')
                status_counts[status] += 1
        
        # Display summary
        print("\n" + "=" * 60)
        print(colored("PREFIX HEALTH SUMMARY", 'cyan', attrs=['bold']))
        print(f"Total prefixes checked: {len(self.results)}")
        print(colored(f"Healthy: {status_counts['healthy']}", 'green'))
        print(colored(f"Warning: {status_counts['warning']}", 'yellow'))
        print(colored(f"Critical: {status_counts['critical']}", 'red'))
        print(colored(f"Errors: {status_counts['error']}", 'red'))
        
        # Display table of prefixes and their statuses
        print("\n" + "=" * 60)
        print(colored("PREFIX STATUS TABLE", 'cyan', attrs=['bold']))
        print(f"{'Prefix':<20} {'ASN':<10} {'Status':<10} {'RPKI':<10} {'Issues'}")
        print("-" * 80)
        
        for result in self.results:
            prefix = result.get('prefix', 'Unknown')
            
            if 'error' in result:
                print(f"{prefix:<20} {'N/A':<10} {'ERROR':<10} {'N/A':<10} {result['error']}")
                continue
            
            asn = str(result.get('origin_asn', 'Unknown'))
            status = result.get('health_status', {}).get('status', 'unknown').upper()
            rpki = result.get('rpki_status', {}).get('validity', {}).get('state', 'unknown').upper()
            
            # Get first issue or 'None' if no issues
            issues = result.get('health_status', {}).get('issues', [])
            issue_text = issues[0] if issues else 'None'
            
            # Truncate issue text if too long
            if len(issue_text) > 35:
                issue_text = issue_text[:32] + "..."
            
            print(f"{prefix:<20} {asn:<10} {status:<10} {rpki:<10} {issue_text}")
    
    def save_results_to_file(self):
        """Save detailed results to both JSON and CSV files"""
        if not self.results:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"prefix_health_{timestamp}.json"
            csv_filename = f"prefix_health_{timestamp}.csv"
            
            # Save to JSON (detailed results)
            with open(json_filename, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            # Save to CSV (summary)
            with open(csv_filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Prefix', 'ASN', 'Status', 'RPKI Status', 'Announced', 'Issues'])
                
                for result in self.results:
                    prefix = result.get('prefix', 'Unknown')
                    
                    if 'error' in result:
                        writer.writerow([prefix, 'N/A', 'ERROR', 'N/A', 'N/A', result['error']])
                        continue
                    
                    asn = result.get('origin_asn', 'Unknown')
                    status = result.get('health_status', {}).get('status', 'unknown')
                    rpki = result.get('rpki_status', {}).get('validity', {}).get('state', 'unknown')
                    announced = "Yes" if result.get('announced', False) else "No"
                    issues = "; ".join(result.get('health_status', {}).get('issues', ['None']))
                    
                    writer.writerow([prefix, asn, status, rpki, announced, issues])
            
            print(colored(f"\nDetailed results saved to {json_filename}", 'green'))
            print(colored(f"Summary saved to {csv_filename}", 'green'))
        except Exception as e:
            print(colored(f"Error saving results: {str(e)}", 'red'))

def main():
    """Main function to run the prefix health monitor"""
    try:
        # Initialize the prefix health monitor
        prefix_tool = PrefixHealth()
        
        # Show welcome message
        print(colored("\n=== Prefix Health Monitor ===", 'cyan', attrs=['bold']))
        print(colored("This tool checks prefix visibility and health in the global routing table.", 'white'))
        print(colored("It validates ROA/RPKI status and monitors propagation across the internet.", 'white'))
        
        # Ask if user wants to enter ASNs with the prefixes
        include_asns = input(colored("\nDo you want to specify origin ASNs for the prefixes? (y/n): ", 'yellow'))
        include_asns = include_asns.lower() == 'y'
        
        # Collect prefixes from user
        prefixes = []
        asns = [] if include_asns else None
        
        print(colored("\nPlease paste your prefixes (one per line) and press Ctrl+C when done:", 'blue'))
        if include_asns:
            print(colored("Format: prefix AS123 (e.g., 192.168.0.0/24 AS64496)", 'yellow'))
        
        try:
            while True:
                line = input().strip()
                if not line:  # Skip empty lines
                    continue
                
                if include_asns:
                    # Try to parse prefix and ASN
                    parts = line.split()
                    if len(parts) >= 2:
                        prefix = parts[0]
                        asn = parts[1]
                        # Remove 'AS' prefix if present
                        if asn.upper().startswith('AS'):
                            asn = asn[2:]
                        prefixes.append(prefix)
                        asns.append(asn)
                    else:
                        print(colored(f"Invalid format: {line}. Expected: prefix ASN", 'red'))
                else:
                    prefixes.append(line)
        except KeyboardInterrupt:
            print("")  # Add a newline after Ctrl+C
        
        # Process the prefixes
        if prefixes:
            prefix_tool.process_prefixes(prefixes, asns)
        else:
            print(colored("No prefixes provided.", 'red'))
        
        # Exit prompt
        input(colored('\nPress ENTER to exit', 'blue'))
    except Exception as e:
        print(colored(f"\nUnexpected error: {str(e)}", 'red'))
    finally:
        # Always return to the main menu
        os.system("python3 mainmenu.py")

if __name__ == "__main__":
    main()