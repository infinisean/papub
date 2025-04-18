import os
import subprocess
from palo_api_metrics import query_firewall_data

def get_firewall_list():
    # Placeholder for querying Panorama to get a list of firewalls
    # Replace this with actual logic to query Panorama
    return [1, 2, 3]  # Example store numbers

def main():
    firewalls = get_firewall_list()
    for store_number in firewalls:
        print(f"Spawning process for store number: {store_number}")
        # For now, run the process sequentially
        query_firewall_data(store_number)
        # In the future, you can use subprocess or multiprocessing to run concurrently

if __name__ == "__main__":
    main()