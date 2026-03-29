import struct

def make_server_identifier(ip, port = 32887):
    try:
        int(ip)
        a = (ip & 4278190080L) >> 24
        b = (ip & 16711680) >> 16
        c = (ip & 65280) >> 8
        d = ip & 255
        return '%s.%s.%s.%s:%s' % (a,
         b,
         c,
         d,
         port)
    except ValueError:
        a, b, c, d = ip.split('.')
        a = int(a)
        b = int(b)
        c = int(c)
        d = int(d)
        return '%s.%s.%s.%s:%s' % (a,
         b,
         c,
         d,
         port)


def make_game_manager_favourite_key(ip, port):
    identifier = make_server_identifier(ip, port)
    splitted = identifier.split(':')
    ip = splitted[0]
    favourite_key = (ip, port)
    return favourite_key


def get_server_details(value):
    if value.startswith('aos://'):
        splitted = value[6:].split(':')
        if len(splitted) == 1:
            host = int(splitted[0])
            port = 32887
        else:
            host, port = splitted
            host = int(host)
            port = int(port)
        host_ip = '%s.%s.%s.%s' % (host & 255,
         (host & 65280) >> 8,
         (host & 16711680) >> 16,
         (host & 4278190080L) >> 24)
    else:
        splitted = value.split(':')
        if len(splitted) == 1:
            host = splitted[0]
            port = 32887
        else:
            host, port = splitted
            port = int(port)
        import socket
        host_ip = socket.gethostbyname(host)
    return (host_ip, port)


def ip_to_int(ip):
    blocks = ip.split('.')
    a = int(blocks[0]) << 24
    b = int(blocks[1]) << 16
    c = int(blocks[2]) << 8
    d = int(blocks[3])
    return a | b | c | d