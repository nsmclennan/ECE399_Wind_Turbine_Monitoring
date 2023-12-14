import network
import socket
from time import sleep, sleep_ms


def create_AP(ssid, password):
    """Create a wireless AP with the specified SSID and password."""
    # Enable WLAN AP
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=ssid, password=password)
    ap.active(True)
    
    while not ap.active():
        sleep_ms(1)
    
    ip = ap.ifconfig()[0]
    print(f'AP active. Pico available at {ip}')
    return ap, ip

def connect_to_network(ssid, password, retry=True):
    """Connect to a wireless network using the specified SSID and password."""
    # Enable WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    # Connect to the target network
    wlan.connect(ssid, password)
    timeout = 15
    while wlan.status() >= 0 and wlan.status() < 3 and timeout > 0:
        print('Waiting for connection...')
        timeout -= 1
        sleep(1)
    if not wlan.isconnected():
        if wlan.status() == network.STAT_WRONG_PASSWORD:
            raise RuntimeError('Incorrect WiFi password')
        elif wlan.status() == network.STAT_NO_AP_FOUND:
            raise RuntimeError('Failed to find WiFi network')
        elif wlan.status() == network.STAT_CONNECT_FAIL:
            if retry:
                print("Retrying connection")
                return connect_to_network(ssid, password, False)
            else:
                raise RuntimeError('Failed to connect to WiFi network')
        elif timeout == 0:
            raise RuntimeError('Timeout connecting to WiFi network')
        else:
            print(wlan.status())
            raise RuntimeError('Unknown connection error!')
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    return wlan, ip

def unquote(string):
    """Decode a URL-escaped string."""
    # Mostly based on https://forum.micropython.org/viewtopic.php?t=3076
    if isinstance(string, str):
        string = string.encode()
    
    string = string.replace(b'+', b' ')
    
    parts = string.split(b'%')
    
    if len(parts) == 1:
        return string.decode()
    
    res = bytearray(parts[0])
    for item in parts[1:]:
        try:
            res.append(int(item[:2], 16))
            res.extend(item[2:])
        except KeyError:
            res.append(b'%')
            res.extend(item)
    return res.decode()

def open_socket(ip):
    """Open/bind an HTTP socket to host a web server."""
    connection = socket.socket()
    connection.bind((ip, 80)) # Reduce inconsistent binding issues by using ip to distinguish AP and WLAN
    connection.listen(3)
    return connection
