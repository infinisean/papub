 device = {
        "device_type": "cisco_ios",
        "host": "your_device_ip",
        "username": "your_username",
        "use_keys": True,  # Indicate using SSH keys
        "key_file": "/path/to/your/private_key", # Path to your private key file
        # "password": "your_password" # Not needed if using keys exclusively
    }

try:
        # Establish SSH connection
        with ConnectHandler(**device) as net_connect:
            # Send configuration commands
            output = net_connect.send_config_set(['set cli scripting-mode on', 'set cli pager off'])
            print(output)

            # Send show commands
            output = net_connect.send_command('show system info')
            print(output)

            # Send commands with pipes (using triple quotes for multiline)
            output = net_connect.send_command("""show counter global filter delta yes | match pkt_recv""")
            print(output)

            # Pause for a few seconds
            time.sleep(5)

    except Exception as e:
        print(f"An error occurred: {e}")