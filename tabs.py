import streamlit as st
from streamlit.web import cli as stcli

tab1, tab2, tab3 = st.tabs(["Tab 1", "Tab 2", "Tab 3"])

with tab1:
    st.header("Tab 1")
    st.write("Content of Tab 1")
    st.line_chart({"data": [1, 5, 2, 6, 2, 1]})

with tab2:
    st.header("Tab 2")
    st.write("Content of Tab 2")
    st.bar_chart({"data": [1, 5, 2, 6, 2, 1]})

with tab3:
    st.header("Tab 3")
    st.write("Content of Tab 3")
    st.area_chart({"data": [1, 5, 2, 6, 2, 1]})