import machine
import os
from time import sleep, sleep_ms
import ubinascii
import ucryptolib

from network_utils import create_AP, connect_to_network, unquote, open_socket


CONFIG_FILE = const("config.txt")
SETUP_AP_SSID = const("Pi Pico Setup")
SETUP_AP_PASSWORD = const("12345678")


# Store WiFi credentials encrypted to increase difficulty of reading
# TODO freeze code in flash and also disable debug pins to increase difficulty of reverse engineering
def encrypt(msg):
    # Encrypt config with AES-ECB using device-specific flash ID padded with constant as a 128-bit key (256-bit key also supported)
    aes = ucryptolib.aes(machine.unique_id() + ubinascii.unhexlify("0123456789abcdef"), 1)
    return aes.encrypt(msg + '\0'*((16 - len(msg))%16))
def decrypt(msg):
    aes = ucryptolib.aes(machine.unique_id() + ubinascii.unhexlify("0123456789abcdef"), 1)
    return aes.decrypt(msg).decode().rstrip('\0')

def setup_webpage():
    return f"""<!DOCTYPE html>
<html><head><title>Pico W - Wi-Fi Setup</title></head>
<body>
<h1>Pico W - Wi-Fi Setup</h1>
<form method="post" action="/connect">
<label for="ssid">SSID:</label><br>
<input type="text" id="ssid" name="ssid" placeholder="Wi-Fi Network"><br>
<label for="pass">Password:</label><br>
<input type="password" id="pass" name="pass"><br><br>
<input type="submit" value="Connect">
</form>
</body></html>"""

def serve_setup_page(connection):
    # Start the web server
    print('Server ready for connections')
    while True:
        try:
            client, addr = connection.accept()
            print(f'Connection from {addr}')
            
            request = client.recv(1024).decode()
            print(request)
            try:
                target = ' '.join(request.split()[0:2])
            except IndexError:
                pass
            
            if target == "POST /connect":
                try:
                    # Handle same or separate packet for POST data
                    if "\r\n\r\nssid" in request:
                        data = request.split("\r\n\r\n")[1].split('&')
                    else:
                        data = client.recv(1024).decode().split('&')
                    ssid = unquote(data[0]).split('ssid=')[1]
                    password = unquote(data[1]).split('pass=')[1]
                    print("SSID: " + ssid)
                    #print("Pass: " + password)
                    client.close()
                    return ssid, password
                except IndexError:
                    pass
                client.send("HTTP/1.1 303 See Other\r\nLocation: /\r\n")
            else:
                client.send(setup_webpage())
            client.close()
        except OSError as e:
            print(e)

def setup_wifi():
    """Connect to saved network or create AP for user to enter new credentials and then join new network."""
    # Try to connect to saved network, if any
    if CONFIG_FILE in os.listdir():
        with open(CONFIG_FILE, 'rb') as config_file:
            try:
                config_lines = decrypt(config_file.read()).splitlines()
                ssid = config_lines[0].split("ssid: ")[1]
                password = config_lines[1].split("password: ")[1]
                
                wlan, ip = connect_to_network(ssid, password)
                return wlan, ip
            except (IndexError, ValueError):
                raise Exception("Failed to parse config")
            except RuntimeError as e:
                print("Failed to connect to saved network:\n    " + str(e))
    else:
        print("No config file found")
    
    # Create AP with web server for user to enter WiFi config
    while True:
        ap, ip = create_AP(SETUP_AP_SSID, SETUP_AP_PASSWORD)
        
        connection = open_socket(ip)
        ssid, password = serve_setup_page(connection)
        sleep(1) # Hopefully help reduce inconsistent socket in use errors
        connection.close()
        
        #ap.active(False)
        #while ap.active():
        #    sleep_ms(1)
        
        try:
            wlan, ip = connect_to_network(ssid, password)
            break
        except RuntimeError as e:
            print("Failed to connect to network:\n    " + str(e))
            sleep(2) # Hopefully help reduce inconsistent socket in use errors
    print("Success!!")
    
    # Check if config is unchanged
    config_data = encrypt(f'ssid: {ssid}\npassword: {password}')
    if CONFIG_FILE in os.listdir():
        with open(CONFIG_FILE, 'rb') as config_file:
            current_config = config_file.read()
            if current_config == config_data:
                print("Same config... skipping")
                return wlan, ip
    
    # Save new config
    with open(CONFIG_FILE, 'wb') as config_file:
        config_file.write(config_data)
    
    return wlan, ip
