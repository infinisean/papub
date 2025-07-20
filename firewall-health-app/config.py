"""
Configuration settings for the Firewall Health Metrics Comparison App
"""
import os
from pathlib import Path

# Directory structure configuration
OUTPUT_DIR = Path("../output")  # Relative to the firewall-health-app directory
DEFAULT_OUTPUT_DIR = Path(os.path.dirname(__file__)).parent / "output"

# File naming patterns
PRE_PATTERN = "-pre-"
POST_PATTERN = "-post-"

# Timestamp patterns for parsing
TIMESTAMP_PATTERN = r"\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}"

# UI configuration
APP_TITLE = "Firewall Health Metrics Comparison"
APP_DESCRIPTION = "Compare pre and post-change firewall health metrics to ensure changes don't negatively impact firewall operations."

# Color coding for results
COLORS = {
    "success": "#28a745",  # Green
    "warning": "#ffc107",  # Yellow  
    "error": "#dc3545",    # Red
    "info": "#17a2b8"      # Blue
}

# Status icons
ICONS = {
    "success": "✅",
    "warning": "⚠️", 
    "error": "❌",
    "info": "ℹ️"
}

# Supported command types and their display names
SUPPORTED_COMMANDS = {
    "show_arp_all": "ARP Table",
    "show_session_all": "Session Table",
    "show_session_all_filter_count_yes": "Session Count"
}