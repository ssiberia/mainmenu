import requests
from termcolor import colored
from terminaltables import SingleTable
import os
import sys

API_BASE_URL = "https://irrexplorer.nlnog.net/api/v1"

def query_irr(prefix):
    try:
        response = requests.get(f"{API_BASE_URL}/prefix/{prefix}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(colored(f"Error querying API for {prefix}: {str(e)}", 'red'))
        return None

def process_prefix(prefix):
    data = query_irr(prefix)
    if not data:
        return

    table_data = [
        [colored("Prefix", attrs=['bold']), colored(prefix, 'yellow')]
    ]

    if 'error' in data:
        table_data.append([colored("Error", attrs=['bold']), colored(data['error'], 'red')])
    else:
        if data.get('asn'):
            table_data.append([colored("ASN", attrs=['bold']), colored(data['asn'], 'yellow')])
        
        if data.get('irr_records'):
            irr_count = len(data['irr_records'])
            table_data.append([colored("IRR Records", attrs=['bold']), 
                             colored(str(irr_count), 'yellow' if irr_count > 0 else 'red')])
        
        if data.get('route'):
            table_data.append([colored("Route Object", attrs=['bold']), 
                             colored(data['route'], 'yellow')])
        
        if data.get('rpki'):
            rpki_status = "Valid" if data['rpki']['valid'] else "Invalid"
            table_data.append([colored("RPKI Status", attrs=['bold']), 
                             colored(rpki_status, 'green' if data['rpki']['valid'] else 'red')])

    table = SingleTable(table_data)
    table.inner_row_border = True
    print(table.table)

    if data.get('irr_records'):
        print(colored("\nShow detailed IRR records? (y/n)", 'blue'))
        if input().lower() == 'y':
            detailed_table = [
                [colored("ASN", 'cyan'), colored("Source", 'cyan'), 
                 colored("Policy", 'cyan'), colored("Maintainer", 'cyan')]
            ]
            for record in data['irr_records']:
                detailed_table.append([
                    colored(record.get('asn', 'N/A'), 'yellow'),
                    colored(record.get('source', 'N/A'), 'yellow'),
                    colored(record.get('policy', 'N/A'), 'yellow'),
                    colored(record.get('maintainer', 'N/A'), 'yellow')
                ])
            dt = SingleTable(detailed_table)
            print(dt.table)

def main():
    while True:
        print(colored("\nEnter multiple prefixes (one per line). Press 'q' and ENTER or send EOF (Ctrl+D) to finish.", 'blue'))
        
        prefixes = []
        while True:
            try:
                line = input().strip()
                if line.lower() == 'q':
                    break
                if line:
                    prefixes.append(line)
            except EOFError:
                break
            except KeyboardInterrupt:
                sys.exit(0)

        for prefix in prefixes:
            process_prefix(prefix)

        print(colored("\nQuery more prefixes? (y/n)", 'green'))
        choice = input().strip().lower()
        if choice != 'y':
            os.system("python3 mainmenu.py")
            break

if __name__ == "__main__":
    main()