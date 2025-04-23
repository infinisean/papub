import paramiko
import time
import re
import os

def read_ssh_key():
    with open('/root/.ssh/id_rsa.pub', 'r') as file:
        return file.read().strip()

def create_ssh_client(hostname, username, ssh_key):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, key_filename=ssh_key)
    return client

def wait_for_prompt(channel, hostname):
    buffer = ''
    while True:
        if channel.recv_ready():
            buffer += channel.recv(1024).decode('utf-8')
            if re.search(rf'{hostname} \(primary|secondary-active|standby\)', buffer, re.IGNORECASE):
                break
        time.sleep(1)

def execute_command(channel, command):
    channel.send(command + '\n')
    time.sleep(5)  # Wait for command execution
    output = ''
    while channel.recv_ready():
        output += channel.recv(1024).decode('utf-8')
    return output

def main():
    ssh_key = '/root/.ssh/id_rsa'  # Path to the private key
    username = 'pano-xml'
    hostnames = ['a46panorama', 'l17panorama']
    command = 'show high-availability state'
    output_dir = '/tmp/palo'

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    while True:
        for hostname in hostnames:
            try:
                client = create_ssh_client(hostname, username, ssh_key)
                channel = client.invoke_shell()

                wait_for_prompt(channel, hostname)
                output = execute_command(channel, command)

                output_file = os.path.join(output_dir, f'{hostname}_ha-state.txt')
                with open(output_file, 'w') as file:
                    file.write(output)

                client.close()
            except Exception as e:
                print(f"Error connecting to {hostname}: {e}")

        time.sleep(60)

if __name__ == "__main__":
    main()