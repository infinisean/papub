import streamlit as st
import requests
from xml.etree import ElementTree as ET
import urllib3
import os
import time
import matplotlib.pyplot as plt

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ensure the logs directory exists
if not os.path.exists("logs"):
    os.makedirs("logs")

# Function to get API key
def get_api_key(hostname, username, password):
    url = f"https://{hostname}/api/?type=keygen"
    payload = {'user': username, 'password': password}
    response = requests.post(url, data=payload, verify=False)
    if response.status_code == 200:
        xml_response = ET.fromstring(response.text)
        if xml_response.attrib['status'] == 'success':
            return xml_response.find('.//key').text
    return None

# Function to get system info and additional details
def get_system_info(hostname, api_key):
    headers = {'X-PAN-KEY': api_key}

    # Helper function to make API requests
    def api_request(cmd, query_name):
        url = f"https://{hostname}/api/?type=op&cmd={cmd}"
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            # Log the raw XML response to a file
            with open(f"logs/{hostname}_{query_name}.xml", "w") as file:
                file.write(response.text)
            return ET.fromstring(response.text)
        return None

    # Get basic system info
    system_info = api_request("<show><system><info></info></system></show>", "system_info")

    # Get license information
    license_info = api_request("<request><license><info></info></license></request>", "license_info")

    # Get resource utilization
    resource_info = api_request("<show><system><resources></resources></system></show>", "resource_info")

    # Get interface information
    interface_info = api_request("<show><interface>all</interface></show>", "interface_info")

    # Get HA status
    ha_info = api_request("<show><high-availability><state></state></high-availability></show>", "ha_info")

    return {
        'system_info': system_info,
        'license_info': license_info,
        'resource_info': resource_info,
        'interface_info': interface_info,
        'ha_info': ha_info
    }

# Function to extract and format information
def extract_info(info):
    data = {}

    # Extract basic system information
    if info['system_info'] is not None:
        system_info = info['system_info']
        data.update({
            'Hostname': system_info.find('.//hostname').text,
            'IP Address': system_info.find('.//ip-address').text,
            'Uptime': system_info.find('.//uptime').text,
            'Model': system_info.find('.//model').text,
            'Version': system_info.find('.//sw-version').text
        })

    # Extract license information
    if info['license_info'] is not None:
        licenses = info['license_info'].findall('.//entry')
        data['Licenses'] = [license.find('feature').text for license in licenses]

    # Extract resource utilization
    if info['resource_info'] is not None:
        resource_info = info['resource_info'].find('.//result').text.splitlines()
        # Parse load averages
        load_line = resource_info[0]
        load_averages = load_line.split()[-3:]
        data['Load Averages'] = load_averages

        # Parse CPU usage
        cpu_line = next(line for line in resource_info if line.startswith("%Cpu"))
        cpu_idle = float(cpu_line.split()[-4].replace("id,", ""))
        data['CPU Usage'] = 100 - cpu_idle

        # Parse memory usage
        mem_line = next(line for line in resource_info if line.startswith("MiB Mem:"))
        mem_values = mem_line.split()
        total_mem = float(mem_values[2])
        used_mem = float(mem_values[4])
        free_mem = total_mem - used_mem
        data['Memory'] = {'Total': total_mem, 'Used': used_mem, 'Free': free_mem}
    # Extract interface information
    if info['interface_info'] is not None:
        interfaces = info['interface_info'].findall('.//entry')
        data['Interfaces'] = [{'Name': iface.find('name').text, 'IP': iface.find('ip').text, 'Status': iface.find('status').text} for iface in interfaces]

    # Extract HA status
    if info['ha_info'] is not None:
        ha_info = info['ha_info']
        data['HA Status'] = ha_info.find('.//state').text

    return data

# Streamlit app
def main():
    st.title("Palo Alto Panorama Health Dashboard")

    # Check for the existence of the "testingkey" file
    api_key = None
    if os.path.exists("testingkey"):
        with open("testingkey", "r") as file:
            api_key = file.read().strip()
        st.info("Using API key from 'testingkey' file.")
    else:
        # Prompt for user credentials
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            # Get API keys for both Panorama instances
            lak_api_key = get_api_key('l17panorama', username, password)
            atl_api_key = get_api_key('a46panorama', username, password)

            if lak_api_key and atl_api_key:
                st.success("Successfully obtained API keys.")
                api_key = lak_api_key  # Use one of the keys for further operations
            else:
                st.error("Failed to obtain API keys. Please check your credentials.")

    if api_key:
        # Get system info for both Panorama instances
        lak_info = get_system_info('l17panorama', api_key)
        atl_info = get_system_info('a46panorama', api_key)

        if lak_info and atl_info:
            # Extract relevant information
            lak_data = extract_info(lak_info)
            atl_data = extract_info(atl_info)

            # Display the information in a table
            st.table([lak_data, atl_data])

            # Set up dynamic updates for resource info
            while True:
                # Re-query resource info
                lak_resource_info = get_system_info('l17panorama', api_key)['resource_info']
                atl_resource_info = get_system_info('a46panorama', api_key)['resource_info']

                # Extract and display updated resource info
                lak_resource_data = extract_info({'resource_info': lak_resource_info})
                atl_resource_data = extract_info({'resource_info': atl_resource_info})

                # Update load average graph
                st.line_chart([float(lak_resource_data['Load Averages'][0]), float(atl_resource_data['Load Averages'][0])])

                # Update CPU usage graph
                st.line_chart([lak_resource_data['CPU Usage'], atl_resource_data['CPU Usage']])

                # Update memory usage pie chart
                fig, ax = plt.subplots()
                ax.pie([lak_resource_data['Memory']['Used'], lak_resource_data['Memory']['Free']],
                       labels=['Used', 'Free'], autopct='%1.1f%%')
                st.pyplot(fig)

                # Wait for 10 seconds before updating
                time.sleep(10)
        else:
            st.error("Failed to retrieve system information.")

if __name__ == "__main__":
    main()

