import requests
import os
import time
import mysql.connector
import argparse
import logging
from xml.etree import ElementTree as ET
from xml.dom import minidom







def main():
    parser = argparse.ArgumentParser(description='Gather metrics for a specified firewall.')
    parser.add_argument('store_number', type=int, help='The 4-digit store number of the firewall')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--live-db', action='store_true', help='Insert data into the live database')
    parser.add_argument('--invocation', choices=['cli', 'streamlit'], default='cli', help='Specify the invocation method')
    args = parser.parse_args()

    setup_logging(args.debug)
    logging.debug(f"Invocation method: {args.invocation}")

    # Example usage of get_pan_connected_devices
    panorama_instances = ['a46panorama', 'l17panorama']  # Replace with actual Panorama hostnames
    for panorama in panorama_instances:
        devices = get_pan_connected_devices(panorama)
        for device in devices:
            print(f"Hostname: {device['hostname']}, Model: {device['model']}, Serial: {device['serial']}, Mgmt IP: {device['mgmt_ip']}")
        print(f"Total connected devices from {panorama}: {len(devices)}")

    # query_firewall_data(args.store_number, args.live_db)

if __name__ == "__main__":
    main()
    