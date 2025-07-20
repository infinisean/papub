# Firewall Health Metrics Comparison App

A Streamlit web application that compares pre and post-change firewall health metrics to ensure changes don't negatively impact firewall operations.

![Firewall Health App Screenshot](https://github.com/user-attachments/assets/d91920cf-4863-47ff-8d6f-a801a9b4a2fe)

## Features

### Core Functionality
- **Automatic File Discovery**: Scans output directory for firewall subdirectories and identifies pre/post file pairs
- **Intuitive Web Interface**: Clean Streamlit UI for operations teams
- **Color-Coded Results**: Green (success), yellow (warning), red (error) status indicators
- **Detailed Analysis**: Expandable sections showing metrics and detailed changes

### Supported Comparisons
1. **ARP Table Analysis** (`show arp all`):
   - Compares number of active ARP entries
   - Identifies missing/new IP addresses
   - Flags significant drops in MAC addresses
   - Example: "ARP table unchanged ✅" or "IPs 192.168.1.15 no longer responding ❌"

2. **Session Analysis** (`show session all`):
   - Compares active session counts
   - Monitors session state changes
   - Detects significant connection drops or increases

3. **Session Count** (`show session all filter count yes`):
   - Simple session count comparison
   - Percentage change calculation
   - Threshold-based alerting

### Extensible Framework
- Modular comparator design for easy addition of new command types
- Standardized result format with status and detailed metrics
- Base comparator class for consistent implementation

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup
```bash
cd firewall-health-app
pip install -r requirements.txt
```

### Dependencies
- streamlit >= 1.28.0
- pandas >= 1.5.0
- pathlib
- colorama >= 0.4.6

## Usage

### Running the Application
```bash
streamlit run main.py
```

The application will start on http://localhost:8501

### Directory Structure
The app expects the following directory structure:
```
output/
├── firewall1/
│   ├── show_arp_all-pre-12-20-24-10-30-15.txt
│   ├── show_arp_all-post-12-20-24-11-30-15.txt
│   ├── show_session_all-pre-12-20-24-10-30-15.txt
│   └── show_session_all-post-12-20-24-11-30-15.txt
├── firewall2/
│   └── ...
```

### File Naming Convention
Files must follow this pattern:
- `{command}-{context}-{timestamp}.txt`
- `context`: "pre" or "post"
- `timestamp`: MM-DD-YY-HH-MM-SS format

### Using the Interface
1. **Select Output Directory**: Configure the path to your firewall output files
2. **Choose Firewall**: Select from available firewall hostnames
3. **View Results**: Review color-coded comparison results
4. **Expand Details**: Click on metrics and analysis sections for detailed information

## Configuration

Edit `config.py` to customize:
- Output directory paths
- File naming patterns
- Color schemes
- Supported command types

## Architecture

### Directory Structure
```
firewall-health-app/
├── main.py                 # Main Streamlit application
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
└── comparators/
    ├── __init__.py
    ├── base.py            # Base comparator class
    ├── arp_table.py       # ARP table comparator
    ├── sessions.py        # Sessions comparator
    └── utils.py           # Common parsing utilities
```

### Adding New Comparators

1. Create a new comparator class inheriting from `BaseComparator`:
```python
from .base import BaseComparator, ComparisonResult, ComparisonStatus

class MyComparator(BaseComparator):
    def __init__(self):
        super().__init__("my_command")
    
    def parse_output(self, output: str) -> Dict[str, Any]:
        # Parse command output
        return parsed_data
    
    def compare(self, pre_data: Dict, post_data: Dict) -> ComparisonResult:
        # Compare data and return result
        return ComparisonResult(status=status, message=message)
```

2. Add to `COMPARATORS` dict in `main.py`
3. Add to `SUPPORTED_COMMANDS` in `config.py`

## Error Handling

The application handles various error conditions gracefully:
- Missing files or directories
- Corrupted data
- Parsing errors
- Timestamp extraction failures

Errors are displayed with clear messages and don't crash the application.

## Integration

This app integrates with existing firewall health collection scripts:
- `palo_pre_post_health_comparison.py` (paramiko-based)
- `phc.py` (netmiko-based)

Both scripts create the expected output directory structure automatically.

## Screenshots

### Main Interface
![Main View](https://github.com/user-attachments/assets/d91920cf-4863-47ff-8d6f-a801a9b4a2fe)

### Detailed Analysis
![Detailed View](https://github.com/user-attachments/assets/36eb37b6-f3cc-4e42-b97f-0fd84cf8e683)

## Status Indicators

- ✅ **Success**: No significant changes detected
- ⚠️ **Warning**: Changes detected but within acceptable thresholds
- ❌ **Error**: Significant issues detected that require attention
- ℹ️ **Info**: Informational messages

## Contributing

To add support for new firewall commands:
1. Study the existing comparators for patterns
2. Implement the required `parse_output()` and `compare()` methods
3. Add appropriate test data
4. Update configuration and documentation