import sys
from xml.dom import minidom

def pretty_print_xml(file_path):
    try:
        # Parse the XML file
        with open(file_path, 'r') as file:
            xml_content = file.read()
        
        # Parse the XML content
        dom = minidom.parseString(xml_content)
        
        # Pretty print the XML with indentation
        pretty_xml_as_string = dom.toprettyxml(indent="    ")  # Use 4 spaces for indentation
        
        # Print the pretty XML
        print(pretty_xml_as_string)
    
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python pretty_print_xml.py <path_to_xml_file>")
    else:
        xml_file_path = sys.argv[1]
        pretty_print_xml(xml_file_path)