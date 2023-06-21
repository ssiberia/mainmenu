import os
from termcolor import colored

def generate_config(prefix):
    prefix_no_slash = prefix.split("/")[0]
    base_config = f"""### xaas prefixes
set routing-options rib inet6.0 static route {prefix_no_slash}:3::100:0/112 next-hop {prefix_no_slash}:3::4
set routing-options rib inet6.0 static route {prefix_no_slash}:3::100:0/112 community 47147:100
set routing-options rib inet6.0 static route {prefix_no_slash}:3::101:0/112 next-hop {prefix_no_slash}:3::4
set routing-options rib inet6.0 static route {prefix_no_slash}:3::101:0/112 community 47147:100
set routing-options rib inet6.0 static route {prefix_no_slash}:3::102:0/112 next-hop {prefix_no_slash}:3::4
set routing-options rib inet6.0 static route {prefix_no_slash}:3::102:0/112 community 47147:100
"""
    return base_config.replace(":::", ":")


def main():
    print("Enter IPv6 prefixes (one per line, Ctrl+C to finish):")
    prefixes = []
    try:
        while True:
            prefix = input()
            if prefix:
                prefixes.append(prefix)
            else:
                break
    except KeyboardInterrupt:
        pass

    print(colored("\nGenerated Juniper configuration:\n", 'green'))
    for prefix in prefixes:
        config = generate_config(prefix)
        print(config)
        print(colored("------------------------------------------------------------------------------------------\n", 'yellow'))
    
	# Exit prompt
    input(colored('Press ENTER to exit', attrs=['dark']))

    # Return to the main menu
    os.system("python mainmenu.py")



if __name__ == "__main__":
    main()
