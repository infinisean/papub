import streamlit as st
import pan_ha_state
import pan_health
from streamlit_option_menu import option_menu
from functions import get_primary_pan  # Ensure this import is correct based on your project structure
from functions import setup_logging

setup_logging(debug_mode=True)


def main():
    st.set_page_config(page_title="Publix Network Monitoring", layout="wide")

    # Get the primary Panorama instance
    panorama_instances = ['A46PANORAMA', 'L17PANORAMA']  
    primary_pan = get_primary_pan(panorama_instances)
    if primary_pan:
        st.sidebar.success(f"Primary Panorama: {primary_pan}")
    else:
        st.sidebar.error("No primary Panorama instance found.")

    # Sidebar navigation
    with st.sidebar:
        selected = option_menu(
            "Navigation",
            ["Panorama", "Palo Alto"],
            icons=["diagram-3", "shield-lock"],
            menu_icon="cast",
            default_index=0,
        )

    # Main content
    if selected == "Panorama":
        st.title("Panorama Dashboard")
        PANtabs = st.tabs(["HA State", "Panorama Health", "Connected Devices"])

        with PANtabs[0]:
            #st.header("Panorama High-Availability State")
            pan_ha_state.display_ha_state()

        with PANtabs[1]:
            pan_health.display_pan_health()

        with PANtabs[2]:
            st.header("Connected Devices")
            st.write("Connected devices information goes here. Click on a device to view details.")

    elif selected == "Palo Alto":
        st.title("Palo Alto Dashboard")
        PAtabs = st.tabs(["Palo Device Overview", "Palo Tool1", "Palo Tool2"])
        
        with PAtabs[0]:
            st.header("Palo Device Overview")
            # Import and execute the palo_device_overview module
            import palo_device_overview
            palo_device_overview.display_device_overview()
            
        with PAtabs[1]:
            st.header("Palo ARP Tables")
            st.write("Palo ARP tables information goes here.")
            
        with PAtabs[2]:
            st.header("Palo Tool2")
            st.write("Palo tool2 information goes here.")

if __name__ == "__main__":
    main()