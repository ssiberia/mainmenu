from termcolor import colored
from terminaltables import AsciiTable
import os

def print_table(header, data):
    table_data = [["Type", "Quantity"]]
    for item_type, count in data.items():
        if count != 0:
            table_data.append([item_type, count])

    print(colored(f"\n{header}", "magenta"))
    table = AsciiTable(table_data)
    print(colored(table.table, "cyan"))


def main():
    try:
      sfp_counts = {
          "100G SR4": 0,
          "40G SR4": 0,
          "10G LR": 0,
          "10G SR - Juniper": 0,
          "10G SR - Netapp" : 0,
          "10G SR - Server" : 0,
          "1G LX": 0,
          "1G SX": 0,
          "1G T": 0
      }

      cable_counts = {
          "C13 C14 blue 1.5m": 0,
          "C13 C14 black 1.5m": 0,
          "C13 C14 blue 1.8m": 0,
          "C13 C14 black 1.8m": 0,
          "MTP 1m": 0,
          "MTP 2m": 0,
          "SM 1m": 0,
          "SM 2m": 0,
          "SM 3m": 0,
          "MM 1m": 0,
          "MM 2m": 0,
          "MM 3m": 0,
          "UTP green 1m": 0,
          "UTP green 2m": 0,
          "UTP green 3m": 0,
          "UTP red 1m": 0,
          "UTP red 2m": 0,
          "UTP red 3m": 0,
          "UTP grey 0.5m": 0,
          "UTP grey 1m": 0,
          "UTP grey 2m": 0,
          "UTP grey 3m": 0,
          "C13/Schuko blue 0.9m": 0,
          "C13/Schuko black 0.9m": 0
      }

      # routers * 2
      sfp_counts["10G LR"] += 5 * 2
      sfp_counts["1G LX"] += 3 * 2
      sfp_counts["40G SR4"] += 2 * 2
      sfp_counts["100G SR4"] += 1 * 2
      cable_counts["C13 C14 blue 1.8m"] += 1 * 2
      cable_counts["C13 C14 black 1.8m"] += 1 * 2
      # to csw
      cable_counts["MTP 2m"] += 2 * 2
      # between dcr's
      cable_counts["MTP 1m"] += 1
      # upstreams + precabling
      cable_counts["SM 1m"] += 4
      
      # sw switches *2
      sfp_counts["10G SR - Juniper"] += 16 * 2
      sfp_counts["1G SX"] += 2 * 2
      sfp_counts["1G T"] += 2 * 2
      sfp_counts["1G LX"] += 4 * 2
      sfp_counts["10G LR"] += 4 * 2
      sfp_counts["40G SR4"] += 2 * 2
      sfp_counts["100G SR4"] += 2 * 2
      cable_counts["C13 C14 blue 1.5m"] += 1 * 2
      cable_counts["C13 C14 black 1.5m"] += 1 * 2
      # VC
      cable_counts["MTP 1m"] += 2
      # upstream precabling
      cable_counts["SM 2m"] += 2

    # serial server
      cable_counts["C13 C14 blue 1.8m"] += 1
      cable_counts["UTP red 2m"] += 1*2
      cable_counts["UTP green 1m"] += 2
      cable_counts["UTP green 2m"] += 5

      # mgt switch
      sfp_counts["1G LX"] += 3
      cable_counts["C13 C14 black 1.8m"] += 1
      cable_counts["SM 2m"] += 2

    # firewalls
      cable_counts["UTP grey 0.5m"] += 1
      cable_counts["UTP grey 1m"] += 1*2
      cable_counts["UTP grey 2m"] += 1*2
      # primary
      cable_counts["C13/Schuko black 0.9m"] += 1
      # secondary
      cable_counts["C13/Schuko blue 0.9m"] += 1

      # Ask the user for the number of servers and netapp
      servers = int(input(colored("How many servers do you plan to install? ", "cyan")))
      netapp = int(input(colored("How many netApps do you plan to install? ", "yellow")))
      shelves = 0
      if netapp != 0:
          shelves = int(input(colored("How many extra shelves do you install next to the netapp? ", "yellow")))

      # each server needs 2 SFPs
      if servers != 0:
          sfp_counts["10G SR - Server"] += 2 * servers
          cable_counts["MM 2m"] += 2 * servers
          cable_counts["UTP red 2m"] += 1 * servers
          cable_counts["C13 C14 black 1.5m"] += 1 * servers
          cable_counts["C13 C14 blue 1.5m"] += 1 * servers

      # each netapp needs 4 SFPs
      if netapp != 0:
          sfp_counts["10G SR - Netapp"] += netapp * 4
          cable_counts["UTP red 3m"] += netapp * 2
          cable_counts["MM 3m"] += netapp * 4
          cable_counts["C13 C14 black 1.5m"] += netapp * 1
          cable_counts["C13 C14 blue 1.5m"] += netapp * 1

      if shelves != 0:
          cable_counts["C13 C14 black 1.5m"] += 1 * shelves
          cable_counts["C13 C14 blue 1.5m"] += 1 * shelves

      # Print the result
      print_table("SFP Summary Table", sfp_counts)
      print_table("Cable Summary Table", cable_counts)

      try:
          input(colored('\nPress ENTER to exit', attrs=['dark']))
      except KeyboardInterrupt:
          pass
    except KeyboardInterrupt:
      pass

    os.system("python mainmenu.py")


if __name__ == "__main__":
    main()

