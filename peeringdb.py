import requests
import os
import json
from termcolor import colored


def fetch_asn_details(asn):
    response = requests.get(f'https://peeringdb.com/api/net?asn={asn}')
    data = response.json()
    if data['data']:
        return data['data'][0]
    else:
        return None

asn = input("Enter the ASN: ")
details = fetch_asn_details(asn)

if details:
    print(json.dumps(details, indent=4))
else:
    print(f"No data found for ASN {asn}")


# Exit prompt
input(colored('\nPress ENTER to exit', 'blue'))

# Return to the main menu
os.system("python mainmenu.py")
