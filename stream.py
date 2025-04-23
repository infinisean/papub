import streamlit as st
from streamlit_option_menu import option_menu

def main():
    st.set_page_config(page_title="Network Monitoring", layout="wide")

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
        tabs = st.tabs(["HA State", "Other Tab 1", "Other Tab 2"])

        with tabs[0]:
            st.header("Panorama High-Availability State")
            # Import and execute the ha_state module
            import ha_state
            ha_state.display_ha_state()

        with tabs[1]:
            st.header("Other Tab 1")
            st.write("Content for other tab 1.")

        with tabs[2]:
            st.header("Other Tab 2")
            st.write("Content for other tab 2.")

    elif selected == "Palo Alto":
        st.title("Palo Alto Dashboard")
        st.write("Content for Palo Alto.")

if __name__ == "__main__":
    main()