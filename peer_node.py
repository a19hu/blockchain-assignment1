"""
Peer node: registers with seeds, connects to >=4 peers, gossip (TX/block), liveness, PoW mining.
Simplified single-threaded design with threads for network and mining.
"""
import socket
import threading
import time
import random
import sys
import os

# Add project root for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from protocol import encode_message, read_message
from config import (
    NUM_SEEDS,
    SEED_PORTS,
    INTERARRIVAL_TIME,
    LIVENESS_INTERVAL,
    LIVENESS_FAIL_THRESHOLD,
    BLOCK_TIME_TOLERANCE,
    MIN_PEERS,
)
from wallet import Wallet
from transaction import create_transaction, verify_transaction, tx_to_bytes, tx_from_bytes
from block import create_block, block_to_bytes, block_from_bytes, compute_block_hash
from block_db import (
    get_db_path,
    init_db,
    insert_block,
    get_block_by_hash,
    get_block_by_height,
    get_max_height,
    block_hash_exists,
)
from crypto_utils import sha256_hash

# Default seed host (run seeds on same machine for demo)
SEED_HOST = "127.0.0.1"


class PeerNode:
    def __init__(self, my_port: int, my_host: str = "127.0.0.1", hash_power: float = 10.0):
        self.my_port = my_port
        self.my_host = my_host
        self.hash_power = hash_power  # percentage 0-100
        self.wallet = Wallet()
        self.db_path = get_db_path(str(my_port))
        init_db(self.db_path)
        # Genesis block if empty chain
        if get_max_height(self.db_path) < 0:
            genesis = create_block("0", 0, [])
            insert_block(self.db_path, genesis)
            self.longest_chain_height = 0

        self.peer_connections = {}  # (ip, port) -> socket
        self.conn_to_peer = {}  # socket -> (ip, port)
        self.lock = threading.Lock()
        self.message_list = set()  # hashes of seen gossip messages (for dedup)
        self.msg_counter = 0
        self.pending_blocks = []  # blocks to validate and append
        self.pending_txs = []  # unconfirmed transactions
        self.mining_abort = False
        self.mining_interrupt = threading.Event()
        self.longest_chain_height = get_max_height(self.db_path)
        self.seeds = [(SEED_HOST, p) for p in SEED_PORTS[:NUM_SEEDS]]
        self.liveness_fail_count = {}  # (ip, port) -> consecutive failures
        self.liveness_state = {}  # (ip, port) -> {"fail": int, "awaiting": bool}
        self.genesis_hash = "0" * 64  # placeholder genesis

    def _gossip_msg(self, timestamp: float, ip: str, msg_num: int) -> str:
        return f"{timestamp}:{ip}:{msg_num}"

    def _gossip_id_from_msg(self, msg: str) -> str:
        return sha256_hash(msg.encode())

    def _register_with_seeds(self):
        n = NUM_SEEDS
        required = (n // 2) + 1
        ok = 0
        for (h, p) in self.seeds:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                s.connect((h, p))
                s.send(encode_message({"type": "REGISTER", "port": self.my_port}))
                resp = read_message(s)
                if resp and resp.get("type") == "OK":
                    ok += 1
                s.close()
            except Exception as e:
                print(f"[Peer {self.my_port}] Seed {h}:{p} failed: {e}")
            if ok >= required:
                break
        print(f"[Peer {self.my_port}] Registered with {ok} seeds (need {required})")

    def _get_peer_list(self) -> list:
        all_peers = []
        for (h, p) in self.seeds:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                s.connect((h, p))
                s.send(encode_message({"type": "GET_PL"}))
                resp = read_message(s)
                s.close()
                if resp and resp.get("type") == "PEER_LIST":
                    all_peers.extend(resp.get("peers", []))
            except Exception:
                pass
        # Union: unique (ip, port), exclude self
        seen = set()
        unique = []
        for pe in all_peers:
            key = (pe["ip"], pe["port"])
            if key not in seen and pe["port"] != self.my_port:
                seen.add(key)
                unique.append(pe)
        return unique

    def _connect_to_peers(self, peer_list: list):
        random.shuffle(peer_list)
        need = min(len(peer_list), max(MIN_PEERS, 4))
        connected = 0
        for pe in peer_list[:need]:
            if connected >= need:
                break
            ip, port = pe["ip"], pe["port"]
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(10)
                s.connect((ip, port))
                s.settimeout(None)
                key = (ip, port)
                with self.lock:
                    self.peer_connections[key] = s
                    self.conn_to_peer[s] = key
                    self.liveness_fail_count[key] = 0
                    self.liveness_state[key] = {"fail": 0, "awaiting": False}
                try:
                    s.send(encode_message({"type": "HELLO", "port": self.my_port}))
                    print(f"[Peer {self.my_port}] Sent HELLO to {ip}:{port}")
                except Exception:
                    pass
                connected += 1
                threading.Thread(target=self._recv_loop, args=(s,), daemon=True).start()
            except Exception as e:
                print(f"[Peer {self.my_port}] Connect to {ip}:{port} failed: {e}")
        print(f"[Peer {self.my_port}] Connected to {connected} peers")

    def _report_dead(self, dead_ip: str, dead_port: int):
        report = f"Dead Node:{dead_ip}:{dead_port}:{time.time()}:{self.my_host}"
        for (h, p) in self.seeds:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                s.connect((h, p))
                s.send(encode_message({
                    "type": "DEAD_NODE",
                    "dead_ip": dead_ip,
                    "dead_port": dead_port,
                    "reporter_ip": self.my_host,
                    "report": report,
                }))
                read_message(s)
                s.close()
            except Exception:
                pass

    def _close_peer(self, key):
        with self.lock:
            s = self.peer_connections.pop(key, None)
            if s:
                self.conn_to_peer.pop(s, None)
                self.liveness_state.pop(key, None)
                try:
                    s.close()
                except Exception:
                    pass

    def _broadcast(self, msg: dict, exclude_socket=None):
        with self.lock:
            for key, s in list(self.peer_connections.items()):
                if s is exclude_socket:
                    continue
                try:
                    s.send(encode_message(msg))
                except Exception:
                    self._close_peer(key)

    def _recv_loop(self, conn: socket.socket):
        peer_key = None
        try:
            while True:
                msg = read_message(conn)
                if not msg:
                    break
                with self.lock:
                    peer_key = self.conn_to_peer.get(conn)
                if not peer_key:
                    break
                self._handle_message(msg, conn)
        except Exception as e:
            pass
        finally:
            if peer_key:
                self._close_peer(peer_key)

    def _handle_message(self, msg: dict, from_conn: socket.socket):
        typ = msg.get("type")
        if typ == "GOSSIP_TX":
            gossip_msg = msg.get("gossip_msg")
            gid = self._gossip_id_from_msg(gossip_msg) if gossip_msg else msg.get("gossip_id")
            if not gid:
                return
            if gid and gid in self.message_list:
                return
            tx_data = msg.get("tx")
            if not tx_data:
                return
            self.message_list.add(gid)
            if not verify_transaction(tx_data):
                return
            with self.lock:
                self.pending_txs.append(tx_data)
            self._broadcast(msg, exclude_socket=from_conn)
        elif typ == "GOSSIP_BLOCK":
            gossip_msg = msg.get("gossip_msg")
            gid = self._gossip_id_from_msg(gossip_msg) if gossip_msg else msg.get("gossip_id")
            if not gid:
                return
            if gid and gid in self.message_list:
                return
            block_data = msg.get("block")
            if not block_data:
                return
            self.message_list.add(gid)
            with self.lock:
                self.pending_blocks.append((block_data, from_conn))
            self._broadcast(msg, exclude_socket=from_conn)
            if block_data.get("Height", -1) > self.longest_chain_height:
                self.mining_abort = True
        elif typ == "LIVENESS_REQ":
            try:
                from_conn.send(encode_message({"type": "LIVENESS_RESP"}))
            except Exception:
                pass
        elif typ == "LIVENESS_RESP":
            with self.lock:
                if from_conn in self.conn_to_peer:
                    key = self.conn_to_peer[from_conn]
                    self.liveness_fail_count[key] = 0
                    if key in self.liveness_state:
                        self.liveness_state[key]["fail"] = 0
                        self.liveness_state[key]["awaiting"] = False
        elif typ == "HELLO":
            listen_port = msg.get("port")
            if not listen_port:
                return
            with self.lock:
                old_key = self.conn_to_peer.get(from_conn)
                new_key = (old_key[0], listen_port) if old_key else None
                if not new_key:
                    return
                existing = self.peer_connections.get(new_key)
                if existing and existing is not from_conn:
                    try:
                        from_conn.close()
                    except Exception:
                        pass
                    return
                if old_key in self.peer_connections:
                    self.peer_connections.pop(old_key, None)
                    self.liveness_fail_count.pop(old_key, None)
                    self.liveness_state.pop(old_key, None)
                self.peer_connections[new_key] = from_conn
                self.conn_to_peer[from_conn] = new_key
                self.liveness_fail_count[new_key] = 0
                self.liveness_state[new_key] = {"fail": 0, "awaiting": False}
            print(f"[Peer {self.my_port}] Handshake from {new_key[0]}:{new_key[1]}")
        elif typ == "GET_BLOCKS":
            from_height = msg.get("from_height", 0)
            to_height = msg.get("to_height", -1)
            if to_height < 0:
                to_height = get_max_height(self.db_path)
            blocks = []
            for h in range(from_height, to_height + 1):
                b = get_block_by_height(self.db_path, h)
                if b:
                    blocks.append(b)
            try:
                from_conn.send(encode_message({"type": "BLOCKS", "blocks": blocks}))
            except Exception:
                pass
        elif typ == "BLOCKS":
            for b in msg.get("blocks", []):
                with self.lock:
                    self.pending_blocks.append((b, None))
        elif typ == "LATEST_HEIGHT":
            try:
                from_conn.send(encode_message({
                    "type": "LATEST_BLOCK",
                    "height": self.longest_chain_height,
                    "block": get_block_by_height(self.db_path, self.longest_chain_height),
                }))
            except Exception:
                pass
        elif typ == "LATEST_BLOCK":
            # New node sync: received Bk, put in pending, request B0..Bk-1
            block = msg.get("block")
            height = msg.get("height", -1)
            if block and height >= 0:
                with self.lock:
                    self.pending_blocks.insert(0, (block, None))
                if from_conn and height > 0:
                    from_conn.send(encode_message({"type": "GET_BLOCKS", "from_height": 0, "to_height": height - 1}))

    def _process_pending_blocks(self):
        while True:
            with self.lock:
                if not self.pending_blocks:
                    break
                block, _ = self.pending_blocks.pop(0)
            if not self._validate_block(block):
                # Re-queue only if parent missing (so we process in chain order)
                if block["Height"] > 0 and not get_block_by_hash(self.db_path, block["PrevHash"]):
                    with self.lock:
                        self.pending_blocks.append((block, None))
                break
            prev_height = self.longest_chain_height
            insert_block(self.db_path, block)
            self.longest_chain_height = max(self.longest_chain_height, block["Height"])
            self.msg_counter += 1
            gossip_msg = self._gossip_msg(time.time(), self.my_host, self.msg_counter)
            gid = self._gossip_id_from_msg(gossip_msg)
            self.message_list.add(gid)
            self._broadcast({"type": "GOSSIP_BLOCK", "gossip_id": gid, "gossip_msg": gossip_msg, "block": block})
            with self.lock:
                if block["Height"] > prev_height and not self.pending_blocks:
                    self.mining_interrupt.set()

    def _validate_block(self, block: dict) -> bool:
        if block_hash_exists(self.db_path, block["BlockHash"]):
            return False
        if abs(block["Timestamp"] - time.time()) > BLOCK_TIME_TOLERANCE:
            return False
        tx_hashes = [t["TxID"] for t in block.get("Transactions", [])]
        if block.get("TxHashes") and sorted(block["TxHashes"]) != sorted(tx_hashes):
            return False
        computed = compute_block_hash(block["PrevHash"], block["Height"], block["Timestamp"], tx_hashes)
        if computed != block["BlockHash"]:
            return False
        if block["Height"] > 0 and not get_block_by_hash(self.db_path, block["PrevHash"]):
            return False  # parent not yet in chain
        return True

    def _liveness_loop(self):
        while True:
            time.sleep(LIVENESS_INTERVAL)
            with self.lock:
                to_check = list(self.peer_connections.items())
            for key, s in to_check:
                with self.lock:
                    state = self.liveness_state.get(key, {"fail": 0, "awaiting": False})
                    if state["awaiting"]:
                        state["fail"] += 1
                    self.liveness_state[key] = state
                    if state["fail"] >= LIVENESS_FAIL_THRESHOLD:
                        self._report_dead(key[0], key[1])
                        self._close_peer(key)
                        continue
                try:
                    s.send(encode_message({"type": "LIVENESS_REQ"}))
                    with self.lock:
                        if key in self.liveness_state:
                            self.liveness_state[key]["awaiting"] = True
                except Exception:
                    with self.lock:
                        state = self.liveness_state.get(key, {"fail": 0, "awaiting": False})
                        state["fail"] += 1
                        state["awaiting"] = False
                        self.liveness_state[key] = state
                        if state["fail"] >= LIVENESS_FAIL_THRESHOLD:
                            self._report_dead(key[0], key[1])
                            self._close_peer(key)
                            continue

    def _mining_loop(self):
        mean_tk = 1.0 / INTERARRIVAL_TIME
        lambda_ = self.hash_power * mean_tk / 100.0
        while True:
            self._process_pending_blocks()
            with self.lock:
                if self.pending_blocks:
                    time.sleep(0.5)
                    continue
                txs = list(self.pending_txs)[:10] if self.pending_txs else []
            latest = get_block_by_height(self.db_path, self.longest_chain_height)
            prev_hash = latest["BlockHash"] if latest else self.genesis_hash
            next_height = self.longest_chain_height + 1
            tau = random.expovariate(lambda_) if lambda_ > 0 else 10.0
            self.mining_abort = False
            self.mining_interrupt.clear()
            deadline = time.time() + tau
            while time.time() < deadline and not self.mining_abort and not self.mining_interrupt.is_set():
                time.sleep(0.2)
                self._process_pending_blocks()
            if self.mining_abort or self.mining_interrupt.is_set():
                continue
            # Mine block
            with self.lock:
                txs = [self.pending_txs.pop(0) for _ in range(min(len(self.pending_txs), 10))] if self.pending_txs else []
            block = create_block(prev_hash, next_height, txs)
            insert_block(self.db_path, block)
            self.longest_chain_height = next_height
            self.msg_counter += 1
            gossip_msg = self._gossip_msg(time.time(), self.my_host, self.msg_counter)
            gid = self._gossip_id_from_msg(gossip_msg)
            self.message_list.add(gid)
            self._broadcast({"type": "GOSSIP_BLOCK", "gossip_id": gid, "gossip_msg": gossip_msg, "block": block})
            print(f"[Peer {self.my_port}] Mined block height={next_height}")

    def _listen(self):
        listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_sock.bind(("0.0.0.0", self.my_port))
        listen_sock.listen(20)
        print(f"[Peer {self.my_port}] Listening on {self.my_port}")
        while True:
            conn, addr = listen_sock.accept()
            key = (addr[0], addr[1])
            with self.lock:
                self.peer_connections[key] = conn
                self.conn_to_peer[conn] = key
                self.liveness_fail_count[key] = 0
                self.liveness_state[key] = {"fail": 0, "awaiting": False}
            try:
                conn.send(encode_message({"type": "HELLO", "port": self.my_port}))
                print(f"[Peer {self.my_port}] Sent HELLO to {key[0]}:{key[1]}")
            except Exception:
                pass
            threading.Thread(target=self._recv_loop, args=(conn,), daemon=True).start()

    def run(self):
        threading.Thread(target=self._listen, daemon=True).start()
        time.sleep(0.5)
        self._register_with_seeds()
        pl = self._get_peer_list()
        self._connect_to_peers(pl)
        # New node sync: ask one peer for latest block, then we'll request B0..Bk-1 on reply
        with self.lock:
            for _, s in list(self.peer_connections.items())[:1]:
                try:
                    s.send(encode_message({"type": "LATEST_HEIGHT"}))
                except Exception:
                    pass
                break
        threading.Thread(target=self._liveness_loop, daemon=True).start()
        threading.Thread(target=self._mining_loop, daemon=True).start()
        while True:
            time.sleep(60)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    hash_power = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
    node = PeerNode(port, hash_power=hash_power)
    node.run()


if __name__ == "__main__":
    main()
