import socket, time
import struct
from threading import Thread
from shared.constants_gamemode import A2448

def parse_ace_of_spades_response(data):
    """Special parser for Ace of Spades servers"""
    if not data or len(data) < 5 or data[0:4] != '\xFF\xFF\xFF\xFF':
        return None
    
    header = ord(data[4])
    if header == 0x41:
        return {'challenge': data[5:]}
    elif header != 0x49:
        return None
    
    info = {}
    pos = 5
    
    try:
        # Protocol version
        info['protocol'] = ord(data[pos])
        pos += 1
        
        # Server name
        info['name'] = ''
        while pos < len(data) and data[pos] != '\x00':
            info['name'] += data[pos]
            pos += 1
        pos += 1
        
        # Map name
        info['map'] = ''
        while pos < len(data) and data[pos] != '\x00':
            info['map'] += data[pos]
            pos += 1
        pos += 1
        
        # Game folder
        info['game'] = ''
        while pos < len(data) and data[pos] != '\x00':
            info['game'] += data[pos]
            pos += 1
        pos += 1
        
        # Game name
        info['game_name'] = ''
        while pos < len(data) and data[pos] != '\x00':
            info['game_name'] += data[pos]
            pos += 1

        pos += 3
        
        info['players'] = ord(data[pos])
        pos += 1
        info['max_players'] = ord(data[pos])
        
        info['server_type'] = 'dedicated' if data[pos] == 'd' else 'listen'
        pos += 1
        
        info['environment'] = 'windows' if data[pos] == 'w' else 'linux'
        pos += 24

        info['version'] = ''
        while pos < len(data) and data[pos] != ';':
            info['version'] += data[pos]
            pos += 1
        pos += 1
        
        info['mode'] = ''
        while pos < len(data) and data[pos] != ';':
            info['mode'] += data[pos]
            pos += 1

        info['mode'] = list(A2448.keys())[int(info['mode'].replace("playlist=", ""))]
        
        return info
    except IndexError:
        return None

def get_server_info(ip, port=27015, timeout=1.0):
    try:
        start_time = time.time()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        end_time = time.time()
        
        s.send('\xFF\xFF\xFF\xFFTSource Engine Query\x00')
        data = s.recv(4096)
        
        if not data:
            s.close()
            return None
            
        response = parse_ace_of_spades_response(data)

        if response and 'challenge' in response:
            challenge_packet = '\xFF\xFF\xFF\xFFTSource Engine Query\x00' + response['challenge']
            s.send(challenge_packet)
            data = s.recv(4096)
            response = parse_ace_of_spades_response(data)
        
        response["ip"] = ip
        response["port"] = port
        response["ping"] = int((end_time - start_time) * 1000)
        s.close()
        return response
    except:
        if 's' in locals():
            s.close()
        return None

def scan_local_network(port=27015, timeout=1.0):
    """Scan local network for Steam game servers"""
    local_ip = socket.gethostbyname(socket.gethostname())
    network_prefix = '.'.join(local_ip.split('.')[:3])
    
    active_servers = []
    
    def check_ip(ip):
        server_info = get_server_info(ip, port, timeout)
        if server_info:
            active_servers.append(server_info)

    threads = []
    for i in range(1, 255):
        ip = network_prefix + "." + str(i)
        t = Thread(target=check_ip, args=(ip,))
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    return active_servers