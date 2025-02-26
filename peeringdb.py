import requests
import os
import json
import time
from termcolor import colored
from datetime import datetime

# Cache for API responses to avoid duplicate requests
REQUEST_CACHE = {}
# Minimum delay between API requests (seconds)
API_RATE_LIMIT = 0.3

def print_section_header(title):
    """Print a formatted section header."""
    print("\n" + colored("=" * 60, 'blue'))
    print(colored(f" {title}", 'cyan', attrs=['bold']))
    print(colored("=" * 60, 'blue'))

def print_key_value(key, value, color='yellow'):
    """Print a key-value pair with consistent formatting."""
    print(f"{key.ljust(20)}: {colored(value, color)}")

def fetch_data(endpoint, params=None, retries=2):
    """Fetch data from PeeringDB API with caching, rate limiting and error handling."""
    base_url = 'https://peeringdb.com/api'
    url = f"{base_url}/{endpoint}"
    
    # Create a cache key based on the URL and parameters
    param_str = json.dumps(params, sort_keys=True) if params else ""
    cache_key = f"{url}_{param_str}"
    
    # Check if response is in cache
    if cache_key in REQUEST_CACHE:
        return REQUEST_CACHE[cache_key]
    
    # Rate limiting - ensure we don't make requests too quickly
    time.sleep(API_RATE_LIMIT)
    
    for attempt in range(retries + 1):
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 429:  # Too Many Requests
                if attempt < retries:
                    # Exponential backoff - wait longer with each retry
                    wait_time = (2 ** attempt) * 2  # 2, 4, 8 seconds...
                    print(colored(f"Rate limited by PeeringDB API. Waiting {wait_time} seconds before retry...", 'yellow'))
                    time.sleep(wait_time)
                    continue
                else:
                    print(colored(f"Rate limit exceeded for {url}", 'red'))
                    return None
            
            response.raise_for_status()  # Raise exception for other non-200 responses
            data = response.json()
            
            # Cache the successful response
            REQUEST_CACHE[cache_key] = data
            return data
            
        except requests.exceptions.RequestException as e:
            if attempt < retries:
                # Wait before retrying
                wait_time = (2 ** attempt) * 1
                print(colored(f"Error: {str(e)}. Retrying in {wait_time} seconds...", 'yellow'))
                time.sleep(wait_time)
            else:
                print(colored(f"Error fetching data from {url}: {str(e)}", 'red'))
                return None
    
    return None

def search_networks_by_name(name_fragment):
    """Search for networks by name fragment."""
    print(colored(f"Searching for networks with name containing '{name_fragment}'...", 'green'))
    
    # Use the search endpoint with the name parameter
    params = {"name__contains": name_fragment}
    data = fetch_data("net", params=params)
    
    if not data or not data.get('data'):
        return []
    
    return data['data']

def fetch_asn_details(asn):
    """Fetch basic details about an ASN from PeeringDB."""
    # Validate ASN input
    try:
        asn = int(asn.replace("AS", "").strip())
    except ValueError:
        print(colored(f"Invalid ASN format: {asn}. Please enter a valid ASN number.", 'red'))
        return None

    # Fetch network details
    print(colored("Fetching network information...", 'green'))
    data = fetch_data(f"net?asn={asn}")
    if not data or not data.get('data'):
        return None
    
    # Return the network information
    return data['data'][0]

def display_network_info(network):
    """Display basic network information."""
    print_section_header("NETWORK INFORMATION")
    
    # Status indicator
    status = "✅ ACTIVE" if network.get('status', 'ok') == 'ok' else "❌ INACTIVE"
    
    # Format created/updated dates
    created = datetime.fromisoformat(network.get('created', '').replace('Z', '+00:00')) if network.get('created') else None
    updated = datetime.fromisoformat(network.get('updated', '').replace('Z', '+00:00')) if network.get('updated') else None
    
    created_str = created.strftime("%Y-%m-%d") if created else "Unknown"
    updated_str = updated.strftime("%Y-%m-%d") if updated else "Unknown"
    
    print_key_value("AS Number", f"AS{network.get('asn', 'Unknown')}")
    print_key_value("Name", network.get('name', 'Unknown'))
    print_key_value("Status", status, 'green' if 'ACTIVE' in status else 'red')
    print_key_value("Website", network.get('website', 'Not provided'))
    print_key_value("Looking Glass", network.get('looking_glass', 'Not provided'))
    print_key_value("Route Server", network.get('route_server', 'Not provided'))
    print_key_value("IRR Records", network.get('irr_as_set', 'Not provided'))
    print_key_value("Type", network.get('info_type', 'Not specified'))
    print_key_value("Traffic", f"{network.get('info_traffic', 'Unknown')}")
    print_key_value("Scope", network.get('info_scope', 'Not specified'))
    print_key_value("Created", created_str)
    print_key_value("Last Updated", updated_str)
    
    # Print network notes if available
    if network.get('notes'):
        print("\n" + colored("Network Notes:", 'yellow'))
        print(network.get('notes'))
    
    # Print policy information
    print_section_header("PEERING POLICY")
    
    print_key_value("General Policy", network.get('policy_general', 'Not specified'))
    print_key_value("Location Requirement", "Yes" if network.get('policy_locations', False) else "No")
    print_key_value("Ratio Requirement", "Yes" if network.get('policy_ratio', False) else "No")
    print_key_value("Contracts Required", "Yes" if network.get('policy_contracts', False) else "No")
    print_key_value("Policy URL", network.get('policy_url', 'Not provided'))

def display_peeringdb_links(asn):
    """Display useful PeeringDB web links."""
    print_section_header("USEFUL LINKS")
    
    # Remove any AS prefix and ensure it's just the number
    asn_num = asn.replace("AS", "").strip()
    
    links = [
        ["PeeringDB Network Page", f"https://www.peeringdb.com/net/{asn_num}"],
        ["PeeringDB ASN Search", f"https://www.peeringdb.com/asn/{asn_num}"],
        ["BGP.tools", f"https://bgp.tools/as/{asn_num}"],
        ["Hurricane Electric BGP Toolkit", f"https://bgp.he.net/AS{asn_num}"]
    ]
    
    for link in links:
        print(f"{link[0].ljust(30)}: {colored(link[1], 'cyan')}")

def display_search_results(results):
    """Display search results in a numbered list."""
    print_section_header(f"SEARCH RESULTS ({len(results)} networks found)")
    
    for i, network in enumerate(results, 1):
        asn = network.get('asn', 'Unknown')
        name = network.get('name', 'Unknown')
        info_type = network.get('info_type', '')
        info_scope = network.get('info_scope', '')
        info_traffic = network.get('info_traffic', '')
        
        # Format the additional info
        additional_info = []
        if info_type:
            additional_info.append(info_type)
        if info_scope:
            additional_info.append(info_scope)
        if info_traffic:
            additional_info.append(info_traffic)
        
        additional_info_str = " | ".join(additional_info)
        if additional_info_str:
            additional_info_str = f" ({additional_info_str})"
        
        print(colored(f"{i}. ", 'cyan') + 
              colored(f"AS{asn}", 'yellow') + 
              f" - {name}" + 
              colored(additional_info_str, 'green'))

def main():
    try:
        print(colored("\n=== PeeringDB Information Tool ===", 'cyan', attrs=['bold']))
        print(colored("You can search by ASN or by company name", 'white'))
        
        # Get input
        search_input = input(colored("Enter ASN, company name, or name fragment: ", 'yellow'))
        
        if not search_input.strip():
            print(colored("No input provided. Exiting.", 'red'))
            return
        
        # Check if input is an ASN (starts with AS or is numeric)
        if search_input.upper().startswith('AS') or search_input.strip().isdigit():
            # Normalize input by removing 'AS' prefix if present
            asn = search_input.upper().replace("AS", "").strip()
            
            print(colored(f"\nFetching data for AS{asn}...", 'green'))
            network = fetch_asn_details(asn)
            
            if network:
                # Display network information
                display_network_info(network)
                display_peeringdb_links(asn)
            else:
                print(colored(f"No data found for AS{asn} in PeeringDB.", 'red'))
                print(colored("This AS may not be registered in PeeringDB or might not exist.", 'yellow'))
        else:
            # Search by name
            networks = search_networks_by_name(search_input)
            
            if not networks:
                print(colored(f"No networks found matching '{search_input}'.", 'red'))
                return
            
            # Display search results
            display_search_results(networks)
            
            # Prompt user to select a network
            while True:
                try:
                    selection = input(colored("\nSelect a network by number (or 'q' to quit): ", 'yellow'))
                    
                    if selection.lower() == 'q':
                        print(colored("Exiting search.", 'yellow'))
                        return
                    
                    idx = int(selection) - 1
                    if 0 <= idx < len(networks):
                        selected_network = networks[idx]
                        # Display detailed information for the selected network
                        display_network_info(selected_network)
                        display_peeringdb_links(str(selected_network.get('asn', '')))
                        break
                    else:
                        print(colored("Invalid selection. Please try again.", 'red'))
                except ValueError:
                    print(colored("Please enter a valid number or 'q' to quit.", 'red'))
    
    except KeyboardInterrupt:
        print(colored("\nOperation cancelled by user.", 'yellow'))
    except Exception as e:
        print(colored(f"\nAn error occurred: {str(e)}", 'red'))
    finally:
        # Exit prompt
        input(colored('\nPress ENTER to exit', 'blue'))
        
        # Return to the main menu
        os.system("python mainmenu.py")

if __name__ == "__main__":
    main()