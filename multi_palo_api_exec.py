#!/usr/bin/python3
import os
import sys
import requests
from colorama import init, Fore, Style
import urllib3

# Suppress only the single InsecureRequestWarning from urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def palo_get_api_key(host, user, password):
    url = f"https://{host}/api/?type=keygen&user={user}&password={password}"
    try:
        response = requests.get(url, verify=False, timeout=15)
        response.raise_for_status()
        contents = response.text
        if contents:
            raw = contents.split("key>")
            key = raw[1].split("<")[0].strip()
            return key
        else:
            return "AuthFail"
    except requests.RequestException as e:
        print(f"Error: {e}")
        return "AuthFail"

def construct_xml_command(command):
    # Split the command into words
    command_words = command.split()
    if not command_words:
        return ""

    # Determine if the last word is a value modifier
    last_word = command_words[-1]
    last_is_val = any(char in last_word for char in ['-', '.', 'all'])

    # Construct the XML command
    xml_cmd = ""
    for word in command_words[:-1] if last_is_val else command_words:
        xml_cmd += f"<{word}>"
    
    if last_is_val:
        xml_cmd += last_word

    for word in reversed(command_words[:-1] if last_is_val else command_words):
        xml_cmd += f"</{word}>"

    return xml_cmd

def do_api_query(host, key, cmd, verbose):
    xml_cmd = construct_xml_command(cmd)
    url = f"https://{host}/api/?type=op&cmd={xml_cmd}"
    headers = {"X-PAN-KEY": key}
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        curl_out = response.text.strip()

        # Create logs directory and hostname subdirectory
        logs_dir = "logs"
        host_dir = os.path.join(logs_dir, host)
        os.makedirs(host_dir, exist_ok=True)

        # Sanitize the command to create a valid filename
        sanitized_cmd = cmd.replace(" ", "_")
        log_file_path = os.path.join(host_dir, f"{sanitized_cmd}.txt")

        # Log the full raw output to a file
        with open(log_file_path, "w") as log_file:
            log_file.write(f"CMD: {url}\n")
            log_file.write(curl_out + "\n\n")

        if verbose:
            print(f"\n\nCMD: {url}\n")

        # Extract and print the result if the status is success
        if 'status="success"' in curl_out:
            start = curl_out.find("<result>") + len("<result>")
            end = curl_out.find("</result>")
            result = curl_out[start:end].strip()
            print(f"{Fore.GREEN}{result}{Style.RESET_ALL}")
        elif 'status="error"' in curl_out:
            start = curl_out.find("<msg>") + len("<msg>")
            end = curl_out.find("</msg>")
            error_msg = curl_out[start:end].strip()
            print(f"{Fore.YELLOW}{error_msg}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}{curl_out}{Style.RESET_ALL}")
    except requests.RequestException as e:
        print(f"Error: {e}")

def read_creds():
    try:
        with open('.creds', 'r') as creds_file:
            user = creds_file.readline().strip()
            password = creds_file.readline().strip()
            if not user or not password:
                raise ValueError("Credentials file must contain both a username and a password.")
            return user, password
    except (FileNotFoundError, ValueError) as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        sys.exit(1)

def read_api_cmds(filename):
    try:
        with open(filename, 'r') as file:
            commands = file.readlines()
        return [command.strip() for command in commands if command.strip()]
    except FileNotFoundError:
        print(f"{Fore.RED}Error: File {filename} not found.{Style.RESET_ALL}")
        sys.exit(1)

def main():
    init(autoreset=True)  # Initialize colorama

    if len(sys.argv) < 4 or "-f" not in sys.argv:
        print(f"Syntax: {sys.argv[0]} [-v] -f filename hostname\n\n")
        sys.exit(1)

    verbose = "-v" in sys.argv
    file_index = sys.argv.index("-f") + 1

    if file_index >= len(sys.argv) - 1:
        print("Error: Filename and hostname must follow the -f option.")
        sys.exit(1)

    filename = sys.argv[file_index]
    fwname = sys.argv[file_index + 1].strip()

    user, password = read_creds()
    key = palo_get_api_key(fwname, user, password)
    commands = read_api_cmds(filename)

    for command in commands:
        do_api_query(fwname, key, command, verbose)

if __name__ == "__main__":
    main()