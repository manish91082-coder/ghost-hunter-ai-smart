from __future__ import annotations

import json
from typing import AsyncIterator

import websockets

from .models import BlockState
import time


class PolygonWSS:
    """Low-latency new-head stream.

    WSS is an acceleration path only. The canonical block is re-read through RPC
    before execution-critical state is accepted.
    """

    def __init__(self, urls: list[str], timeout_seconds: float = 3.0):
        self.urls = urls
        self.timeout_seconds = timeout_seconds

    async def heads(self) -> AsyncIterator[BlockState]:
        if not self.urls:
            raise ValueError("no WSS URLs configured")
        while True:
            connected = False
            for url in self.urls:
                try:
                    async with websockets.connect(url, open_timeout=self.timeout_seconds) as ws:
                        await ws.send(json.dumps({
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "eth_subscribe",
                            "params": ["newHeads"],
                        }))
                        connected = True
                        async for message in ws:
                            data = json.loads(message)
                            result = data.get("params", {}).get("result")
                            if not result:
                                continue
                            yield BlockState(
                                number=int(result["number"], 16),
                                hash=result["hash"],
                                parent_hash=result["parentHash"],
                                timestamp=int(result["timestamp"], 16),
                                base_fee=None,
                                observed_at_ns=time.time_ns(),
                            )
                except Exception:
                    continue
            if not connected:
                raise RuntimeError("all WSS providers unavailable")
