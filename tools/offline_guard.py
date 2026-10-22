"""CI child-process network boundary: permit loopback tests, deny everything else."""
import ipaddress
import socket

_connect = socket.socket.connect
_getaddrinfo = socket.getaddrinfo

def local(host):
    if host == 'localhost':
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except (ValueError, TypeError):
        return False

def connect(self, address):
    if isinstance(address, tuple) and not local(address[0]):
        raise RuntimeError('offline_validation_external_network_denied')
    return _connect(self, address)

def getaddrinfo(host, *args, **kwargs):
    if not local(host):
        raise RuntimeError('offline_validation_external_dns_denied')
    return _getaddrinfo(host, *args, **kwargs)

socket.socket.connect = connect
socket.getaddrinfo = getaddrinfo
