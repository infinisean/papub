import streamlit as st
import functions

def display_pan_health():
    st.header("Panorama Health")
    pan_api_key = read_api_key()
    query_type = "op"
    command = "<show><system><resources></resources></system></show>"
    # Define the Panorama instances
    panorama_instances = ['A46PANORAMA', 'L17PANORAMA']  # Replace with actual Panorama hostnames

    # Query health data for each Panorama instance
    health_data = {}
    for panorama_host in panorama_instances:
        #health_data[panorama_host] = query_firewall_data(panorama, live_db=False)
        health_data[panorama_host] = send_api_query(panorama_host, pan_api_key, query_type, command)

    # Display the health data in a structured format
    metrics = ["Uptime", "1 Min Load", "CPU Usage", "Memory Used", "Memory Free"]
    st.write("### Panorama Health Metrics")
    for metric in metrics:
        col1, col2, col3 = st.columns(3)
        col1.write(f"**{metric}**")
        for i, panorama in enumerate(panorama_instances):
            if health_data[panorama]:
                col = col2 if i == 0 else col3
                col.write(health_data[panorama].get(metric.lower().replace(" ", "_"), "N/A"))