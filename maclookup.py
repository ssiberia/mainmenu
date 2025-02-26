import os
import re
import sys
from termcolor import colored
from manuf import manuf

# Simple cache for vendor lookups
vendor_cache = {}

def validate_mac(mac):
    """
    Validate if the input is a proper MAC address.
    Returns cleaned input if valid, None otherwise.
    """
    if not mac:
        return None
        
    # Remove all non-hexadecimal characters except common separators
    cleaned = re.sub(r'[^0-9a-fA-F\-\.:]', '', mac)
    
    # Check if we have enough hex digits (12 hex digits = 6 bytes)
    hex_only = re.sub(r'[\-\.:]', '', cleaned)
    if len(hex_only) != 12:
        return None
        
    return cleaned

def normalize_mac(mac):
    """
    Normalize MAC address to standard format (xx:xx:xx:xx:xx:xx).
    Handles various input formats like xx-xx-xx-xx-xx-xx or xxxx.xxxx.xxxx.
    """
    if not mac:
        return None
        
    # Convert to lowercase and remove any non-hex characters except separators
    mac = re.sub(r'[^0-9a-fA-F\-\.:]', '', mac.lower())
    
    # Extract all hex digits
    hex_digits = re.sub(r'[\-\.:]', '', mac)
    
    # Check if we have enough digits
    if len(hex_digits) != 12:
        return None
    
    # Group into bytes
    mac_bytes = [hex_digits[i:i+2] for i in range(0, 12, 2)]
    
    # Return standard format
    return ':'.join(mac_bytes)

def format_mac(mac, vendor_format):
    """
    Format MAC address according to vendor requirements.
    
    Parameters:
    mac (str): Normalized MAC address (xx:xx:xx:xx:xx:xx)
    vendor_format (str): Format type ('cisco', 'juniper', or any other for standard)
    
    Returns:
    str: Formatted MAC address
    """
    if not mac:
        return "Invalid MAC"
        
    mac_bytes = mac.split(':')
    
    if vendor_format.lower() == "cisco":
        return '.'.join([''.join(mac_bytes[i:i+2]) for i in range(0, len(mac_bytes), 2)])
    elif vendor_format.lower() == "juniper":
        return '-'.join(mac_bytes)
    else:  # Standard format
        return ':'.join(mac_bytes)

def get_vendor(mac):
    """
    Get vendor information for a MAC address with caching.
    
    Parameters:
    mac (str): Normalized MAC address
    
    Returns:
    str: Vendor name or None if not found
    """
    if not mac:
        return None
        
    # Check cache first
    if mac in vendor_cache:
        return vendor_cache[mac]
    
    try:
        p = manuf.MacParser()
        vendor = p.get_manuf(mac)
        
        # Cache the result
        vendor_cache[mac] = vendor
        return vendor
    except Exception as e:
        print(colored(f"Error looking up vendor: {str(e)}", 'red'))
        return None

def display_results(mac, vendor, formats):
    """
    Display the results in a formatted way.
    
    Parameters:
    mac (str): The normalized MAC address
    vendor (str): Vendor information
    formats (dict): Dictionary of different format outputs
    """
    # Print vendor information
    if vendor:
        print(colored("\nVendor: " + vendor, 'yellow'))
    else:
        print(colored("\nVendor not found for this MAC address", 'red'))
    
    # Print the MAC address in different formats
    print(colored("\nMAC address in different formats:", 'blue'))
    for format_name, formatted_mac in formats.items():
        print(colored(f"{format_name.ljust(10)}", 'yellow'), end="")
        print(f"{formatted_mac}")

def main():
    try:
        # Prompt for MAC address
        print(colored("\nPlease give me the MAC address in any format: ", 'blue'), end='')
        mac_address = input().strip()
        
        # Validate input
        valid_mac = validate_mac(mac_address)
        if not valid_mac:
            print(colored(f"Invalid MAC address format: {mac_address}", 'red'))
            print(colored("MAC should contain 12 hexadecimal digits (6 bytes)", 'yellow'))
            input(colored('\nPress ENTER to exit', attrs=['dark']))
            os.system("python3 mainmenu.py")
            return
        
        # Normalize the MAC address
        normalized_mac = normalize_mac(valid_mac)
        if not normalized_mac:
            print(colored(f"Could not normalize MAC address: {mac_address}", 'red'))
            input(colored('\nPress ENTER to exit', attrs=['dark']))
            os.system("python3 mainmenu.py")
            return
        
        # Get vendor information
        vendor = get_vendor(normalized_mac)
        
        # Format the MAC address in different formats
        formats = {
            "Cisco": format_mac(normalized_mac, 'cisco'),
            "Juniper": format_mac(normalized_mac, 'juniper'),
            "Standard": format_mac(normalized_mac, 'standard'),
        }
        
        # Display results
        display_results(normalized_mac, vendor, formats)
        
        # Exit prompt
        input(colored('\nPress ENTER to exit', attrs=['dark']))
        
        # Return to the main menu
        os.system("python3 mainmenu.py")
        
    except KeyboardInterrupt:
        print(colored("\nOperation cancelled by user.", 'yellow'))
        os.system("python3 mainmenu.py")
    except Exception as e:
        print(colored(f"\nAn error occurred: {str(e)}", 'red'))
        input(colored('\nPress ENTER to exit', attrs=['dark']))
        os.system("python3 mainmenu.py")

if __name__ == "__main__":
    main()