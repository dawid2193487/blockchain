from dataclasses import dataclass
from abc import ABC
import struct
from typing import Self
from hashlib import sha256

DATA_LENGTH = 1024
HASH_LENGTH = 256 // 8
DIFFICULTY = 2 # ostrożnie!

BLOCK_STRUCT_SCHEMA = f"!{HASH_LENGTH}sQ{DATA_LENGTH}s"

class Encodable(ABC):
    """
    Interfejs do kodowania klas do danych binarnych
    """
    def encode(self) -> bytes:
        raise NotImplementedError
    
    @classmethod
    def decode(cls, data: bytes) -> Self:
        raise NotImplementedError


@dataclass
class BlockHash(Encodable):
    value: bytes 

    def __hash__(self):
        return hash(self.value)

    def __post_init__(self):
        """
        Dodaje padding do hasha aby miał on stałą długość
        """
        # enforce size
        self.value += b"\0" * (HASH_LENGTH - len(self.value))

    def encode(self) -> bytes:
        return self.value
    
    @classmethod
    def decode(cls, data: bytes) -> Self:
        return cls(data)
    
    @property
    def is_genesis(self):
        """
        Sprawdza czy hash należy do "genesis blocku", czyli czy jego wartość to same zera
        """
        return self.value == b"\0"*(HASH_LENGTH)
    
    def __str__(self):
        return self.value.hex()


@dataclass
class BlockData(Encodable):
    value: bytes

    def __post_init__(self):
        """
        Dodaje padding do danych aby miały stałą długość
        """
        # enforce size
        self.value += b"\0" * (DATA_LENGTH - len(self.value))

    def encode(self) -> bytes:
        return self.value
    
    @classmethod
    def decode(cls, data: bytes) -> Self:
        return cls(data)


@dataclass
class Block(Encodable):
    prev: BlockHash
    nonce: int
    data: BlockData
    
    def encode(self):
        """
        Koduje blok do postaci binarnej
        """
        return struct.pack(BLOCK_STRUCT_SCHEMA, self.prev.encode(), self.nonce, self.data.encode())
    
    @classmethod
    def decode(cls, data: bytes) -> Self:
        """
        Dekoduje blok z postaci binarnej
        """
        prev_bin, nonce, data_bin = struct.unpack(BLOCK_STRUCT_SCHEMA, data)
        return cls(
            BlockHash.decode(prev_bin),
            nonce,
            BlockData.decode(data_bin),
        )
    
    @property
    def hash(self):
        """
        Oblicza hash bloku
        """
        return BlockHash(sha256(self.encode()).digest())
    
    @property
    def is_verified(self):
        """
        Sprawdza czy hash bloku jest poprawny
        """
        total = sum(self.hash.value[:DIFFICULTY])
        return total == 0
    
    def make_verified(self):
        """
        Wykonuje proof-of-work aby uczynić blok poprawnym
        """
        MAX_ITER = 2**24
        while self.nonce < MAX_ITER:
            self.nonce += 1
            if self.is_verified:
                return self
        raise Exception
            
    def __str__(self):
       stripped_data = self.data.value.strip(b'\0')
       return f"{self.hash.value.hex()} {'Verified' if self.is_verified else 'Unverified'} \n  {stripped_data}"


class Database:
    heap = dict()
    generations = {BlockHash(b"\0"): 0}
    pending = {}

    @property
    def head(self):
        """
        Zwraca hash bloku który jest końcem najdłuższego łańcucha. W przypadku remisu wybiera hash o większej wartości.
        """
        max_len = max(self.generations.values())
        candidates = [hash for hash, length in self.generations.items() if length == max_len]

        return max(candidates, key=lambda h: h.value)
    
    def resolve_pending(self, block: Block):
        child = self.pending[block.hash]
        self.append(child)
        del self.pending[block.hash]
        self.resolve_pending(child)

    def append(self, block: Block):
        """
        Dodaje blok do bazy danych
        """
        if not block.is_verified:
            raise ValueError("Attempted to append unverified block")
        self.heap[block.hash] = block
        try:
            self.generations[block.hash] = self.generations[block.prev] + 1
            self.resolve_pending(block)
        except KeyError:
            # block references a parent we don't have yet.
            self.pending[block.prev] = block

        return block

    def write(self, data: bytes):
        """
        Konstruuje blok z podanymi danymi, przeprowadza proof-of-work i zapisuje po aktualnym `head`
        """
        block = Block(
            self.head,
            0,
            BlockData(data)
        )
        block.make_verified()
        return self.append(block)

    def __iter__(self):
        """
        Iterator po kanonicznym łańcuchu
        """
        cursor = self.head
        while not cursor.is_genesis:
            yield self.heap[cursor]
            cursor = self.heap[cursor].prev


if __name__ == "__main__":
    db = Database()

    print("Primal blockchain")
    # dopisywanie po kolei
    a = db.write(b"czesc")
    b = db.write(b"siema")
    c = db.write(b"elo")

    for block in db:
        print(block)

    print("----------------------------------------------------------------")
    # dopisywanie do wczesniejszych blokow zamiast pisania po najnowszym
    b2 = db.append(Block(a.hash, 0, BlockData(b"alternatywnie")).make_verified())
    c2 = db.append(Block(b2.hash, 0, BlockData(b"tzw forkjhjkkhhhjj w")).make_verified())
    # d2 = db.append(Block(c2.hash, 0, BlockData(b"lancuchu")).make_verified())

    print(c2.encode())

    print("Final blockchain")
    for block in db:
        print(block)
