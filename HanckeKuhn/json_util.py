import json
import socket
import os
from typing import Any


class JSONSocket:
    def __init__(self, conn: socket.socket, *, encoding: str = "utf-8"):
        self.conn = conn
        self.buf = bytearray()
        self.encoding = encoding

    def send(self, obj: Any) -> None:
        data = json.dumps(obj, separators=(",", ":")).encode(self.encoding) + b"\n"
        self.conn.sendall(data)

    def recv(self) -> Any:
        while True:
            nl = self.buf.find(b"\n")
            if nl != -1:
                line = bytes(self.buf[:nl])
                del self.buf[:nl + 1]   # remove line + newline
                if not line:
                    continue
                return json.loads(line.decode(self.encoding))

            chunk = self.conn.recv(4096)
            if not chunk:
                if self.buf:
                    raise ConnectionError("Connection closed with a partial JSON frame")
                raise ConnectionError("Connection closed")
            self.buf.extend(chunk)

    def close(self) -> None:
        try:
            self.conn.shutdown(socket.SHUT_RDWR)
        except:
            pass
        self.conn.close()


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)