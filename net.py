import socket
from select import select
from typing import Tuple, Union

BUFSIZE = 4096

class Network:
    def __init__(self, port=3333):
        self.peers: list[socket.socket] = []
        self.listener = None
        for _ in range(32):
            # 32 attempts
            try:
                self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.listener.bind(("127.0.0.1", port))
                self.listener.listen()
                print(f"Listening on port {port}")
                return
            except OSError:
                port += 1

    def accept(self):
        assert self.listener is not None
        peer, retaddr = self.listener.accept()
        self.peers.append(peer)

    def connect_to(self, addr, port):
        peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer.connect((addr, port))
        self.peers.append(peer)

    def read(self):
        readable, writable, errored = select(self.peers, [], self.peers, 0)
        for peer in errored:
            self.peers.remove(peer)

        for peer in readable:
            yield peer.recv(BUFSIZE)

    def write(self, data: bytes):
        readable, writable, errored = select([], self.peers, [], 0)
        for peer in writable:
            peer.send(data)
