import paramiko
import time
import re
import os
import argparse
from prettytable import PrettyTable

def read_ssh_key():
    with open('/root/.ssh/id_rsa.pub', 'r') as file:
        return file.read().strip()

def create_ssh_client(hostname, username, ssh_key):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, key_filename=ssh_key)
    return client

def wait_for_prompt(channel, hostname, debug):
    buffer = ''
    counter = 0
    raw_output_file = f"/tmp/palo/{hostname}_RAW_SSH_OUT.txt"
    
    with open(raw_output_file, 'w') as raw_file:
        while True:
            if channel.recv_ready():
                received_data = channel.recv(1024).decode('utf-8')
                buffer += received_data
                raw_file.write(received_data)
                raw_file.flush()  # Ensure data is written immediately
                if re.search(rf'{hostname} \(primary|secondary-active|standby\)', buffer, re.IGNORECASE):
                    if debug:
                        print(f"Prompt detected for {hostname}")
                    break
            if debug:
                print(f"Waiting for prompt... {counter} seconds")
            counter += 1
            time.sleep(1)

def execute_command(channel, command, debug):
    if debug:
        print(f"Sending command: {command}")
    channel.send(command + '\r\n')
    time.sleep(5)  # Wait for command execution
    output = ''
    while channel.recv_ready():
        output += channel.recv(1024).decode('utf-8')
    if debug:
        print("Command output received")
    return output

def get_ha_state(hostname, username, ssh_key, output_dir, debug):
    try:
        if debug:
            print(f"Connecting to {hostname}")
        client = create_ssh_client(hostname, username, ssh_key)
        channel = client.invoke_shell()

        wait_for_prompt(channel, hostname, debug)
        output = execute_command(channel, 'show high-availability state', debug)

        output_file = os.path.join(output_dir, f'{hostname}_ha-state.txt')
        with open(output_file, 'w') as file:
            file.write(output)

        if debug:
            print(f"Output written to {output_file}")

        # Parse and print the HA state in a table format
        table = PrettyTable()
        table.field_names = ["Element", "Value"]
        for line in output.splitlines():
            if ':' in line:
                element, value = line.split(':', 1)
                table.add_row([element.strip(), value.strip()])
        print(table)

        client.close()
    except Exception as e:
        print(f"Error connecting to {hostname}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Retrieve HA state from Panorama devices.')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    ssh_key = '/root/.ssh/id_rsa'  # Path to the private key
    username = 'pano-xml'
    hostnames = ['a46panorama', 'l17panorama']
    output_dir = '/tmp/palo'

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    while True:
        for hostname in hostnames:
            get_ha_state(hostname, username, ssh_key, output_dir, args.debug)
        time.sleep(60)

if __name__ == "__main__":
    main()