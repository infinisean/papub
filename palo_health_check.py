#!/usr/bin/python3
import os
import sys
import paramiko
from datetime import datetime, timedelta
from colorama import init, Fore, Style

# Predefined status commands
STATUS_COMMANDS = [
    "show clock",
    "show lacp aggregate-ethernet all",
    "show interface all",
    "show high-availability state",
    "show log system receive_time in last-24-hrs",
    "show system info",
    "show running resource-monitor hour last 24",
    "show running resource-monitor day last 7",
    "show lldp neighbors all",
    "show arp all",
    "show routing route",
    "show routing protocol bgp summary",
    "show routing protocol bgp peer",
    "show routing protocol bgp loc-rib",
    "show routing protocol bgp rib-out",
    "show session all filter count yes",
    "show session all"
]

def read_creds():
    try:
        with open('.creds', 'r') as creds_file:
            user = creds_file.readline().strip()
            password = creds_file.readline().strip()
            if not user or not password:
                raise ValueError("Credentials file must contain both a username and a password.")
            return user, password
    except (FileNotFoundError, ValueError) as e:
        log_error("N/A", "read_creds", str(e))
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        sys.exit(1)

def execute_ssh_command(host, user, password, command):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=password)
        
        # Disable interactive paging
        client.exec_command("set cli pager off")
        
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode()
        client.close()
        return output
    except Exception as e:
        error_message = f"Error executing command on {host}: {e}"
        log_error(host, command, error_message)
        print(f"{Fore.RED}Error executing command '{command}' on {host}: {e}{Style.RESET_ALL}")
        return None

def store_output(host, command, output, context, error=False):
    timestamp = datetime.now().strftime("%m-%d-%y-%H-%M-%S")
    logs_dir = "output"
    host_dir = os.path.join(logs_dir, host)
    os.makedirs(host_dir, exist_ok=True)
    sanitized_cmd = command.replace(" ", "_")
    suffix = "-ERROR" if error else ""
    log_file_path = os.path.join(host_dir, f"{sanitized_cmd}-{context}-{timestamp}{suffix}.txt")
    with open(log_file_path, "w") as log_file:
        log_file.write(output)
    return log_file_path

def log_error(host, command, error_message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_log_path = os.path.join(os.path.dirname(__file__), "errors.log")
    with open(error_log_path, "a") as error_log:
        error_log.write(f"{timestamp} | {host} | {command} | {error_message}\n")

def find_recent_pre_files(host):
    host_dir = os.path.join("output", host)
    if not os.path.exists(host_dir):
        return []

    pre_files = [f for f in os.listdir(host_dir) if "-pre-" in f]
    pre_files.sort(key=lambda x: os.path.getmtime(os.path.join(host_dir, x)), reverse=True)
    return pre_files

def compare_outputs(pre_file, post_file):
    # Implement custom comparison logic for each command
    # Return "pass" or "fail" with detailed comparison results
    pass

def main():
    init(autoreset=True)  # Initialize colorama

    if len(sys.argv) < 4 or "-c" not in sys.argv:
        print(f"Syntax: {sys.argv[0]} [-v] -c context hostname\n\n")
        sys.exit(1)

    verbose = "-v" in sys.argv
    context_index = sys.argv.index("-c") + 1

    if context_index >= len(sys.argv) - 1:
        print("Error: Context and hostname must follow the -c option.")
        sys.exit(1)

    context = sys.argv[context_index].lower()
    fwname = sys.argv[context_index + 1].strip()

    if context not in ["pre", "post"]:
        print("Error: Context must be 'pre' or 'post'.")
        sys.exit(1)

    user, password = read_creds()

    if context == "pre":
        for command in STATUS_COMMANDS:
            output = execute_ssh_command(fwname, user, password, command)
            if output:
                store_output(fwname, command, output, context)
            else:
                error_message = f"Failed to execute command: {command}"
                error_file_path = store_output(fwname, command, error_message, context, error=True)
                log_error(fwname, command, error_file_path)

    elif context == "post":
        pre_files = find_recent_pre_files(fwname)
        if not pre_files:
            print(f"{Fore.YELLOW}Warning: No pre-change files found for {fwname}.{Style.RESET_ALL}")
            sys.exit(1)

        # Check the age of the most recent pre file
        most_recent_pre_file = pre_files[0]
        pre_file_path = os.path.join("output", fwname, most_recent_pre_file)
        pre_file_time = datetime.fromtimestamp(os.path.getmtime(pre_file_path))
        if datetime.now() - pre_file_time > timedelta(hours=24):
            print(f"{Fore.YELLOW}Warning: The most recent pre-change file for {fwname} is more than 24 hours old.{Style.RESET_ALL}")

        for command in STATUS_COMMANDS:
            output = execute_ssh_command(fwname, user, password, command)
            if output:
                post_file_path = store_output(fwname, command, output, context)
                # Compare with the most recent pre file
                pre_file = next((f for f in pre_files if command.replace(" ", "_") in f), None)
                if pre_file:
                    pre_file_path = os.path.join("output", fwname, pre_file)
                    compare_outputs(pre_file_path, post_file_path)
            else:
                error_message = f"Failed to execute command: {command}"
                error_file_path = store_output(fwname, command, error_message, context, error=True)
                log_error(fwname, command, error_file_path)

if __name__ == "__main__":
    main()