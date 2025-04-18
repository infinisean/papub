import streamlit as st
import time
import os
from palo_api_metrics import query_firewall_data, get_pan_connected_devices
from icmplib import ping
import pandas as pd

@st.cache_data
def load_devices():
    # Retrieve devices from Panorama
    panorama_instances = ['a46panorama', 'l17panorama']  # Replace with actual Panorama hostnames
    all_devices = []
    for panorama in panorama_instances:
        devices = get_pan_connected_devices(panorama)
        all_devices.extend(devices)

    # Sort and remove duplicates based on hostname
    unique_devices = {device['hostname']: device for device in all_devices}.values()
    sorted_devices = sorted(unique_devices, key=lambda x: x['hostname'])
    return sorted_devices

def ping_host(host, count=10, interval=0.1):
    output = []
    try:
        result = ping(host, count=count, interval=interval)

        output.append(f"Pinging {host}:")
        output.append(f"Packets sent: {result.packets_sent}")
        
        if result.packets_received > 0:
            output.append(f"{result.packets_received}/{result.packets_sent} packets received, {result.packet_loss * 100:.1f}% packet loss")
            if result.packets_received > 0:
                output.append("RTT min/avg/max:")
                output.append(f"{result.min_rtt:.3f}/{result.avg_rtt:.3f}/{result.max_rtt:.3f} ms")
        else:
            output.append(f"{host} didn't reply.")
    except Exception as e:
        output.append(f"An error occurred: {e}")

    return "\n".join(output)

def show_devices(devices):
    st.title("Connected Devices")

    # Convert to DataFrame for display
    df = pd.DataFrame(devices)

    # Check if the 'model' column exists
    if 'model' not in df.columns:
        st.error("The 'model' column is missing from the data.")
        return

    # Create search boxes and selector
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        hostname_search = st.text_input("Search Hostname")
    with col2:
        model_options = df['model'].unique()
        model_filter = st.selectbox("Filter by Model", options=["All"] + list(model_options))
    with col3:
        serial_search = st.text_input("Search Serial")
    with col4:
        ip_search = st.text_input("Search IP")

    # Filter the DataFrame based on search inputs
    if hostname_search:
        df = df[df['hostname'].str.contains(hostname_search, case=False, na=False)]
    if serial_search:
        df = df[df['serial'].str.contains(serial_search, case=False, na=False)]
    if ip_search:
        df = df[df['mgmt_ip'].str.contains(ip_search, case=False, na=False)]
    if model_filter != "All":
        df = df[df['model'] == model_filter]

    # Display the filtered DataFrame
    st.dataframe(df)

def main():
    st.set_page_config(layout="wide")
    st.title("Palo Alto Network Monitoring Tool")

    # Load and cache devices data
    devices = load_devices()

    # Sidebar navigation
    st.sidebar.title("Navigation")
    nav_choice = st.sidebar.radio("Choose a tool:", ["Select", "Panorama Tools", "Palo FW Tools"], index=0)

    if nav_choice == "Panorama Tools":
        st.sidebar.subheader("Panorama Tools")
        if st.sidebar.button("Show Devices"):
            show_devices(devices)

    elif nav_choice == "Palo FW Tools":
        st.sidebar.subheader("Palo FW Tools")

        # Create a list of all possible search terms
        search_terms = [device['hostname'] for device in devices] + \
                       [device['serial'] for device in devices] + \
                       [device['mgmt_ip'] for device in devices]

        # Autocomplete text input for selecting a device
        selected_device = st.sidebar.text_input("Search and select a device:", "")
        matching_devices = [term for term in search_terms if selected_device.lower() in term.lower()]

        if matching_devices:
            selected_device = st.sidebar.selectbox("Matching Devices", matching_devices)

        if selected_device:
            # Find the selected device details
            device_info = next((device for device in devices if selected_device in device.values()), None)
            if device_info:
                hostname = device_info['hostname']
                st.sidebar.success(f"Selected Hostname: {hostname}")

                # Ping the firewall and display the results
                ping_results = ping_host(hostname)
                st.sidebar.text_area("Ping Results", ping_results, height=200)

                # Call the data gathering function with live_db set to False
                try:
                    query_firewall_data(hostname, live_db=False)
                except Exception as e:
                    st.error(f"Error gathering data: {str(e)}")
                    return

                # Expanders for different outputs
                with st.expander("Firewall Health"):
                    st.write("Loading firewall health data...")
                    # Implement logic to read and display data from the files
                    time.sleep(30)

                with st.expander("ARP Table"):
                    st.write("Loading ARP table data...")
                    # Implement logic to read and display ARP table data
                    time.sleep(30)

if __name__ == "__main__":
    main()