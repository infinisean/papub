import sys, os
sys.path.append('/home/netmonitor/palostream')
import streamlit as st
from streamlit_option_menu import option_menu
#from streamlit_keyup import st_keyup
from pan_functions import xml_logger, main_logger, read_file, get_db_credentials, palo_gen_api_key, read_pan_api_key 
from pan_functions import send_api_query, get_pan_connected_devices, parse_system_resources, get_active_pan
from pan_functions import get_pan_devices, parse_element_to_dict, get_pan_ha_state, display_ha_state, display_pan_devices


#import pan_ha_state
#import pan_health
#from pan_devices import get_pan_devices  # Import the get_pan_devices function
print("Current working directory:", os.getcwd())
print("Python path:", sys.path)

from logging_setup import xml_logger, main_logger

# Use the loggers in your code
xml_logger.debug("This is a test log message for XML processing.")
main_logger.debug("This is a test log message for main processing.")

def main():
    st.set_page_config(page_title="Publix Network Monitoring", layout="wide")

    # Get the primary Panorama instance
    panorama_instances = ['A46PANORAMA', 'L17PANORAMA']  # Replace with actual Panorama hostnames
    active_pan = get_active_pan(panorama_instances)
    if active_pan:
        st.sidebar.success(f"Active  :   {active_pan}")
    else:
        st.sidebar.error("No primary Pan found.")
        exit()
    # Sidebar navigation
    with st.sidebar:
        selected = option_menu(
            "Navigation",
            ["Panorama", "Firewalls"],
            icons=["diagram-3", "shield-lock"],
            menu_icon="cast",
            default_index=0,
        )

    # Main content
    if selected == "Panorama":
        st.title("Panorama")
        PANtabs = st.tabs(["H.A. Status", "Health", "Connected Devices"])

        with PANtabs[0]:
            st.header("H.A. Status")
            if active_pan:
                display_ha_state(active_pan)

        with PANtabs[1]:
            st.header("Health")
            #pan_health.display_pan_health()

        with PANtabs[2]:
            #st.header("Connected Devices")
            pan_devices = get_pan_devices(active_pan) # Call the get_pan_devices function with the primary Panorama instance
            display_pan_devices(pan_devices)  # Call the display_pan_connected_devices function with the primary Panorama instance

    elif selected == "Firewalls":
        st.title("Firewalls")
        PAtabs = st.tabs(["Overview", "Health", "ARP Table"])
        
        with PAtabs[0]:
            st.header("Overview")
            # Import and execute the palo_device_overview module
            #import palo_device_overview
            #palo_device_overview.display_device_overview()
            
        with PAtabs[1]:
            st.header("Health")
            st.write("Palo Health information goes here.")
            
        with PAtabs[2]:
            st.header("ARP Table")
            st.write("Palo ARP information goes here.")

if __name__ == "__main__":
    main()