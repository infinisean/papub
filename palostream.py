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
    if system_info is not None: 
        # Write raw output to a file
        with open(f"logs/{hostname}_system_info.xml", "w") as file:
            file.write(ET.tostring(system_info, encoding='unicode'))
    else:
        print(f"Failed to retrieve system info for {hostname}")

    # Get license information
    license_info = api_request("<request><license><info></info></license></request>", "license_info")
    if license_info is not None:
        # Write raw output to a file
        with open(f"logs/{hostname}_license_info.xml", "w") as file:
            file.write(ET.tostring(license_info, encoding='unicode'))
    else:
        print(f"Failed to retrieve license info for {hostname}")

    # Get resource utilization
    resource_info = api_request("<show><system><resources></resources></system></show>", "resource_info")
    if resource_info is not None:
        # Write raw output to a file
        with open(f"logs/{hostname}_resource_info.xml", "w") as file:
            file.write(ET.tostring(resource_info, encoding='unicode'))
    else:
        print(f"Failed to retrieve resource info for {hostname}")

    # Get interface information
    interface_info = api_request("<show><interface>all</interface></show>", "interface_info")
    if interface_info is not None:
        # Write raw output to a file
        with open(f"logs/{hostname}_interface_info.xml", "w") as file:
            file.write(ET.tostring(interface_info, encoding='unicode'))
    else:
        print(f"Failed to retrieve interface info for {hostname}")

    # Get HA status
    ha_info = api_request("<show><high-availability><state></state></high-availability></show>", "ha_info")
    if ha_info is not None:
        # Write raw output to a file
        with open(f"logs/{hostname}_ha_info.xml", "w") as file:
            file.write(ET.tostring(ha_info, encoding='unicode'))
    else:
        print(f"Failed to retrieve HA info for {hostname}")

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
    st.title("This... is... Sean's Palo Alto Recon Tool AAAAAnd...   <br/>more to come soon")

    # Check for the existence of the "testingkey" file
    api_key = None
    if os.path.exists("testingkey"):
        with open("testingkey", "r") as file:
            api_key = file.read().strip()
        st.info("Using API key from 'testingkey' file.")

    if api_key:
        # Get system info for both Panorama instances
        lak_info = get_system_info('l17panorama', api_key)
        atl_info = get_system_info('a46panorama', api_key)

        if lak_info and atl_info:
            # Select refresh interval
            refresh_interval = st.selectbox("Select refresh interval (seconds):", [10, 30, 60, 120, 300], index=2)

            # Select timespan for graphs
            timespan_options = {
                "5 minutes": 5 * 60,
                "30 minutes": 30 * 60,
                "1 hour": 60 * 60,
                "12 hours": 12 * 60 * 60,
                "24 hours": 24 * 60 * 60,
                "7 days": 7 * 24 * 60 * 60
            }
            timespan = st.selectbox("Select timespan for graphs:", list(timespan_options.keys()), index=0)
            timespan_seconds = timespan_options[timespan]

            # Initialize lists to store historical data
            lak_load_history = []
            atl_load_history = []
            lak_cpu_history = []
            atl_cpu_history = []
            lak_memory_history = []
            atl_memory_history = []

            # Organize graphs into columns
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("LAK Load Averages")
                lak_load_chart_placeholder = st.empty()

                st.subheader("LAK CPU Usage")
                lak_cpu_chart_placeholder = st.empty()

                st.subheader("LAK Memory Usage")
                lak_memory_chart_placeholder = st.empty()

            with col2:
                st.subheader("ATL Load Averages")
                atl_load_chart_placeholder = st.empty()

                st.subheader("ATL CPU Usage")
                atl_cpu_chart_placeholder = st.empty()

                st.subheader("ATL Memory Usage")
                atl_memory_chart_placeholder = st.empty()

            # Create placeholder for the table
            table_placeholder = st.empty()

            # Set up dynamic updates for resource info
            while True:
                # Re-query resource info
                lak_resource_info = get_system_info('l17panorama', api_key)['resource_info']
                atl_resource_info = get_system_info('a46panorama', api_key)['resource_info']

                # Extract and display updated resource info
                lak_resource_data = extract_info({'resource_info': lak_resource_info})
                atl_resource_data = extract_info({'resource_info': atl_resource_info})

                # Append new data to history
                lak_load_history.append(lak_resource_data['Load Averages'])
                atl_load_history.append(atl_resource_data['Load Averages'])
                lak_cpu_history.append(lak_resource_data['CPU Usage'])
                atl_cpu_history.append(atl_resource_data['CPU Usage'])
                lak_memory_history.append(lak_resource_data['Memory'])
                atl_memory_history.append(atl_resource_data['Memory'])

                # Trim history to match the selected timespan
                max_points = timespan_seconds // refresh_interval
                lak_load_history = lak_load_history[-max_points:]
                atl_load_history = atl_load_history[-max_points:]
                lak_cpu_history = lak_cpu_history[-max_points:]
                atl_cpu_history = atl_cpu_history[-max_points:]
                lak_memory_history = lak_memory_history[-max_points:]
                atl_memory_history = atl_memory_history[-max_points:]

                # Update load average graph for LAK
                lak_load_chart_placeholder.line_chart({
                    '1 min': [load[0] for load in lak_load_history],
                    '5 min': [load[1] for load in lak_load_history],
                    '15 min': [load[2] for load in lak_load_history]
                })

                # Update CPU usage graph for LAK
                lak_cpu_chart_placeholder.line_chart(lak_cpu_history)

                # Update memory usage graph for LAK
                fig_lak_mem, ax_lak_mem = plt.subplots(figsize=(5, 3))
                ax_lak_mem.fill_between(range(len(lak_memory_history)),
                                        [mem['Used'] for mem in lak_memory_history],
                                        label='Used', color='red', alpha=0.5)
                ax_lak_mem.fill_between(range(len(lak_memory_history)),
                                        [mem['Total'] for mem in lak_memory_history],
                                        [mem['Used'] for mem in lak_memory_history],
                                        label='Free', color='green', alpha=0.5)
                ax_lak_mem.set_ylim(0, max(mem['Total'] for mem in lak_memory_history))
                ax_lak_mem.legend()
                lak_memory_chart_placeholder.pyplot(fig_lak_mem)

                # Update load average graph for ATL
                atl_load_chart_placeholder.line_chart({
                    '1 min': [load[0] for load in atl_load_history],
                    '5 min': [load[1] for load in atl_load_history],
                    '15 min': [load[2] for load in atl_load_history]
                })

                # Update CPU usage graph for ATL
                atl_cpu_chart_placeholder.line_chart(atl_cpu_history)

                # Update memory usage graph for ATL
                fig_atl_mem, ax_atl_mem = plt.subplots(figsize=(5, 3))
                ax_atl_mem.fill_between(range(len(atl_memory_history)),
                                        [mem['Used'] for mem in atl_memory_history],
                                        label='Used', color='red', alpha=0.5)
                ax_atl_mem.fill_between(range(len(atl_memory_history)),
                                        [mem['Total'] for mem in atl_memory_history],
                                        [mem['Used'] for mem in atl_memory_history],
                                        label='Free', color='green', alpha=0.5)
                ax_atl_mem.set_ylim(0, max(mem['Total'] for mem in atl_memory_history))
                ax_atl_mem.legend()
                atl_memory_chart_placeholder.pyplot(fig_atl_mem)

                # Update the table with new data
                table_placeholder.table([lak_resource_data, atl_resource_data])

                # Wait for the selected interval before updating
                time.sleep(refresh_interval)
        else:
            st.error("Failed to retrieve system information.")

if __name__ == "__main__":
    main()




