import streamlit as st
import time
import os
import subprocess
from palo_api_metrics import query_firewall_data

def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read().strip()

def ping_host(hostname):
    try:
        # Execute the ping command
        result = subprocess.run(
            ["ping", "-c", "20", "-i", "0.05", "-w", ".05", hostname], stdout=subprocess.PIPE
            #capture_output=True,
            #text=True
        )
        print(result.stdout)
        # Return the output of the ping command
        return result.stdout
    except Exception as e:
        return f"Error pinging host: {str(e)}"

def main():
    st.set_page_config(layout="wide")
    st.title("Palo Alto Network Monitoring Tool")

    # Construct file paths for the API key and credentials
    base_dir = os.path.dirname(os.path.dirname(__file__))  # One directory level up
    pankey_path = os.path.join(base_dir, 'pankey')
    pacreds_path = os.path.join(base_dir, 'pacreds')

    # Sidebar navigation
    st.sidebar.title("Navigation")
    nav_choice = st.sidebar.radio("Choose a tool:", ["Panorama Tools", "Palo FW Tools"])

    if nav_choice == "Palo FW Tools":
        store_number = st.sidebar.text_input("Enter Store Number (1-3000):", "")
        
        if store_number.isdigit() and 1 <= int(store_number) <= 3000:
            hostname = f"S{int(store_number):04d}MLANF01"
            st.sidebar.success(f"Hostname: {hostname}")

            # Ping the firewall and display the results
            ping_results = ping_host(hostname)
            st.sidebar.text_area("Ping Results", ping_results, height=200)

            # Call the data gathering function
            try:
                query_firewall_data(store_number)
            except Exception as e:
                st.error(f"Error gathering data: {str(e)}")
                return

            # Tabs for different outputs
            tab1, tab2 = st.tabs(["Firewall Health", "ARP Table"])

            with tab1:
                st.write("Loading firewall health data...")
                # Periodically read and display data from the files
                #while True:
                    # Implement logic to read and display data from the files
                time.sleep(30)

            with tab2:
                st.write("Loading ARP table data...")
                # Periodically read and display data from the files
                #while True:
                    # Implement logic to read and display data from the files
                time.sleep(30)
                # Implement logic to read and display ARP table data
                #while True:
                    # Implement logic to read and display data from the files
                #time.sleep(30)

        else:
            st.sidebar.error("Please enter a valid store number between 1 and 3000.")

if __name__ == "__main__":
    main()