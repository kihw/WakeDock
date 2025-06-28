"""
Network utility functions for WakeDock
"""

import socket
import ipaddress
import asyncio
import logging
import subprocess
import platform
from typing import Dict, List, Optional, Tuple, Any
import struct
import time

logger = logging.getLogger(__name__)


class NetworkUtils:
    """Utility class for network operations"""
    
    @staticmethod
    def is_port_open(host: str, port: int, timeout: float = 5.0) -> bool:
        """Check if a port is open on a host
        
        Args:
            host: Host to check
            port: Port to check
            timeout: Connection timeout in seconds
            
        Returns:
            True if port is open
        """
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.error, socket.timeout):
            return False
    
    @staticmethod
    async def is_port_open_async(host: str, port: int, timeout: float = 5.0) -> bool:
        """Asynchronously check if a port is open on a host
        
        Args:
            host: Host to check
            port: Port to check
            timeout: Connection timeout in seconds
            
        Returns:
            True if port is open
        """
        try:
            future = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(future, timeout=timeout)
            writer.close()
            await writer.wait_closed()
            return True
        except (asyncio.TimeoutError, OSError, ConnectionRefusedError):
            return False
    
    @staticmethod
    def find_free_port(start_port: int = 8000, end_port: int = 9000, host: str = 'localhost') -> Optional[int]:
        """Find a free port in the given range
        
        Args:
            start_port: Start of port range
            end_port: End of port range
            host: Host to check ports on
            
        Returns:
            Free port number or None if no free port found
        """
        for port in range(start_port, end_port + 1):
            if not NetworkUtils.is_port_open(host, port, timeout=1.0):
                try:
                    # Double-check by trying to bind to the port
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.bind((host, port))
                        return port
                except OSError:
                    continue
        return None
    
    @staticmethod
    def get_local_ip() -> str:
        """Get the local IP address
        
        Returns:
            Local IP address as string
        """
        try:
            # Connect to a remote address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                return local_ip
        except Exception:
            return "127.0.0.1"
    
    @staticmethod
    def get_all_local_ips() -> List[str]:
        """Get all local IP addresses
        
        Returns:
            List of local IP addresses
        """
        import netifaces
        
        ips = []
        try:
            for interface in netifaces.interfaces():
                addresses = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addresses:
                    for address_info in addresses[netifaces.AF_INET]:
                        ip = address_info['addr']
                        if ip != '127.0.0.1':
                            ips.append(ip)
        except ImportError:
            # Fallback if netifaces is not available
            import socket
            hostname = socket.gethostname()
            try:
                ips = [socket.gethostbyname(hostname)]
            except socket.gaierror:
                ips = ['127.0.0.1']
        
        return ips
    
    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        """Check if an IP address is valid
        
        Args:
            ip: IP address to validate
            
        Returns:
            True if IP is valid
        """
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_valid_domain(domain: str) -> bool:
        """Check if a domain name is valid
        
        Args:
            domain: Domain name to validate
            
        Returns:
            True if domain is valid
        """
        import re
        
        if not domain or len(domain) > 253:
            return False
        
        # Basic domain validation regex
        domain_pattern = re.compile(
            r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
        )
        
        return bool(domain_pattern.match(domain))
    
    @staticmethod
    def resolve_hostname(hostname: str) -> Optional[str]:
        """Resolve hostname to IP address
        
        Args:
            hostname: Hostname to resolve
            
        Returns:
            IP address or None if resolution fails
        """
        try:
            return socket.gethostbyname(hostname)
        except socket.gaierror:
            return None
    
    @staticmethod
    async def resolve_hostname_async(hostname: str) -> Optional[str]:
        """Asynchronously resolve hostname to IP address
        
        Args:
            hostname: Hostname to resolve
            
        Returns:
            IP address or None if resolution fails
        """
        try:
            loop = asyncio.get_event_loop()
            result = await loop.getaddrinfo(hostname, None, family=socket.AF_INET)
            if result:
                return result[0][4][0]
        except (socket.gaierror, OSError):
            pass
        return None
    
    @staticmethod
    def ping_host(host: str, timeout: int = 5) -> bool:
        """Ping a host to check if it's reachable
        
        Args:
            host: Host to ping
            timeout: Ping timeout in seconds
            
        Returns:
            True if host is reachable
        """
        try:
            # Determine ping command based on OS
            if platform.system().lower() == 'windows':
                cmd = ['ping', '-n', '1', '-w', str(timeout * 1000), host]
            else:
                cmd = ['ping', '-c', '1', '-W', str(timeout), host]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=timeout + 1
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    @staticmethod
    async def ping_host_async(host: str, timeout: int = 5) -> bool:
        """Asynchronously ping a host to check if it's reachable
        
        Args:
            host: Host to ping
            timeout: Ping timeout in seconds
            
        Returns:
            True if host is reachable
        """
        try:
            # Determine ping command based on OS
            if platform.system().lower() == 'windows':
                cmd = ['ping', '-n', '1', '-w', str(timeout * 1000), host]
            else:
                cmd = ['ping', '-c', '1', '-W', str(timeout), host]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            
            try:
                await asyncio.wait_for(process.wait(), timeout=timeout + 1)
                return process.returncode == 0
            except asyncio.TimeoutError:
                process.kill()
                return False
        except FileNotFoundError:
            return False
    
    @staticmethod
    def create_magic_packet(mac_address: str) -> bytes:
        """Create a Wake-on-LAN magic packet
        
        Args:
            mac_address: MAC address in format XX:XX:XX:XX:XX:XX
            
        Returns:
            Magic packet as bytes
        """
        # Remove separators and convert to bytes
        mac_bytes = bytes.fromhex(mac_address.replace(':', '').replace('-', ''))
        
        # Magic packet: 6 bytes of 0xFF followed by 16 repetitions of the MAC address
        magic_packet = b'\xFF' * 6 + mac_bytes * 16
        
        return magic_packet
    
    @staticmethod
    def send_wake_on_lan(mac_address: str, broadcast_ip: str = '255.255.255.255', port: int = 9) -> bool:
        """Send Wake-on-LAN packet to wake up a device
        
        Args:
            mac_address: MAC address of the device to wake
            broadcast_ip: Broadcast IP address
            port: UDP port to send to (usually 7 or 9)
            
        Returns:
            True if packet was sent successfully
        """
        try:
            magic_packet = NetworkUtils.create_magic_packet(mac_address)
            
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                s.sendto(magic_packet, (broadcast_ip, port))
            
            logger.info(f"Wake-on-LAN packet sent to {mac_address}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Wake-on-LAN packet to {mac_address}: {e}")
            return False
    
    @staticmethod
    async def send_wake_on_lan_async(mac_address: str, broadcast_ip: str = '255.255.255.255', port: int = 9) -> bool:
        """Asynchronously send Wake-on-LAN packet
        
        Args:
            mac_address: MAC address of the device to wake
            broadcast_ip: Broadcast IP address
            port: UDP port to send to
            
        Returns:
            True if packet was sent successfully
        """
        try:
            magic_packet = NetworkUtils.create_magic_packet(mac_address)
            
            # Use asyncio's datagram endpoint
            loop = asyncio.get_event_loop()
            transport, protocol = await loop.create_datagram_endpoint(
                lambda: asyncio.DatagramProtocol(),
                allow_broadcast=True
            )
            
            try:
                transport.sendto(magic_packet, (broadcast_ip, port))
                logger.info(f"Wake-on-LAN packet sent to {mac_address}")
                return True
            finally:
                transport.close()
        except Exception as e:
            logger.error(f"Failed to send Wake-on-LAN packet to {mac_address}: {e}")
            return False
    
    @staticmethod
    def get_network_interfaces() -> Dict[str, Dict[str, Any]]:
        """Get information about network interfaces
        
        Returns:
            Dictionary of network interface information
        """
        try:
            import netifaces
            
            interfaces = {}
            for interface_name in netifaces.interfaces():
                interface_info = {
                    'name': interface_name,
                    'addresses': {}
                }
                
                addresses = netifaces.ifaddresses(interface_name)
                
                # IPv4 addresses
                if netifaces.AF_INET in addresses:
                    interface_info['addresses']['ipv4'] = addresses[netifaces.AF_INET]
                
                # IPv6 addresses
                if netifaces.AF_INET6 in addresses:
                    interface_info['addresses']['ipv6'] = addresses[netifaces.AF_INET6]
                
                # MAC address
                if netifaces.AF_LINK in addresses:
                    interface_info['addresses']['mac'] = addresses[netifaces.AF_LINK]
                
                interfaces[interface_name] = interface_info
            
            return interfaces
        except ImportError:
            logger.warning("netifaces not available, returning minimal interface info")
            return {'lo': {'name': 'lo', 'addresses': {'ipv4': [{'addr': '127.0.0.1'}]}}}
    
    @staticmethod
    def calculate_network_address(ip: str, netmask: str) -> Optional[str]:
        """Calculate network address from IP and netmask
        
        Args:
            ip: IP address
            netmask: Netmask
            
        Returns:
            Network address or None if calculation fails
        """
        try:
            network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
            return str(network.network_address)
        except ValueError:
            return None
    
    @staticmethod
    def is_private_ip(ip: str) -> bool:
        """Check if an IP address is private
        
        Args:
            ip: IP address to check
            
        Returns:
            True if IP is private
        """
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private
        except ValueError:
            return False
    
    @staticmethod
    def get_port_info(port: int) -> Dict[str, Any]:
        """Get information about a port
        
        Args:
            port: Port number
            
        Returns:
            Port information including common service names
        """
        # Common port mappings
        common_ports = {
            20: 'FTP Data',
            21: 'FTP Control',
            22: 'SSH',
            23: 'Telnet',
            25: 'SMTP',
            53: 'DNS',
            80: 'HTTP',
            110: 'POP3',
            143: 'IMAP',
            443: 'HTTPS',
            993: 'IMAPS',
            995: 'POP3S',
            3306: 'MySQL',
            5432: 'PostgreSQL',
            6379: 'Redis',
            27017: 'MongoDB',
            3000: 'Node.js Dev',
            8000: 'HTTP Alt',
            8080: 'HTTP Proxy',
            8443: 'HTTPS Alt',
            9000: 'HTTP Alt'
        }
        
        return {
            'port': port,
            'service': common_ports.get(port, 'Unknown'),
            'is_well_known': port <= 1023,
            'is_registered': 1024 <= port <= 49151,
            'is_dynamic': port >= 49152
        }


# Global instance for easy access
network_utils = NetworkUtils()
