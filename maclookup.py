import os
import re
from termcolor import colored
from manuf import manuf

def normalize_mac(mac):
    mac = mac.lower()
    if '-' in mac:
        mac_bytes = mac.split('-')
    elif '.' in mac:
        mac_bytes = re.findall('..', mac.replace('.', ''))
    else:
        mac_bytes = mac.split(':')

    return ':'.join(mac_bytes)

def format_mac(mac, vendor):
    mac_bytes = mac.split(':')
    if vendor == "cisco":
        return '.'.join([''.join(mac_bytes[i:i + 2]) for i in range(0, len(mac_bytes), 2)])
    elif vendor == "juniper":
        return '-'.join(mac_bytes)
    else:  # Standard format
        return ':'.join(mac_bytes)

# Prompt the user for the MAC address (not case sensitive)
print(colored("\nPlease give me the MAC address in any format: ", 'blue'), end='')
mac_address = input()
normalized_mac = normalize_mac(mac_address)
p = manuf.MacParser()
vendor = p.get_manuf(normalized_mac)

if vendor:
    print(colored("Vendor: " + vendor, 'yellow'))
else:
    print(f"Vendor not found for MAC address {mac_address}")

# Print the MAC address in different formats
print(colored("\nMAC address in different formats:", 'blue'))
print(colored("Cisco:    ", 'yellow'), end="")
print(f"{format_mac(normalized_mac, 'cisco')}")
print(colored("Juniper:  ", 'yellow'), end="")
print(f"{format_mac(normalized_mac, 'juniper')}")
print(colored("Standard: ", 'yellow'), end="")
print(f"{format_mac(normalized_mac, 'standard')}")

# Exit prompt
input(colored('\nPress ENTER to exit', attrs=['dark']))

# Return to the main menu
os.system("python3 mainmenu.py")
