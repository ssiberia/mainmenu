import os
import re
import json
import folium
import socket
import webbrowser
import requests
import time
from termcolor import colored
from folium.plugins import AntPath, Fullscreen, MousePosition
from collections import defaultdict
import ipaddress
import csv
from datetime import datetime

def is_valid_ip(ip):
    """Check if a string is a valid IP address."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def resolve_hostname(hostname):
    """Resolve a hostname to an IP address using DNS."""
    if hostname == "???" or hostname.lower() == "unknown":
        return None
    
    try:
        ip = socket.gethostbyname(hostname)
        if is_valid_ip(ip):
            return ip
    except socket.gaierror:
        pass
    
    return None

def get_location(ip):
    """Get the geolocation data for an IP address."""
    # Skip private, loopback, and unspecified IPs
    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_unspecified or ip_obj.is_link_local:
            return None
    except ValueError:
        return None
    
    # Query ipinfo.io API
    try:
        # Use ipinfo.io API (free tier allows 50,000 requests per month)
        response = requests.get(f"https://ipinfo.io/{ip}/json")
        if response.status_code == 200:
            data = response.json()
            
            # Extract and format location data
            location = {
                "ip": ip,
                "country": data.get("country", "Unknown"),
                "region": data.get("region", "Unknown"),
                "city": data.get("city", "Unknown"),
                "asn": data.get("org", "Unknown"),
                "lat": None,
                "lon": None
            }
            
            # Parse coordinates if available
            if "loc" in data and data["loc"]:
                try:
                    lat, lon = data["loc"].split(",")
                    location["lat"] = float(lat)
                    location["lon"] = float(lon)
                except (ValueError, TypeError):
                    pass
                
            # Return location if we have coordinates
            if location["lat"] is not None and location["lon"] is not None:
                return location
            
    except Exception as e:
        print(colored(f"Error querying IP data for {ip}: {e}", "red"))
    
    # Fallback to ip-api.com if ipinfo.io failed or had no coordinates
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,lat,lon,as,query")
        data = response.json()
        
        if data.get("status") == "success":
            location = {
                "ip": ip,
                "country": data.get("country", "Unknown"),
                "region": data.get("regionName", "Unknown"),
                "city": data.get("city", "Unknown"),
                "asn": data.get("as", "Unknown"),
                "lat": data.get("lat"),
                "lon": data.get("lon")
            }
            
            return location
        
    except Exception as e:
        print(colored(f"Error querying fallback API for {ip}: {e}", "red"))
    
    return None

def extract_ips_from_trace(trace_output):
    """Extract IPs with hop numbers from various traceroute outputs."""
    ips_with_hops = []
    packet_loss = {}
    hostnames = {}
    asn_info = {}
    
    # Try to match MTR style with hostnames, IPs, and packet loss
    # Format: 1. AS47583 153.92.2.241 0.0% ...
    mtr_full_pattern = re.compile(r"^\s*(\d+)\.\s+(?:AS(\d+|\?\?\?))\s+([^\s]+)\s+(\d+\.?\d*|100\.0)%", re.MULTILINE)
    matches = mtr_full_pattern.findall(trace_output)
    
    if matches:
        print(colored("Detected MTR output with packet loss information", "green"))
        for hop, asn, host, loss in matches:
            hop = int(hop)
            # Check if host is an IP or hostname
            if is_valid_ip(host):
                ip = host
            else:
                # It's a hostname or ??? - try to resolve
                if host == "???" or host.lower() == "unknown":
                    # Skip unresolvable hops but record the loss
                    packet_loss[hop] = float(loss.rstrip('%'))
                    hostnames[hop] = "???"
                    continue
                
                ip = resolve_hostname(host)
                if not ip:
                    # Skip unresolvable hostnames but record the loss
                    packet_loss[hop] = float(loss.rstrip('%'))
                    hostnames[hop] = host
                    continue
            
            # Record the data
            ips_with_hops.append((hop, ip))
            packet_loss[hop] = float(loss.rstrip('%'))
            hostnames[hop] = host
            
            # Store ASN if available
            if asn and asn != "???":
                asn_info[hop] = f"AS{asn}"
    else:
        # First, try to match MTR-style output with hop numbers (handles specific MTR format)
        mtr_detailed_pattern = re.compile(r"^\s*(\d+)\.\s+[\w\.\-]+\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", re.MULTILINE)
        matches = mtr_detailed_pattern.findall(trace_output)
        
        if matches:
            for hop, ip in matches:
                ips_with_hops.append((int(hop), ip))
        else:
            # Try standard MTR pattern
            mtr_pattern = re.compile(r"^\s*(\d+)(?:\.|:).*?\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", re.MULTILINE)
            matches = mtr_pattern.findall(trace_output)
            
            if matches:
                for hop, ip in matches:
                    ips_with_hops.append((int(hop), ip))
            else:
                # Try standard traceroute style
                traceroute_pattern = re.compile(r"^\s*(\d+)\s+(?:[\w\-\.]+\s+)?\(?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", re.MULTILINE)
                matches = traceroute_pattern.findall(trace_output)
                
                if matches:
                    for hop, ip in matches:
                        ips_with_hops.append((int(hop), ip))
                else:
                    # Last resort: just extract all IPs and assume sequential ordering
                    ip_pattern = re.compile(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b")
                    ips = ip_pattern.findall(trace_output)
                    ips_with_hops = [(i+1, ip) for i, ip in enumerate(ips)]
    
        # If we don't have packet loss from the full pattern match, try to extract it separately
        if not packet_loss:
            loss_pattern = re.compile(r"^\s*(\d+).*?(\d+\.?\d*|100\.0)%", re.MULTILINE)
            loss_matches = loss_pattern.findall(trace_output)
            for hop, loss in loss_matches:
                packet_loss[int(hop)] = float(loss.rstrip('%'))
        
        # Try to extract hostnames if we don't have them yet
        if not hostnames:
            hostname_pattern = re.compile(r"^\s*(\d+).*?\s+([a-zA-Z0-9\-\.]+)\s+", re.MULTILINE)
            hostname_matches = hostname_pattern.findall(trace_output)
            for hop, hostname in hostname_matches:
                if not is_valid_ip(hostname):  # Only store actual hostnames, not IPs
                    hostnames[int(hop)] = hostname
    
    # Filter out duplicate IPs while preserving order and hop number
    seen_ips = set()
    filtered_ips = []
    
    for hop, ip in ips_with_hops:
        if ip not in seen_ips and is_valid_ip(ip):
            seen_ips.add(ip)
            filtered_ips.append((hop, ip))
    
    return filtered_ips, packet_loss, hostnames, asn_info

def extract_latencies(trace_output, ips_with_hops):
    """Extract latencies for each hop if available in trace output."""
    latencies = {}
    
    # Iterate through IPs and try to find latency
    for hop, ip in ips_with_hops:
        # Look for lines with both the IP and ms values
        pattern = re.compile(r"(?:^|\s)" + re.escape(ip) + r".*?(\d+\.?\d*)\s*ms", re.MULTILINE)
        matches = pattern.findall(trace_output)
        
        if not matches:
            # Try alternative pattern for mtr output (columns)
            mtr_pattern = re.compile(r"^\s*" + str(hop) + r"\.\s+.*?\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)", re.MULTILINE)
            mtr_matches = mtr_pattern.findall(trace_output)
            if mtr_matches:
                # Take the average value from MTR (typically the 2nd value is avg)
                try:
                    latencies[(hop, ip)] = float(mtr_matches[0][1])  # Index 1 is typically the avg
                except (ValueError, IndexError):
                    pass
        else:
            # If multiple latency values, take the minimum
            try:
                latencies[(hop, ip)] = min(float(m) for m in matches)
            except ValueError:
                pass
    
    return latencies

def create_map(ips_with_hops, packet_loss, hostnames, asn_info, latencies=None):
    """Create a Folium map with the route visualization."""
    # Get locations for all IPs
    locations = []
    hop_data = []
    
    for hop, ip in ips_with_hops:
        location = get_location(ip)
        if location and location["lat"] is not None and location["lon"] is not None:
            location["hop"] = hop
            location["latency"] = latencies.get((hop, ip), None) if latencies else None
            location["packet_loss"] = packet_loss.get(hop, 0)
            location["hostname"] = hostnames.get(hop, "")
            location["asn_info"] = asn_info.get(hop, location["asn"])
            locations.append(location)
            hop_data.append((location["lat"], location["lon"]))
    
    # Create the map centered at the first valid location or default to world center
    if hop_data:
        m = folium.Map(location=hop_data[0], zoom_start=4)
    else:
        m = folium.Map(location=[0, 0], zoom_start=2)
    
    # Add fullscreen control
    Fullscreen().add_to(m)
    
    # Add mouse position
    MousePosition().add_to(m)
    
    # Color function based on packet loss
    def get_loss_color(loss):
        if loss == 0:
            return '#00cc00'  # Green for no loss
        elif loss < 5:
            return '#cccc00'  # Yellow for minor loss
        elif loss < 20:
            return '#ff9900'  # Orange for moderate loss
        else:
            return '#cc0000'  # Red for severe loss
    
    # Country counter
    countries = {}
    asns = {}
    
    # Add markers and create path
    for i, location in enumerate(locations):
        lat, lon = location["lat"], location["lon"]
        hop = location["hop"]
        loss = location["packet_loss"]
        hostname = location["hostname"]
        asn_display = location["asn_info"]
        
        # Count countries and ASNs
        country = location["country"]
        asn = location["asn"]
        countries[country] = countries.get(country, 0) + 1
        asns[asn] = asns.get(asn, 0) + 1
        
        # Popup content
        popup_html = f"""
        <div style="width: 220px">
        <b>Hop:</b> {hop}<br>
        <b>IP:</b> {location["ip"]}<br>
        """
        
        if hostname:
            popup_html += f"<b>Hostname:</b> {hostname}<br>"
            
        popup_html += f"""
        <b>Location:</b> {location["city"]}, {location["region"]}, {location["country"]}<br>
        <b>ASN:</b> {asn_display}<br>
        <b>Packet Loss:</b> {loss}%<br>
        """
        
        if location["latency"] is not None:
            popup_html += f"<b>Latency:</b> {location['latency']:.2f} ms<br>"
            
        popup_html += "</div>"
        
        # Create the marker with color based on packet loss
        marker_color = get_loss_color(loss)
        
        folium.CircleMarker(
            location=[lat, lon],
            radius=7,
            color=marker_color,
            fill=True,
            fill_color=marker_color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"Hop {hop}: {location['city']}, {location['country']} (Loss: {loss}%)"
        ).add_to(m)
        
        # Add hop number label
        folium.map.Marker(
            [lat, lon],
            icon=folium.DivIcon(
                icon_size=(20, 20),
                icon_anchor=(0, 0),
                html=f'<div style="font-size: 10pt; color: white; background-color: {marker_color}; border-radius: 50%; width: 20px; height: 20px; text-align: center; line-height: 20px;">{hop}</div>'
            )
        ).add_to(m)
    
    # Create lines between points
    if len(hop_data) > 1:
        AntPath(hop_data, color="blue", weight=2.5, opacity=0.8, tooltip="Route path").add_to(m)
    
    # Add title
    title_html = '''
    <div style="position: fixed; 
        top: 10px; left: 50px; width: 300px; height: 30px; 
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 5px;
        z-index: 900;
        font-size: 14pt;
        font-weight: bold;
        padding: 5px;
        text-align: center;">
        Network Route Visualization
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add packet loss legend
    legend_html = '''
    <div style="position: fixed; 
        top: 50px; right: 50px; width: 150px;
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 5px;
        z-index: 900;
        font-size: 10pt;
        padding: 10px;">
        <b>Packet Loss</b><br>
        <i class="fa fa-circle" style="color:#00cc00"></i> 0% (No Loss)<br>
        <i class="fa fa-circle" style="color:#cccc00"></i> 1-5% (Minor)<br>
        <i class="fa fa-circle" style="color:#ff9900"></i> 5-20% (Moderate)<br>
        <i class="fa fa-circle" style="color:#cc0000"></i> >20% (Severe)<br>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add unreachable hops information
    unreachable_hops = []
    for hop in sorted(packet_loss.keys()):
        if packet_loss[hop] == 100 and hop not in [h for h, _ in ips_with_hops]:
            hostname = hostnames.get(hop, "???")
            asn = asn_info.get(hop, "???")
            unreachable_hops.append((hop, hostname, asn))
    
    if unreachable_hops:
        unreachable_html = '''
        <div style="position: fixed; 
            bottom: 10px; right: 10px; max-width: 300px;
            background-color: rgba(255, 255, 255, 0.8);
            border-radius: 5px;
            z-index: 900;
            font-size: 10pt;
            padding: 10px;">
            <b>Unreachable Hops (100% Loss):</b><br>
        '''
        
        for hop, hostname, asn in unreachable_hops:
            unreachable_html += f"Hop {hop}: {hostname} {asn}<br>"
            
        unreachable_html += "</div>"
        m.get_root().html.add_child(folium.Element(unreachable_html))
    
    # Add country and ASN summary
    if countries:
        summary_html = '''
        <div style="position: fixed; 
            bottom: 10px; left: 10px; max-width: 300px;
            background-color: rgba(255, 255, 255, 0.8);
            border-radius: 5px;
            z-index: 900;
            font-size: 10pt;
            padding: 10px;">
            <b>Countries traversed:</b><br>
        '''
        
        for country, count in countries.items():
            summary_html += f"{country}: {count} hops<br>"
            
        summary_html += "<br><b>ASNs traversed:</b><br>"
        
        for asn, count in asns.items():
            summary_html += f"{asn.split(' ')[0]}: {count} hops<br>"
            
        summary_html += "</div>"
        m.get_root().html.add_child(folium.Element(summary_html))
    
    # Save map
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    map_file = f"trace_map_{timestamp}.html"
    m.save(map_file)
    
    return map_file, locations

def print_route_summary(ips_with_hops, locations, packet_loss, hostnames, asn_info, latencies=None):
    """Print a summary of the route to the console."""
    # Create lookup table for locations
    location_lookup = {loc["ip"]: loc for loc in locations}
    
    # Print header
    print("\n" + colored("=== Route Summary ===", "cyan", attrs=["bold"]))
    print(f"Total hops: {max(hop for hop, _ in ips_with_hops) if ips_with_hops else 0}")
    print(f"Mapped locations: {len(locations)}")
    
    # Count unreachable hops
    unreachable_count = sum(1 for loss in packet_loss.values() if loss == 100)
    if unreachable_count:
        print(colored(f"Unreachable hops: {unreachable_count}", "yellow"))
    
    # Count countries and ASNs
    countries = defaultdict(int)
    asns = defaultdict(int)
    
    for loc in locations:
        countries[loc["country"]] += 1
        asns[loc["asn"]] += 1
    
    print(colored("\nCountries traversed:", "yellow"))
    for country, count in countries.items():
        print(f"  {country}: {count} hop(s)")
    
    print(colored("\nASNs traversed:", "yellow"))
    for asn, count in asns.items():
        print(f"  {asn}: {count} hop(s)")
    
    # Print hop details
    print(colored("\nHop details:", "yellow"))
    print(colored(f"{'Hop':4} {'IP Address':15} {'Hostname':30} {'Loss':6} {'Latency':10} {'Location':20} {'ASN'}", "green"))
    print("-" * 100)
    
    # Get all hop numbers, including those without IPs
    all_hops = sorted(set([hop for hop, _ in ips_with_hops] + list(packet_loss.keys())))
    
    for hop in all_hops:
        # Find the IP for this hop if it exists
        ip = next((ip for h, ip in ips_with_hops if h == hop), None)
        
        if ip and ip in location_lookup:
            loc = location_lookup[ip]
            location_str = f"{loc['city']}, {loc['country']}"
            asn_str = loc["asn"]
        else:
            location_str = "Unknown"
            asn_str = asn_info.get(hop, "Unknown")
        
        hostname_str = hostnames.get(hop, "")[:29].ljust(29)
        
        # Get packet loss and format it
        loss = packet_loss.get(hop, 0)
        if loss == 0:
            loss_str = "0%"
            loss_color = "green"
        elif loss == 100:
            loss_str = "100%"
            loss_color = "red"
        else:
            loss_str = f"{loss}%"
            loss_color = "yellow"
        
        # Get latency if available
        if latencies and ip and (hop, ip) in latencies:
            latency_str = f"{latencies[(hop, ip)]:.2f} ms"
        else:
            latency_str = "N/A"
        
        # Format the line with color for packet loss
        ip_str = ip if ip else "???"
        line = f"{hop:4} {ip_str:15} {hostname_str} {loss_str:6} {latency_str:10} {location_str:20} {asn_str}"
        
        if loss == 100:
            print(colored(line, loss_color))
        else:
            # Only color the loss value
            print(f"{hop:4} {ip_str:15} {hostname_str} " + 
                  colored(f"{loss_str:6}", loss_color) + 
                  f" {latency_str:10} {location_str:20} {asn_str}")
    
    # Print packet loss issues
    print("\n" + colored("=== Packet Loss Analysis ===", "cyan", attrs=["bold"]))
    
    # Count segments with packet loss
    loss_segments = [(hop, loss) for hop, loss in packet_loss.items() if loss > 0]
    
    if not loss_segments:
        print(colored("No packet loss detected in the route!", "green"))
    else:
        print(colored(f"Found {len(loss_segments)} hop(s) with packet loss:", "yellow"))
        
        for hop, loss in sorted(loss_segments, key=lambda x: x[0]):
            hostname = hostnames.get(hop, "???")
            asn = asn_info.get(hop, "Unknown")
            
            if loss == 100:
                print(colored(f"  Hop {hop}: {hostname} - 100% loss (completely unreachable)", "red"))
            else:
                print(colored(f"  Hop {hop}: {hostname} - {loss}% loss", "yellow"))
            
            print(f"      ASN: {asn}")
            
            # Find the IP for this hop if it exists
            ip = next((ip for h, ip in ips_with_hops if h == hop), None)
            if ip:
                print(f"      IP: {ip}")
                
                # Get location if available
                if ip in location_lookup:
                    loc = location_lookup[ip]
                    print(f"      Location: {loc['city']}, {loc['region']}, {loc['country']}")
    
    # Print end-to-end latency if available
    if latencies:
        first_hop = min(hop for hop, _ in ips_with_hops)
        last_hop = max(hop for hop, _ in ips_with_hops)
        
        first_ip = next((ip for hop, ip in ips_with_hops if hop == first_hop), None)
        last_ip = next((ip for hop, ip in ips_with_hops if hop == last_hop), None)
        
        if first_ip and last_ip and (first_hop, first_ip) in latencies and (last_hop, last_ip) in latencies:
            first_latency = latencies[(first_hop, first_ip)]
            last_latency = latencies[(last_hop, last_ip)]
            
            print("\n" + colored("=== End-to-End Latency ===", "cyan", attrs=["bold"]))
            print(f"First hop latency: {first_latency:.2f} ms")
            print(f"Last hop latency: {last_latency:.2f} ms")
            print(f"Approximate end-to-end latency: {last_latency:.2f} ms")

def save_route_data(ips_with_hops, locations, packet_loss, hostnames, asn_info, latencies=None):
    """Save route data to a CSV file for future reference."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = f"trace_data_{timestamp}.csv"
    
    # Create lookup table for locations
    location_lookup = {loc["ip"]: loc for loc in locations}
    
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Hop', 'IP', 'Hostname', 'Packet Loss (%)', 'Latency (ms)', 
                         'City', 'Region', 'Country', 'ASN'])
        
        # Get all hop numbers, including those without IPs
        all_hops = sorted(set([hop for hop, _ in ips_with_hops] + list(packet_loss.keys())))
        
        for hop in all_hops:
            # Find the IP for this hop if it exists
            ip = next((ip for h, ip in ips_with_hops if h == hop), None)
            hostname = hostnames.get(hop, "")
            loss = packet_loss.get(hop, 0)
            
            row = [hop, ip if ip else "???", hostname, loss]
            
            # Add latency if available
            if latencies and ip and (hop, ip) in latencies:
                row.append(f"{latencies[(hop, ip)]:.2f}")
            else:
                row.append("N/A")
            
            # Add location data if available
            if ip and ip in location_lookup:
                loc = location_lookup[ip]
                row.extend([loc["city"], loc["region"], loc["country"], loc["asn"]])
            else:
                row.extend(["Unknown", "Unknown", "Unknown", asn_info.get(hop, "Unknown")])
                
            writer.writerow(row)
    
    print(colored(f"\nRoute data saved to {csv_file}", "green"))
    return csv_file

def main():
    """Main function to run the IP visualization tool."""
    print(colored("\n=== Network Route Visualization Tool ===", "cyan", attrs=["bold"]))
    print(colored("\nThis tool visualizes network routes from traceroute or MTR output.", "white"))
    print(colored("It maps the path across different countries and ASNs.", "white"))
    print(colored("It now supports packet loss detection and hostname resolution.", "white"))
    
    print(colored("\nPlease paste your traceroute/MTR results and press Ctrl+C when done:", "blue"))
    
    # Collect trace output
    trace_output = ""
    try:
        while True:
            line = input()
            trace_output += line + "\n"
    except KeyboardInterrupt:
        print(colored("\nProcessing trace data...", "green"))
    except EOFError:
        print(colored("\nProcessing trace data...", "green"))
    
    if not trace_output.strip():
        print(colored("No input provided. Exiting.", "red"))
        input(colored('\nPress ENTER to exit', 'blue'))
        os.system("python3 mainmenu.py")
        return
    
    # Extract IPs with hop numbers and metadata
    ips_with_hops, packet_loss, hostnames, asn_info = extract_ips_from_trace(trace_output)
    
    if not ips_with_hops:
        print(colored("No valid IP addresses found in the trace output. Exiting.", "red"))
        input(colored('\nPress ENTER to exit', 'blue'))
        os.system("python3 mainmenu.py")
        return
    
    print(colored(f"Found {len(ips_with_hops)} unique IP addresses in trace.", "green"))
    
    # Extract latencies if available
    latencies = extract_latencies(trace_output, ips_with_hops)
    
    try:
        # Create the map
        print(colored("Fetching geolocation data and creating map...", "green"))
        map_file, locations = create_map(ips_with_hops, packet_loss, hostnames, asn_info, latencies)
        
        # Print route summary
        print_route_summary(ips_with_hops, locations, packet_loss, hostnames, asn_info, latencies)
        
        # Save route data
        save_route_data(ips_with_hops, locations, packet_loss, hostnames, asn_info, latencies)
        
        # Open the map in the default browser
        print(colored(f"\nMap saved as {map_file}", "green"))
        print(colored("Opening map in browser...", "green"))
        
        # Use absolute path for opening the file
        abs_path = os.path.abspath(map_file)
        try:
            # Try multiple approaches to open the browser
            if not webbrowser.open('file://' + abs_path):
                if not webbrowser.open(abs_path):
                    os.system(f"xdg-open {abs_path} || open {abs_path} || start {abs_path}")
                    print(colored("Used system command to open browser", "yellow"))
        except Exception as e:
            print(colored(f"Error opening browser: {e}", "red"))
            print(colored(f"Please open {abs_path} manually in your browser", "yellow"))
    
    except Exception as e:
        print(colored(f"An error occurred: {str(e)}", "red"))
    
    # Exit prompt
    input(colored('\nPress ENTER to exit', 'blue'))
    
    # Return to the main menu - ensure this actually runs
    os.system("python3 mainmenu.py")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(colored(f"Fatal error: {str(e)}", "red"))
        input(colored('\nPress ENTER to exit', 'blue'))
        os.system("python3 mainmenu.py")