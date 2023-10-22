import socket
from select import select
from typing import Tuple, Union

BUFSIZE = 1064

class Network:
    def __init__(self, port=3333):
        self.offline = False
        self.peers: list[socket.socket] = []
        self.listener = None
        self.port = port
        for _ in range(32):
            # 32 attempts
            try:
                self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.listener.bind(("127.0.0.1", self.port))
                self.listener.listen()
                print(f"Listening on port {self.port}")
                return
            except OSError:
                self.port += 1

    def accept(self):
        assert self.listener is not None
        readable, writable, errored = select([self.listener], [], [], 0)
        if readable:
            peer, retaddr = self.listener.accept()
            self.peers.append(peer)
            return peer

    def connect_to(self, addr, port):
        peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer.connect((addr, port))
        self.peers.append(peer)
        return peer

    def read(self):
        readable, writable, errored = select(self.peers, [], self.peers, 0)
        for peer in errored:
            self.peers.remove(peer)
            readable.remove(peer)

        for peer in readable:
            data = peer.recv(BUFSIZE)
            if data == b"":
                # remote closed
                self.peers.remove(peer)
            yield data

    def write(self, data: bytes):
        readable, writable, errored = select([], self.peers, [], 0)
        for peer in writable:
            peer.send(data)
