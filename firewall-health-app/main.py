"""
Firewall Health Metrics Comparison App

A Streamlit application that compares pre and post-change firewall health metrics
to ensure changes don't negatively impact firewall operations.
"""
import streamlit as st
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Import configuration and comparators
from config import (
    DEFAULT_OUTPUT_DIR, PRE_PATTERN, POST_PATTERN, TIMESTAMP_PATTERN,
    APP_TITLE, APP_DESCRIPTION, COLORS, ICONS, SUPPORTED_COMMANDS
)
from comparators.base import ComparisonStatus
from comparators.arp_table import ArpTableComparator
from comparators.sessions import SessionsComparator, SessionCountComparator

# Initialize comparators
COMPARATORS = {
    "show_arp_all": ArpTableComparator(),
    "show_session_all": SessionsComparator(),
    "show_session_all_filter_count_yes": SessionCountComparator()
}

def get_available_firewalls(output_dir: Path) -> List[str]:
    """Get list of available firewall hostnames from subdirectories"""
    if not output_dir.exists():
        return []
    
    firewalls = []
    for item in output_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            firewalls.append(item.name)
    
    return sorted(firewalls)

def extract_timestamp_from_filename(filename: str) -> Optional[datetime]:
    """Extract timestamp from filename"""
    match = re.search(TIMESTAMP_PATTERN, filename)
    if match:
        timestamp_str = match.group()
        try:
            return datetime.strptime(timestamp_str, "%m-%d-%y-%H-%M-%S")
        except ValueError:
            pass
    return None

def find_file_pairs(firewall_dir: Path) -> Dict[str, Dict[str, str]]:
    """Find pre/post file pairs for each command"""
    files = list(firewall_dir.glob("*.txt"))
    
    # Group files by command
    command_files = {}
    
    for file in files:
        filename = file.name
        
        # Skip error files
        if "ERROR" in filename:
            continue
        
        # Determine command type
        command_type = None
        for cmd_key in SUPPORTED_COMMANDS.keys():
            cmd_pattern = cmd_key.replace("_", "_")
            if cmd_pattern in filename:
                command_type = cmd_key
                break
        
        if not command_type:
            continue
        
        # Determine if pre or post
        context = None
        if PRE_PATTERN in filename:
            context = "pre"
        elif POST_PATTERN in filename:
            context = "post"
        
        if not context:
            continue
        
        # Extract timestamp
        timestamp = extract_timestamp_from_filename(filename)
        
        if command_type not in command_files:
            command_files[command_type] = {"pre": [], "post": []}
        
        command_files[command_type][context].append({
            "file": file,
            "timestamp": timestamp,
            "filename": filename
        })
    
    # Find the most recent pre/post pairs
    file_pairs = {}
    
    for command_type, contexts in command_files.items():
        pre_files = sorted(contexts["pre"], key=lambda x: x["timestamp"] or datetime.min, reverse=True)
        post_files = sorted(contexts["post"], key=lambda x: x["timestamp"] or datetime.min, reverse=True)
        
        if pre_files and post_files:
            file_pairs[command_type] = {
                "pre_file": pre_files[0]["file"],
                "post_file": post_files[0]["file"],
                "pre_timestamp": pre_files[0]["timestamp"],
                "post_timestamp": post_files[0]["timestamp"]
            }
    
    return file_pairs

def format_status_badge(status: ComparisonStatus) -> str:
    """Format status as colored badge"""
    color = COLORS[status.value]
    icon = ICONS[status.value]
    return f'<span style="color: {color}; font-weight: bold;">{icon} {status.value.upper()}</span>'

def display_comparison_result(command_type: str, result, file_info: Dict):
    """Display comparison result with formatting"""
    st.subheader(f"📊 {SUPPORTED_COMMANDS[command_type]}")
    
    # Display status badge
    st.markdown(format_status_badge(result.status), unsafe_allow_html=True)
    
    # Display main message
    st.write(result.message)
    
    # Display file information
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Pre-change:** {file_info['pre_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    with col2:
        st.write(f"**Post-change:** {file_info['post_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Display metrics if available
    if result.metrics:
        with st.expander("📈 Detailed Metrics"):
            for key, value in result.metrics.items():
                st.write(f"**{key.replace('_', ' ').title()}:** {value}")
    
    # Display details if available  
    if result.details:
        with st.expander("🔍 Detailed Analysis"):
            for key, value in result.details.items():
                if isinstance(value, list) and value:
                    st.write(f"**{key.replace('_', ' ').title()}:**")
                    for item in value[:10]:  # Show first 10 items
                        st.write(f"  • {item}")
                    if len(value) > 10:
                        st.write(f"  ... and {len(value) - 10} more")
                elif isinstance(value, dict) and value:
                    st.write(f"**{key.replace('_', ' ').title()}:**")
                    for k, v in value.items():
                        st.write(f"  • {k}: {v}")
                elif value:
                    st.write(f"**{key.replace('_', ' ').title()}:** {value}")
    
    st.markdown("---")

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🔥",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title(f"🔥 {APP_TITLE}")
    st.markdown(APP_DESCRIPTION)
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")
    
    # Output directory selection
    output_dir_str = st.sidebar.text_input(
        "Output Directory", 
        value=str(DEFAULT_OUTPUT_DIR),
        help="Path to the directory containing firewall output files"
    )
    output_dir = Path(output_dir_str)
    
    if not output_dir.exists():
        st.error(f"❌ Output directory does not exist: {output_dir}")
        st.stop()
    
    # Get available firewalls
    firewalls = get_available_firewalls(output_dir)
    
    if not firewalls:
        st.warning(f"⚠️ No firewall directories found in {output_dir}")
        st.info("Make sure you have subdirectories named after firewall hostnames containing the output files.")
        st.stop()
    
    # Firewall selection
    selected_firewall = st.sidebar.selectbox(
        "Select Firewall",
        firewalls,
        help="Choose the firewall hostname to analyze"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 Supported Commands")
    for cmd_key, cmd_name in SUPPORTED_COMMANDS.items():
        st.sidebar.write(f"• {cmd_name}")
    
    # Main content
    if selected_firewall:
        st.header(f"🖥️ Analysis for: {selected_firewall}")
        
        firewall_dir = output_dir / selected_firewall
        file_pairs = find_file_pairs(firewall_dir)
        
        if not file_pairs:
            st.warning("⚠️ No pre/post file pairs found for this firewall.")
            st.info("Make sure you have both pre-change and post-change files with proper naming conventions.")
            return
        
        # Display summary
        st.success(f"✅ Found {len(file_pairs)} command comparisons available")
        
        # Performance summary section
        st.header("📊 Comparison Results")
        
        # Run comparisons
        results = {}
        for command_type, file_info in file_pairs.items():
            if command_type in COMPARATORS:
                comparator = COMPARATORS[command_type]
                result = comparator.compare_files(
                    str(file_info["pre_file"]), 
                    str(file_info["post_file"])
                )
                results[command_type] = (result, file_info)
        
        # Display overall status
        if results:
            error_count = sum(1 for result, _ in results.values() if result.status == ComparisonStatus.ERROR)
            warning_count = sum(1 for result, _ in results.values() if result.status == ComparisonStatus.WARNING)
            success_count = sum(1 for result, _ in results.values() if result.status == ComparisonStatus.SUCCESS)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("✅ Successful", success_count)
            with col2:
                st.metric("⚠️ Warnings", warning_count)
            with col3:
                st.metric("❌ Errors", error_count)
            
            # Display detailed results
            st.markdown("---")
            
            for command_type, (result, file_info) in results.items():
                display_comparison_result(command_type, result, file_info)
        
        else:
            st.warning("⚠️ No comparisons could be performed. Check if the comparators support your command types.")

if __name__ == "__main__":
    main()