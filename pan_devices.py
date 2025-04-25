import requests
import os
import json
from xml.etree import ElementTree as ET
import logging
import functions

def read_file(file_path):
    logging.debug(f"Attempting to read file: {file_path}")
    with open(file_path, 'r') as file:
        content = file.read().strip()
    logging.debug(f"Successfully read file: {file_path}")
    return content



# Example usage
if __name__ == "__main__":
    active_panorama = "A46PANORAMA"  # Replace with the actual active Panorama instance
    get_pan_devices(active_panorama)