import os
from termcolor import colored
from datetime import datetime
import time
import sys

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    banner = colored("""                                 _          _                 _      
       /\                       (_)        | |               | |     
      /  \    _ __    ___ __  __ _   __ _  | |_  ___    ___  | | ___ 
     / /\ \  | '_ \  / _ \\\\ \/ /| | / _` | | __|/ _ \  / _ \ | |/ __|
    / ____ \ | | | ||  __/ >  < | || (_| | | |_| (_) || (_) || |\__ \\
   /_/    \_\|_| |_| \___|/_/\_\|_| \__,_|  \__|\___/  \___/ |_||___/""", 'yellow')
    print(banner)

def list_tools(tools):
    print(colored("\nWhich tool do you need?\n", 'yellow'))
    for index, tool in enumerate(tools, start=1):
        print(colored(f"{index}. ", 'cyan') + tool)

def get_tool_choice(tools_list_length):
    try:
        index = input(colored('\nOption: ', 'yellow'))
        int_index = int(index) - 1
        if int_index >= 0 and int_index < tools_list_length:
            return int_index
        else:
            print(colored("Invalid input, please enter a valid number.", 'red'))
            time.sleep(1)
            os.system("python3 mainmenu.py")
    except KeyboardInterrupt:
        sys.exit()
    except ValueError:
        print(colored("Invalid input, please enter a number.", 'red'))
        time.sleep(1)
        os.system("python3 mainmenu.py")

def main():
    clear_screen()
    print("\n")
    print_banner()

    now = datetime.now()
    current_day = now.strftime("%d.%m.%Y, %A, Week: %U, %I:%M %p")
    print(colored(f"\nToday is {current_day}", 'green'))

    tools = {
        'Interface description generator': 'ifdescgenerator.py',
        'BGPq3 prefix counter': 'bgpq3.py',
        'Blueprint Upgrade shipping list generator': 'itemgenerator.py',
		'Incident generator' : 'incident.py',
        'IP Calculator': 'netmaskcalc.py',
        'MAC Lookup' : 'maclookup.py',
        'IP visualisation (NO VPN)' : 'ipinfo.py',
        'IP info (RIPE, etc.)' : 'ip_ripe.py',
        'Config generator ipv6 xaas' : 'conf_gen.py',
        'AS PeeringDB datas' : 'peeringdb.py'
    }

    tools_list = list(tools.keys())
    list_tools(tools_list)

    index = get_tool_choice(len(tools_list))
    if index is not None:
        script = tools_list[index]
        os.system(f"python3 {tools[script]}")
    else:
        print(colored("Exiting program...", 'yellow'))
    script = tools_list[index]

    os.system(f"python3 {tools[script]}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit()
