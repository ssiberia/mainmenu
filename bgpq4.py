import os
import webbrowser
import subprocess
from termcolor import colored

def print_usage_guide():
    """Display a usage guide for the bgpq4 tool."""
    print(colored("==== BGPq4 Tool Usage Guide ====", 'cyan', attrs=['bold']))
    print(colored("This tool helps you query Internet Routing Registry (IRR) databases using bgpq4.", 'white'))
    print(colored("Usage:", 'yellow'))
    print("  1. Select an IRR source from the list (RADB for all, or a specific registry)")
    print("  2. Choose between IPv4 and IPv6 queries")
    print("  3. Enter an AS set (e.g. 1234 for AS1234)")
    print("  4. View the prefix count and optionally the full prefix list")
    print("  5. Optionally check PeeringDB information")
    
    print(colored("Common BGPq4 Use Cases:", 'yellow'))
    print("  - Query prefixes advertised by an autonomous system")
    print("  - Verify IRR records for accuracy")
    print("  - Check prefix counts across multiple IRR databases")
    print("  - Research autonomous system information")

def select_irr_source():
    """Prompt the user to select an IRR source."""
    irr_sources = [
        {
            "name": "RADB (All IRRs)", 
            "specific_source": False,
            "description": "Queries all IRR databases through RADB. This is the most comprehensive option."
        },
        {
            "name": "RPKI only", 
            "source": "RPKI",
            "specific_source": True,
            "description": "Resource Public Key Infrastructure - cryptographically validated route origins."
        },
        {
            "name": "RIPE only", 
            "source": "RIPE",
            "specific_source": True,
            "description": "RIPE NCC manages IP addresses for Europe, Middle East, and parts of Central Asia."
        },
        {
            "name": "ARIN only", 
            "source": "ARIN",
            "specific_source": True,
            "description": "ARIN manages IP addresses for the United States, Canada, and parts of the Caribbean."
        },
        {
            "name": "APNIC only", 
            "source": "APNIC",
            "specific_source": True,
            "description": "APNIC manages IP addresses for the Asia-Pacific region."
        },
        {
            "name": "AFRINIC only", 
            "source": "AFRINIC",
            "specific_source": True,
            "description": "AFRINIC manages IP addresses for Africa."
        },
        {
            "name": "LACNIC only", 
            "source": "LACNIC",
            "specific_source": True,
            "description": "LACNIC manages IP addresses for Latin America and the Caribbean."
        }
    ]
    
    print(colored("Select IRR source:", 'blue'))
    for i in range(len(irr_sources)):
        print(f"{i+1}. {irr_sources[i]['name']} - {irr_sources[i]['description']}")
    
    try:
        choice = int(input(colored(f"Enter your choice (1-{len(irr_sources)}): ", 'yellow')))
        if 1 <= choice <= len(irr_sources):
            print(colored(f"Selected: {irr_sources[choice-1]['name']}", 'green'))
            return irr_sources[choice-1]
        else:
            print(colored("Invalid choice. Using default (RADB).", 'red'))
            return irr_sources[0]
    except ValueError:
        print(colored("Invalid input. Using default (RADB).", 'red'))
        return irr_sources[0]

def run_bgpq4(irr_source, asn, ip_version=4):
    """Run the bgpq4 command with appropriate flags based on the IRR source."""
    # Always start with the host flag for RADB
    cmd = ['bgpq4', '-h', 'whois.radb.net']
    
    # Add specific source flag if requested
    if irr_source['specific_source']:
        cmd.extend(['-S', irr_source['source']])
    
    # Add IP version flag
    if ip_version == 6:
        cmd.append('-6')
    
    cmd.append('AS' + asn)
    
    # Print the command being run
    print(colored(f"\nExecuting: {' '.join(cmd)}", 'cyan'))
    
    # Run the command directly
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(colored(f"bgpq4 error: {result.stderr}", 'red'))
            return None
        return result.stdout
    except Exception as e:
        print(colored(f"Error executing bgpq4: {str(e)}", 'red'))
        return None

def main():
    try:
        # Display usage guide
        print_usage_guide()
        
        # Select IRR source
        irr_source = select_irr_source()
        
        # Select IP version
        print(colored("\nSelect IP version:", 'blue'))
        print("1. IPv4")
        print("2. IPv6")
        
        try:
            ip_choice = int(input(colored("\nEnter your choice (1-2): ", 'yellow')))
            ip_version = 6 if ip_choice == 2 else 4
            print(colored(f"Using IPv{ip_version}", 'green'))
        except ValueError:
            print(colored("Invalid input. Using default (IPv4).", 'red'))
            ip_version = 4
        
        # Prompt the user for the AS set (not case sensitive)
        print(colored("\nPlease give me the AS number or AS set (not case sensitive): ", 'blue') + "AS", end='')
        asset = input()
        
        # Check if the AS set is provided
        if str(asset) == "":
            print(colored("AS number or AS set is missing!", 'red'))
        else:
            # Normalize the AS number/set
            asset = str(asset).upper()
            
            # Run the bgpq4 command
            output = run_bgpq4(irr_source, asset, ip_version)
            
            if output:
                # Count lines that aren't just whitespace
                lines = [line for line in output.split('\n') if line.strip()]
                prefix_count = len(lines)
                
                print(colored(f"\nNumber of lines in output: {prefix_count}", 'yellow'))
                
                # Ask the user if they want to see the full output
                pfl = input(colored('\nDo you need the whole prefix list? (y/n): ', 'blue'))
                if pfl.lower() == 'y':
                    print(colored(f"\n==== IPv{ip_version} Prefix List ====", 'cyan'))
                    print(output)
                
                # Ask the user if they want to open the PeeringDB website
                pdb = input(colored('\nDo you need PeeringDB website? (y/n): ', 'blue'))
                if pdb.lower() == 'y':
                    # Remove the hyphen from the beginning of the string, if it exists
                    asset_without_hyphen = asset.lstrip("-")
                    
                    # Create the URL and open the PeeringDB website
                    purl = "https://www.peeringdb.com/search?q=" + asset_without_hyphen
                    webbrowser.open(purl)
            else:
                print(colored("\nNo output from bgpq4 command.", 'red'))
        
        # Exit prompt
        input(colored('\nPress ENTER to exit', 'blue'))
    except KeyboardInterrupt:
        print(colored("\nOperation cancelled by user.", 'yellow'))
    except Exception as e:
        print(colored(f"\nAn error occurred: {str(e)}", 'red'))
    finally:
        # Return to the main menu
        os.system("python3 mainmenu.py")

if __name__ == "__main__":
    main()