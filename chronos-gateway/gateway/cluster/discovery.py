import socket
import asyncio
import json
import logging
from typing import Dict, Optional, List
from datetime import datetime

from gateway.config import config
from gateway.cluster.scorer import calculate_hardware_score, get_mac_address_value

logger = logging.getLogger(__name__)

class ClusterPeer:
    def __init__(self, ip: str, hostname: str, score: int, mac: int, role: str):
        self.ip = ip
        self.hostname = hostname
        self.score = score
        self.mac = mac
        self.role = role
        self.last_seen = datetime.now()

class DiscoveryManager:
    """
    Отговаря за откриването на други гейтуеи в мрежата чрез UDP Broadcast.
    """
    def __init__(self):
        self.port = config.get("cluster.discovery_port", 8891)
        self.shared_secret = config.get("cluster.shared_secret")
        self.peers: Dict[str, ClusterPeer] = {}
        self._running = False
        
        # Локални данни
        self.local_score = calculate_hardware_score()
        self.local_mac = get_mac_address_value()
        self.hostname = socket.gethostname()

    def get_local_priority_tuple(self):
        """Връща (priority_override, score, mac) за сравнение"""
        p_override = config.get("cluster.priority")
        p_val = int(p_override) if isinstance(p_override, int) else 999999
        return (p_val, self.local_score, self.local_mac)

    async def start(self):
        self._running = True
        # Стартираме слушателя и излъчвателя паралелно
        await asyncio.gather(
            self._listen(),
            self._broadcast_loop()
        )

    async def _broadcast_loop(self):
        """Периодично излъчва нашето присъствие"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setblocking(False)

        while self._running:
            try:
                data = {
                    "secret": self.shared_secret,
                    "hostname": self.hostname,
                    "score": self.local_score,
                    "mac": self.local_mac,
                    "priority": config.get("cluster.priority"),
                    "role": "master" if self.is_leader() else "slave", # Текущо състояние
                    "web_port": config.web_port
                }
                message = json.dumps(data).encode()
                sock.sendto(message, ('<broadcast>', self.port))
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
            
            await asyncio.sleep(5)

    async def _listen(self):
        """Слуша за съобщения от други гейтуеи"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            # На Windows SO_REUSEADDR работи малко по-различно, но за UDP е ок
            sock.bind(('', self.port))
        except Exception as e:
            logger.error(f"Failed to bind discovery port {self.port}: {e}")
            return

        sock.setblocking(False)
        loop = asyncio.get_running_loop()

        logger.info(f"Cluster Discovery listening on port {self.port}")

        while self._running:
            try:
                data, addr = await loop.sock_recvfrom(sock, 1024)
                payload = json.loads(data.decode())
                
                if payload.get("secret") != self.shared_secret:
                    continue
                
                ip = addr[0]
                if ip == self.get_local_ip(): # Игнорираме себе си
                    continue

                self.peers[ip] = ClusterPeer(
                    ip=ip,
                    hostname=payload.get("hostname"),
                    score=payload.get("score", 0),
                    mac=payload.get("mac", 0),
                    role=payload.get("role", "slave")
                )
                # Почистване на стари пиъри
                self._cleanup_peers()
                
            except Exception as e:
                if self._running:
                    logger.debug(f"Discovery listen error: {e}")
            await asyncio.sleep(0.1)

    def _cleanup_peers(self):
        """Премахва гейтуеи, които не са се обаждали скоро"""
        now = datetime.now()
        threshold = config.get("cluster.heartbeat_interval", 5) * 3
        to_delete = [ip for ip, p in self.peers.items() if (now - p.last_seen).total_seconds() > threshold]
        for ip in to_delete:
            del self.peers[ip]

    def is_leader(self) -> bool:
        """
        Логика за избор на лидер (Фаза 4 - преглед)
        Сравнява локалния приоритет с всички познати пиъри.
        """
        local_p = self.get_local_priority_tuple()
        
        for ip, peer in self.peers.items():
            peer_p_override = 999999 # Slave devices don't usually override unless config says so
            peer_p = (peer_p_override, peer.score, peer.mac)
            
            # Ако някой друг има по-висок приоритет (по-малко число или по-висок скор)
            if self._compare_priority(peer_p, local_p) > 0:
                return False
        return True

    def _compare_priority(self, p1, p2) -> int:
        """
        Сравнява два приоритета. Връща > 0 ако p1 е по-силен от p2.
        Priority Tuple: (manual_priority, hardware_score, mac_address)
        """
        # 1. Сравнение на ръчен приоритет (по-малкото е по-силно)
        if p1[0] < p2[0]: return 1
        if p1[0] > p2[0]: return -1
        
        # 2. Сравнение на хардуерен скор (по-голямото е по-силно)
        if p1[1] > p2[1]: return 1
        if p1[1] < p2[1]: return -1
        
        # 3. Сравнение на MAC (по-малкото е по-силно)
        if p1[2] < p2[2]: return 1
        if p1[2] > p2[2]: return -1
        
        return 0

    def get_local_ip(self) -> str:
        """Връща локалния IP адрес"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def stop(self):
        self._running = False

discovery_manager = DiscoveryManager()
