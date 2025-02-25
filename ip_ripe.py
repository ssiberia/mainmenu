import requests
from ipwhois import IPWhois
import os
from termcolor import colored
from hyperlink import URL

def get_ip_info(ip):
    try:
        ipwhois = IPWhois(ip)
        result = ipwhois.lookup_rdap()
        
        asn = result['asn']
        as_name = result['asn_description']
        prefix = result['network']['cidr']
        country = result['asn_country_code']

        print(colored(f"\n\nIP: {ip}", "cyan"))
        if asn and as_name:
            peeringdb_url = URL.from_text(f"https://www.peeringdb.com/asn/{asn}")
            print(colored(f"ASN: ", "yellow") + colored(f"{asn}", "white") + colored(f" - {as_name} ", "yellow") + colored(f"{peeringdb_url.to_uri()}", "dark_grey"))
        if prefix:
            bgp_tools_url = URL.from_text(f"https://bgp.tools/prefix/{prefix}")
            print(colored(f"Prefix: {prefix} ", "yellow") + colored(f"{bgp_tools_url.to_uri()}", "dark_grey"))
        if country:
            print(colored(f"Country: {country}", "yellow"))
        print()
    except Exception as e:
        print(colored(f"IP: {ip}\nError retrieving information: {e}\n", "red"))

ips = []
print(colored("Please paste your IPs and press Ctrl+C when you're done:", "blue"))
while True:
    try:
        ip = input()
        ips.append(ip)
    except KeyboardInterrupt:
        break

for ip in ips:
    get_ip_info(ip)

# Exit prompt
input(colored('\nPress ENTER to exit', 'blue'))

# Return to the main menu
os.system("python mainmenu.py")
