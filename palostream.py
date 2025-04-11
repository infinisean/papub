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
    #Write raw output to a file
    with open(f"logs/{hostname}_system_info.xml", "w") as file:
        file.write(system_info.text)

    # Get license information
    license_info = api_request("<request><license><info></info></license></request>", "license_info")
    # Write raw output to a file
    with open(f"logs/{hostname}_license_info.xml", "w") as file:
        file.write(license_info.text)
        
    # Get resource utilization
    resource_info = api_request("<show><system><resources></resources></system></show>", "resource_info")
    # Write raw output to a file
    with open(f"logs/{hostname}_resource_info.xml", "w") as file:
        file.write(resource_info.text)

    # Get interface information
    interface_info = api_request("<show><interface>all</interface></show>", "interface_info")
    # Write raw output to a file
    with open(f"logs/{hostname}_interface_info.xml", "w") as file:
        file.write(interface_info.text)

    # Get HA status
    ha_info = api_request("<show><high-availability><state></state></high-availability></show>", "ha_info")
    # Write raw output to a file
    with open(f"logs/{hostname}_ha_info.xml", "w") as file:
        file.write(ha_info.text)

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
    if 'system_info' in info and info['system_info'] is not None:
        system_info = info['system_info']
        data.update({
            'Hostname': system_info.find('.//hostname').text,
            'IP Address': system_info.find('.//ip-address').text,
            'Uptime': system_info.find('.//uptime').text,
            'Model': system_info.find('.//model').text,
            'Version': system_info.find('.//sw-version').text
        })

    # Extract license information
    if 'license_info' in info and info['license_info'] is not None:
        licenses = info['license_info'].findall('.//entry')
        data['Licenses'] = [license.find('feature').text for license in licenses]

    # Extract resource utilization
    if 'resource_info' in info and info['resource_info'] is not None:
        resource_info = info['resource_info'].find('.//result').text.splitlines()
        # Parse load averages
        load_line = resource_info[0]
        load_averages = [float(avg.replace(',', '')) for avg in load_line.split()[-3:]]
        data['Load Averages'] = load_averages

        # Parse CPU usage
        cpu_line = next(line for line in resource_info if line.startswith("%Cpu"))
        with open("logs/cpu_debug.log", "a") as log_file:  # Log to file
            log_file.write(f"CPU Line: {cpu_line}\n")
        cpu_values = cpu_line.split()
        cpu_idle = float(cpu_values[7].replace("id,", ""))  # Ensure correct index
        with open("logs/cpu_debug.log", "a") as log_file:  # Log to file
            log_file.write(f"Parsed CPU Values: {cpu_values}\n")
            log_file.write(f"CPU Idle: {cpu_idle}\n")
        data['CPU Usage'] = 100 - cpu_idle
        with open("logs/cpu_debug.log", "a") as log_file:  # Log to file
            log_file.write(f"CPU Usage: {data['CPU Usage']}\n")

        # Parse memory usage
        mem_line = next(line for line in resource_info if line.startswith("MiB Mem"))
        mem_values = mem_line.split()
        total_mem = float(mem_values[3])
        used_mem = float(mem_values[7])
        free_mem = total_mem - used_mem
        data['Memory'] = {'Total': total_mem, 'Used': used_mem, 'Free': free_mem}

    # Extract interface information
    if 'interface_info' in info and info['interface_info'] is not None:
        interfaces = info['interface_info'].findall('.//entry')
        data['Interfaces'] = [{'Name': iface.find('name').text, 'IP': iface.find('ip').text, 'Status': iface.find('status').text} for iface in interfaces]

    # Extract HA status
    if 'ha_info' in info and info['ha_info'] is not None:
        ha_info = info['ha_info']
        data['HA Status'] = ha_info.find('.//state').text

    return data

# Streamlit app
def main():
    st.set_page_config(layout="wide")  # Set layout to wide for better alignment
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
            # Select refresh interval
            refresh_interval = st.selectbox("Select refresh interval (seconds):", [10, 30, 60, 120, 300], index=2)

            # Create placeholders for dynamic content
            table_placeholder = st.empty()
            load_chart_placeholder = st.empty()
            cpu_chart_placeholder = st.empty()
            memory_chart_placeholder = st.empty()
            # Set up dynamic updates for resource info
            while True:
                # Re-query resource info
                lak_resource_info = get_system_info('l17panorama', api_key)['resource_info']
                atl_resource_info = get_system_info('a46panorama', api_key)['resource_info']

                # Extract and display updated resource info
                lak_resource_data = extract_info({'resource_info': lak_resource_info})
                atl_resource_data = extract_info({'resource_info': atl_resource_info})

                # Update the table with new data
                table_placeholder.table([lak_resource_data, atl_resource_data])

                # Update load average graph
                load_chart_placeholder.line_chart([lak_resource_data['Load Averages'][0], atl_resource_data['Load Averages'][0]])

                # Update CPU usage graph
                cpu_chart_placeholder.line_chart([lak_resource_data['CPU Usage'], atl_resource_data['CPU Usage']])

                # Update memory usage pie chart
                fig, ax = plt.subplots(figsize=(4, 4))  # Smaller figure size
                ax.pie([lak_resource_data['Memory']['Used'], lak_resource_data['Memory']['Free']],
                       labels=['Used', 'Free'], autopct='%1.1f%%')
                memory_chart_placeholder.pyplot(fig)

                # Wait for the selected interval before updating
                time.sleep(refresh_interval)
        else:
            st.error("Failed to retrieve system information.")

if __name__ == "__main__":

    main()




