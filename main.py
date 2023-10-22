import blocks
import net
import sys
from select import select

if __name__ == "__main__":
    net = net.Network()
    db = blocks.Database()

    while True:
        print("> ", end="")
        sys.stdout.flush()
        readable, _, _ = select([sys.stdin] + net.peers + [net.listener], [], [])
        if sys.stdin in readable:
            line = sys.stdin.readline()
            words = line.split()
            if words == []:
                continue
            command = words[0]
            args = words[1:]
            if command == "connect":
                peer = net.connect_to(args[0], int(args[1]))
                for block in db:
                    peer.send(block.encode())
                print("Finished synchronizing peer")
            elif command == "status":
                print(f"{len(net.peers)} peers, {len(db.heap)} blocks, at block {db.head}")
            elif command == "log":
                try:
                    length = args[0]
                except IndexError:
                    length = 4
                for index, block in enumerate(db):
                    if index == length:
                        print("[more]")
                        break
                    print(block)
                else:
                    print("[end]")
            elif command == "create":
                data = bytes(" ".join(args), encoding="utf-8")
                block = db.write(data)
                net.write(block.encode())
            elif command == "offline":
                net.offline = True
            elif command == "online":
                net.offline = False
            else:
                print("Invalid command")
        else:
            peer = net.accept()
            if peer is not None:
                for block in db:
                    peer.send(block.encode())
                print("Finished synchronizing peer")
            messages = net.read()
            for msg in messages:
                if msg == b"":
                    continue
                block = blocks.Block.decode(msg)
                db.append(block)