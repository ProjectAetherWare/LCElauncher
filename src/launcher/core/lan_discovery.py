import re
import socket
import struct
import threading
import time


MULTICAST_ADDR = '224.0.2.60'
MULTICAST_PORT = 4445
DISCOVER_TIMEOUT = 5.0


def _parse_lan_packet(data):
    try:
        text = data.decode('utf-8', errors='ignore')
    except Exception:
        return None
    port = None
    motd = None
    m = re.search(r'\[AD\](\d+)\[/AD\]', text)
    if m:
        port = int(m.group(1))
    m = re.search(r'\[MOTD\](.*?)\[/MOTD\]', text, re.DOTALL)
    if m:
        motd = m.group(1).strip()
    if port is not None:
        return {'port': port, 'motd': motd or 'LAN World'}
    return None


def discover_lan_servers(timeout=DISCOVER_TIMEOUT, on_found=None):
    found = {}
    lock = threading.Lock()

    def receive():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(0.5)
            sock.bind(('', MULTICAST_PORT))
            mreq = struct.pack('4sl', socket.inet_aton(MULTICAST_ADDR), socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            deadline = time.time() + timeout
            while time.time() < deadline:
                try:
                    data, addr = sock.recvfrom(1024)
                    parsed = _parse_lan_packet(data)
                    if parsed:
                        host = addr[0]
                        port = parsed['port']
                        key = '%s:%d' % (host, port)
                        with lock:
                            if key not in found:
                                found[key] = {
                                    'address': '%s:%d' % (host, port),
                                    'name': parsed.get('motd', 'LAN World'),
                                    'host': host,
                                    'port': port
                                }
                                if on_found:
                                    on_found(found[key])
                except socket.timeout:
                    continue
                except Exception:
                    break
            sock.close()
        except Exception:
            pass

    t = threading.Thread(target=receive, daemon=True)
    t.start()
    t.join(timeout=timeout + 0.5)
    return list(found.values())
