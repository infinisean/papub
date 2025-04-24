import streamlit as st
from functions import query_firewall_data

def display_pan_health():
    st.header("Panorama Health")

    # Define the Panorama instances
    panorama_instances = ['A46PANORAMA', 'L17PANORAMA']  # Replace with actual Panorama hostnames

    # Query health data for each Panorama instance
    health_data = {}
    for panorama in panorama_instances:
        health_data[panorama] = query_firewall_data(panorama, live_db=False)

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