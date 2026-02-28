"""
Seed node: listens for peer registration and peer-list requests.
Maintains Peer List (PL); accepts Dead Node reports.
"""
import socket
import threading
import json
from protocol import encode_message, read_message


class SeedNode:
    def __init__(self, port: int):
        self.port = port
        self.peer_list = []  # list of {"ip": str, "port": int}
        self.lock = threading.Lock()

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", self.port))
        sock.listen(20)
        print(f"[Seed:{self.port}] Listening on port {self.port}")
        while True:
            conn, addr = sock.accept()
            threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True).start()

    def _handle_client(self, conn: socket.socket, addr):
        try:
            msg = read_message(conn)
            if not msg:
                return
            typ = msg.get("type")
            if typ == "REGISTER":
                peer_port = msg.get("port")
                peer_ip = addr[0]
                with self.lock:
                    entry = {"ip": peer_ip, "port": peer_port}
                    if entry not in self.peer_list:
                        self.peer_list.append(entry)
                conn.send(encode_message({"type": "OK"}))
            elif typ == "GET_PL":
                with self.lock:
                    pl = list(self.peer_list)
                conn.send(encode_message({"type": "PEER_LIST", "peers": pl}))
            elif typ == "DEAD_NODE":
                # Log dead node report; optionally remove from PL
                dead_ip = msg.get("dead_ip")
                dead_port = msg.get("dead_port")
                reporter = msg.get("reporter_ip")
                report = msg.get("report")
                if report:
                    print(f"[Seed:{self.port}] {report}")
                else:
                    print(f"[Seed:{self.port}] Dead node report: {dead_ip}:{dead_port} (from {reporter})")
                with self.lock:
                    self.peer_list = [p for p in self.peer_list if not (p["ip"] == dead_ip and p["port"] == dead_port)]
                conn.send(encode_message({"type": "OK"}))
        except Exception as e:
            print(f"[Seed:{self.port}] Error: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass


def main():
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9000
    node = SeedNode(port)
    node.run()


if __name__ == "__main__":
    main()
