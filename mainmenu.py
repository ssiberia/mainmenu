#!/usr/bin/env python3
import os
import json
import sys
import time
from datetime import datetime
from termcolor import colored
from pathlib import Path

CONFIG_FILE = "tools.json"

def create_default_config():
    """Create a default configuration file if none exists."""
    default_config = [
        {
            "name": "BGPq4",
            "script": "bgpq4.py",
            "description": "Query IRR databases using bgpq4"
        },
        {
            "name": "IP Calculator",
            "script": "netmaskcalc.py",
            "description": "Calculate network information from IP/netmask"
        },
        {
            "name": "MAC Lookup",
            "script": "maclookup.py",
            "description": "Lookup MAC address vendor and format conversion"
        },
        {
            "name": "IP Visualization (NO VPN)",
            "script": "ipinfo.py",
            "description": "Visualize IP route paths on a world map"
        },
        {
            "name": "IP Info (RIPE, etc.)",
            "script": "ip_ripe.py",
            "description": "Query IP information from RIPE and other RIRs"
        },
        {
            "name": "AS PeeringDB Data",
            "script": "peeringdb.py",
            "description": "Fetch AS information from PeeringDB"
        },
        {
            "name": "NLNOG Discovery",
            "script": "nlnog_discovery.py",
            "description": "Query NLNOG IRR Explorer API for prefix information"
        }
    ]
    
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=2)
        print(colored(f"Created default configuration file: {CONFIG_FILE}", "green"))
    except Exception as e:
        print(colored(f"Error creating default configuration: {str(e)}", "red"))
        sys.exit(1)

def load_config():
    """Load the tool configuration from the config file."""
    if not os.path.exists(CONFIG_FILE):
        create_default_config()
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(colored(f"Error loading configuration: {str(e)}", "red"))
        sys.exit(1)

def print_banner():
    """Print a simple ASCII art banner."""
    banner = """
    ╔═══════════════════════════════════════════════════╗
    ║                Network Tools Menu                 ║
    ╚═══════════════════════════════════════════════════╝
    """
    print(colored(banner, 'blue'))

def get_available_tools(tools_config):
    """Filter the tools list to only include available scripts."""
    available_tools = []
    
    for tool in tools_config:
        script_path = tool["script"]
        if os.path.exists(script_path):
            available_tools.append(tool)
        else:
            print(colored(f"Warning: {tool['name']} script not found ({script_path})", "yellow"))
    
    return available_tools

def list_tools(tools):
    """Display the available tools with numbering."""
    print(colored("\nAvailable tools:", 'yellow'))
    
    for index, tool in enumerate(tools, start=1):
        name = tool["name"]
        description = tool.get("description", "")
        
        # Print the tool with its number
        print(colored(f"{index}. ", 'cyan') + colored(name, 'white') + 
              (f" - {description}" if description else ""))
    
    # Add exit option
    print(colored(f"{len(tools) + 1}. ", 'cyan') + colored("Exit", 'white'))

def get_tool_choice(tools_list_length):
    """Get the user's tool choice with input validation."""
    while True:
        try:
            choice = input(colored('\nEnter option number: ', 'yellow'))
            int_choice = int(choice)
            
            if 1 <= int_choice <= tools_list_length:
                return int_choice - 1  # Convert to 0-based index
            elif int_choice == tools_list_length + 1:
                return None  # Exit chosen
            else:
                print(colored("Invalid input, please enter a valid number.", 'red'))
        except ValueError:
            print(colored("Invalid input, please enter a number.", 'red'))
        except KeyboardInterrupt:
            print("\n" + colored("Exiting...", 'yellow'))
            return None

def launch_tool(script_path):
    """Launch a tool script with error handling."""
    if not os.path.exists(script_path):
        print(colored(f"Error: Script {script_path} not found.", 'red'))
        return False
    
    try:
        print(colored(f"Launching {script_path}...", 'green'))
        exit_code = os.system(f"python3 {script_path}")
        
        if exit_code != 0:
            print(colored(f"Warning: Tool exited with code {exit_code}", 'yellow'))
        
        return True
    except Exception as e:
        print(colored(f"Error launching tool: {str(e)}", 'red'))
        input(colored('Press ENTER to continue', 'blue'))
        return False

def main():
    """Main function to display the menu and handle user interactions."""
    try:
        # Load tool configuration
        tools_config = load_config()
        
        while True:
            # Print banner
            print_banner()
            
            # Show current date and time
            now = datetime.now()
            current_day = now.strftime("%d.%m.%Y, %A, Week: %U+1, %I:%M %p")
            print(colored(f"Today is {current_day}", 'green'))
            
            # Get available tools
            available_tools = get_available_tools(tools_config)
            
            if not available_tools:
                print(colored("No tools available. Please check your configuration.", 'red'))
                sys.exit(1)
            
            # List available tools
            list_tools(available_tools)
            
            # Get user's choice
            choice = get_tool_choice(len(available_tools))
            
            if choice is None:
                print(colored("Exiting program...", 'yellow'))
                sys.exit(0)
            
            # Launch the selected tool
            selected_tool = available_tools[choice]
            launch_tool(selected_tool["script"])
            
            # Small delay before showing the menu again
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n" + colored("Exiting program...", 'yellow'))
        sys.exit(0)
    except Exception as e:
        print(colored(f"An unexpected error occurred: {str(e)}", 'red'))
        input(colored('Press ENTER to exit', 'blue'))
        sys.exit(1)

if __name__ == "__main__":
    main()