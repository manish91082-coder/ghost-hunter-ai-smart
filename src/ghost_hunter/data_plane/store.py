from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import PoolState, TokenState


@dataclass(frozen=True)
class DiscoveryRecord:
    candidate_key: str
    venue: str
    pool_type: str
    pool_address: str
    block_number: int
    block_hash: str
    transaction_hash: str | None
    log_index: int | None
    payload_hash: str
    status: str = "canonical"

    def __post_init__(self) -> None:
        object.__setattr__(self, "pool_address", self.pool_address.lower())


class DiscoveryStore:
    """Zero-cost durable discovery/evidence store backed by SQLite.

    Records are append-safe and idempotent by canonical candidate key. A block
    hash is mandatory so replay/reorg handling cannot silently treat an
    unanchored event as canonical.
    """

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        self._db = sqlite3.connect(self.path)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    @staticmethod
    def payload_hash(payload: Any) -> str:
        encoded = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), default=str
        ).encode()
        return hashlib.sha256(encoded).hexdigest()

    def _init_schema(self) -> None:
        self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS blocks (
                number INTEGER PRIMARY KEY,
                hash TEXT NOT NULL,
                parent_hash TEXT NOT NULL,
                canonical INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS discoveries (
                candidate_key TEXT PRIMARY KEY,
                venue TEXT NOT NULL,
                pool_type TEXT NOT NULL,
                pool_address TEXT NOT NULL,
                block_number INTEGER NOT NULL,
                block_hash TEXT NOT NULL,
                transaction_hash TEXT,
                log_index INTEGER,
                payload_hash TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('canonical','orphaned')),
                UNIQUE(block_hash, transaction_hash, log_index),
                FOREIGN KEY(block_number) REFERENCES blocks(number)
            );
            CREATE INDEX IF NOT EXISTS idx_discoveries_block
                ON discoveries(block_number);
            CREATE INDEX IF NOT EXISTS idx_discoveries_pool
                ON discoveries(pool_address);
            CREATE TABLE IF NOT EXISTS token_snapshots (
                address TEXT PRIMARY KEY, decimals INTEGER, symbol TEXT, code_hash TEXT,
                block_number INTEGER NOT NULL, source TEXT NOT NULL, confidence REAL NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('canonical','orphaned'))
            );
            CREATE TABLE IF NOT EXISTS pool_snapshots (
                address TEXT PRIMARY KEY, venue TEXT NOT NULL, pool_type TEXT NOT NULL,
                token0 TEXT NOT NULL, token1 TEXT, block_number INTEGER NOT NULL,
                state_json TEXT NOT NULL, state_hash TEXT NOT NULL, source TEXT NOT NULL,
                confidence REAL NOT NULL, status TEXT NOT NULL CHECK(status IN ('canonical','orphaned'))
            );
            CREATE INDEX IF NOT EXISTS idx_token_snapshots_block ON token_snapshots(block_number);
            CREATE INDEX IF NOT EXISTS idx_pool_snapshots_block ON pool_snapshots(block_number);
            """
        )
        self._db.commit()

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> "DiscoveryStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def record_block(self, number: int, block_hash: str, parent_hash: str) -> None:
        if number < 0 or not block_hash or not parent_hash:
            raise ValueError("canonical block requires number, hash and parent_hash")
        existing = self._db.execute(
            "SELECT hash FROM blocks WHERE number=?", (number,)
        ).fetchone()
        if existing and existing["hash"] != block_hash:
            self.rewind_from(number)
        if number > 0:
            previous = self._db.execute(
                "SELECT hash FROM blocks WHERE number=? AND canonical=1",
                (number - 1,),
            ).fetchone()
            if previous is not None and previous["hash"] != parent_hash:
                raise ValueError("canonical block parent does not match durable predecessor")
        self._db.execute(
            """
            INSERT INTO blocks(number, hash, parent_hash, canonical)
            VALUES(?,?,?,1)
            ON CONFLICT(number) DO UPDATE SET
              hash=excluded.hash,
              parent_hash=excluded.parent_hash,
              canonical=1
            """,
            (number, block_hash, parent_hash),
        )
        self._db.commit()

    def record_discovery(self, record: DiscoveryRecord, payload: Any) -> bool:
        if not record.block_hash:
            raise ValueError("discovery block_hash is required")
        if record.status != "canonical":
            raise ValueError("only canonical discoveries may be recorded")
        block = self._db.execute(
            "SELECT hash FROM blocks WHERE number=? AND canonical=1",
            (record.block_number,),
        ).fetchone()
        if not block or block["hash"] != record.block_hash:
            raise ValueError("discovery is not anchored to a canonical block")
        computed = self.payload_hash(payload)
        existing = self._db.execute(
            "SELECT payload_hash,status FROM discoveries WHERE candidate_key=?",
            (record.candidate_key,),
        ).fetchone()
        if existing:
            if existing["payload_hash"] != computed or computed != record.payload_hash:
                raise ValueError("candidate replay payload mismatch")
            return False
        if computed != record.payload_hash:
            raise ValueError("payload hash mismatch")
        self._db.execute(
            """
            INSERT INTO discoveries(
              candidate_key,venue,pool_type,pool_address,block_number,block_hash,
              transaction_hash,log_index,payload_hash,payload_json,status
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                record.candidate_key,
                record.venue,
                record.pool_type,
                record.pool_address.lower(),
                record.block_number,
                record.block_hash,
                record.transaction_hash,
                record.log_index,
                record.payload_hash,
                json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str),
                record.status,
            ),
        )
        self._db.commit()
        return True

    def record_discovery_bundle(
        self,
        record: DiscoveryRecord,
        payload: Any,
        pool_state: PoolState,
        token_states: tuple[TokenState, TokenState],
    ) -> bool:
        """Atomically persist verified discovery evidence and canonical snapshots."""
        if pool_state.block_number != record.block_number or any(
            token.block_number != record.block_number for token in token_states
        ):
            raise ValueError("discovery bundle block mismatch")
        if not record.block_hash or record.status != "canonical":
            raise ValueError("discovery bundle requires canonical block hash")
        block = self._db.execute(
            "SELECT hash FROM blocks WHERE number=? AND canonical=1", (record.block_number,)
        ).fetchone()
        if not block or block["hash"] != record.block_hash:
            raise ValueError("discovery bundle is not anchored to a canonical block")
        computed = self.payload_hash(payload)
        if computed != record.payload_hash:
            raise ValueError("payload hash mismatch")
        existing = self._db.execute(
            "SELECT payload_hash,status FROM discoveries WHERE candidate_key=?", (record.candidate_key,)
        ).fetchone()
        if existing and (existing["payload_hash"] != computed or existing["status"] != "canonical"):
            raise ValueError("candidate replay payload mismatch")
        try:
            self._db.execute("BEGIN")
            if not existing:
                self._db.execute(
                    """INSERT INTO discoveries(
                      candidate_key,venue,pool_type,pool_address,block_number,block_hash,
                      transaction_hash,log_index,payload_hash,payload_json,status
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        record.candidate_key, record.venue, record.pool_type, record.pool_address.lower(),
                        record.block_number, record.block_hash, record.transaction_hash, record.log_index,
                        record.payload_hash, json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str),
                        "canonical",
                    ),
                )
            for token in token_states:
                self._record_token_snapshot_uncommitted(token)
            self._record_pool_snapshot_uncommitted(pool_state)
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise
        return not bool(existing)

    def _record_token_snapshot_uncommitted(self, state: TokenState) -> bool:
        existing = self._db.execute(
            "SELECT block_number FROM token_snapshots WHERE address=?", (state.address.lower(),)
        ).fetchone()
        if existing and int(existing["block_number"]) > state.block_number:
            return False
        self._db.execute("""INSERT INTO token_snapshots(address,decimals,symbol,code_hash,block_number,source,confidence,status)
            VALUES(?,?,?,?,?,?,?,'canonical')
            ON CONFLICT(address) DO UPDATE SET decimals=excluded.decimals,symbol=excluded.symbol,
            code_hash=excluded.code_hash,block_number=excluded.block_number,source=excluded.source,
            confidence=excluded.confidence,status='canonical'""",
            (state.address.lower(), state.decimals, state.symbol, state.code_hash,
             state.block_number, state.source, state.confidence),
        )
        return True

    def _record_pool_snapshot_uncommitted(self, state: PoolState) -> bool:
        existing = self._db.execute(
            "SELECT block_number FROM pool_snapshots WHERE address=?", (state.address.lower(),)
        ).fetchone()
        if existing and int(existing["block_number"]) > state.block_number:
            return False
        payload = json.dumps(dict(state.state), sort_keys=True, separators=(",", ":"), default=str)
        self._db.execute("""INSERT INTO pool_snapshots(address,venue,pool_type,token0,token1,block_number,state_json,state_hash,source,confidence,status)
            VALUES(?,?,?,?,?,?,?,?,?,?,'canonical')
            ON CONFLICT(address) DO UPDATE SET venue=excluded.venue,pool_type=excluded.pool_type,
            token0=excluded.token0,token1=excluded.token1,block_number=excluded.block_number,
            state_json=excluded.state_json,state_hash=excluded.state_hash,source=excluded.source,
            confidence=excluded.confidence,status='canonical'""",
            (state.address.lower(), state.venue, state.pool_type, state.token0.lower(),
             state.token1.lower() if state.token1 else None, state.block_number, payload,
             state.state_hash, state.source, state.confidence),
        )
        return True

    def record_token_snapshot(self, state: TokenState) -> bool:
        if state.block_number < 0:
            raise ValueError("token snapshot requires a valid block number")
        if self.canonical_block_hash(state.block_number) is None:
            raise ValueError("token snapshot is not anchored to a canonical block")
        existing = self._db.execute("SELECT block_number FROM token_snapshots WHERE address=?", (state.address.lower(),)).fetchone()
        if existing and int(existing["block_number"]) > state.block_number:
            return False
        self._db.execute("""INSERT INTO token_snapshots(address,decimals,symbol,code_hash,block_number,source,confidence,status)
            VALUES(?,?,?,?,?,?,?,'canonical')
            ON CONFLICT(address) DO UPDATE SET decimals=excluded.decimals,symbol=excluded.symbol,
            code_hash=excluded.code_hash,block_number=excluded.block_number,source=excluded.source,
            confidence=excluded.confidence,status='canonical'""",
            (state.address.lower(),state.decimals,state.symbol,state.code_hash,state.block_number,state.source,state.confidence))
        self._db.commit()
        return True

    def record_pool_snapshot(self, state: PoolState) -> bool:
        if state.block_number < 0:
            raise ValueError("pool snapshot requires a valid block number")
        if self.canonical_block_hash(state.block_number) is None:
            raise ValueError("pool snapshot is not anchored to a canonical block")
        existing = self._db.execute("SELECT block_number FROM pool_snapshots WHERE address=?", (state.address.lower(),)).fetchone()
        if existing and int(existing["block_number"]) > state.block_number:
            return False
        payload = json.dumps(dict(state.state), sort_keys=True, separators=(",", ":"), default=str)
        self._db.execute("""INSERT INTO pool_snapshots(address,venue,pool_type,token0,token1,block_number,state_json,state_hash,source,confidence,status)
            VALUES(?,?,?,?,?,?,?,?,?,?,'canonical')
            ON CONFLICT(address) DO UPDATE SET venue=excluded.venue,pool_type=excluded.pool_type,
            token0=excluded.token0,token1=excluded.token1,block_number=excluded.block_number,
            state_json=excluded.state_json,state_hash=excluded.state_hash,source=excluded.source,
            confidence=excluded.confidence,status='canonical'""",
            (state.address.lower(),state.venue,state.pool_type,state.token0.lower(),
             state.token1.lower() if state.token1 else None,state.block_number,payload,
             state.state_hash,state.source,state.confidence))
        self._db.commit()
        return True

    def rewind_from(self, block_number: int) -> int:
        """Mark all discoveries at/after a fork point orphaned and invalidate blocks."""
        cur = self._db.execute(
            "UPDATE discoveries SET status='orphaned' WHERE block_number>=? AND status='canonical'",
            (block_number,),
        )
        self._db.execute(
            "UPDATE blocks SET canonical=0 WHERE number>=?", (block_number,)
        )
        self._db.execute("UPDATE token_snapshots SET status='orphaned' WHERE block_number>=? AND status='canonical'", (block_number,))
        self._db.execute("UPDATE pool_snapshots SET status='orphaned' WHERE block_number>=? AND status='canonical'", (block_number,))
        self._db.commit()
        return cur.rowcount

    def canonical_block_hash(self, number: int) -> str | None:
        row = self._db.execute(
            "SELECT hash FROM blocks WHERE number=? AND canonical=1", (number,)
        ).fetchone()
        return row["hash"] if row else None

    def latest_canonical_head(self) -> tuple[int, str, str] | None:
        """Return the latest contiguous canonical block, failing closed on gaps."""
        row = self._db.execute(
            """
            SELECT number,hash,parent_hash
            FROM blocks
            WHERE canonical=1
            ORDER BY number DESC
            LIMIT 1
            """
        ).fetchone()
        if not row:
            return None
        number = int(row["number"])
        first = self._db.execute(
            "SELECT number,hash FROM blocks WHERE canonical=1 ORDER BY number ASC LIMIT 1"
        ).fetchone()
        if first is None:
            raise RuntimeError("durable canonical chain is inconsistent")
        previous_hash = first["hash"]
        previous_number = int(first["number"])
        rows = self._db.execute(
            "SELECT number,hash,parent_hash FROM blocks WHERE canonical=1 AND number>? ORDER BY number ASC",
            (previous_number,),
        ).fetchall()
        for current in rows:
            current_number = int(current["number"])
            if current_number != previous_number + 1 or current["parent_hash"] != previous_hash:
                raise RuntimeError("durable canonical chain is inconsistent")
            previous_number = current_number
            previous_hash = current["hash"]
        if previous_number != number or previous_hash != row["hash"]:
            raise RuntimeError("durable canonical chain is inconsistent")
        return number, row["hash"], row["parent_hash"]

    def get(self, candidate_key: str) -> DiscoveryRecord | None:
        row = self._db.execute(
            """
            SELECT candidate_key,venue,pool_type,pool_address,block_number,
                   block_hash,transaction_hash,log_index,payload_hash,status
            FROM discoveries WHERE candidate_key=?
            """,
            (candidate_key,),
        ).fetchone()
        return DiscoveryRecord(**dict(row)) if row else None

    def canonical_records(self) -> list[DiscoveryRecord]:
        rows = self._db.execute(
            """
            SELECT candidate_key,venue,pool_type,pool_address,block_number,
                   block_hash,transaction_hash,log_index,payload_hash,status
            FROM discoveries WHERE status='canonical'
            ORDER BY block_number,candidate_key
            """
        ).fetchall()
        return [DiscoveryRecord(**dict(row)) for row in rows]

    def orphaned_records(self) -> list[DiscoveryRecord]:
        rows = self._db.execute(
            """
            SELECT candidate_key,venue,pool_type,pool_address,block_number,
                   block_hash,transaction_hash,log_index,payload_hash,status
            FROM discoveries WHERE status='orphaned'
            ORDER BY block_number,candidate_key
            """
        ).fetchall()
        return [DiscoveryRecord(**dict(row)) for row in rows]

    def canonical_token_snapshots(self) -> list[TokenState]:
        rows = self._db.execute("SELECT address,decimals,symbol,code_hash,block_number,source,confidence FROM token_snapshots WHERE status='canonical' ORDER BY address").fetchall()
        return [TokenState(**dict(row)) for row in rows]

    def canonical_pool_snapshots(self) -> list[PoolState]:
        rows = self._db.execute("SELECT address,venue,pool_type,token0,token1,block_number,state_json,state_hash,source,confidence FROM pool_snapshots WHERE status='canonical' ORDER BY address").fetchall()
        return [PoolState(address=row["address"],venue=row["venue"],pool_type=row["pool_type"],token0=row["token0"],token1=row["token1"],block_number=row["block_number"],state=json.loads(row["state_json"]),state_hash=row["state_hash"],source=row["source"],confidence=row["confidence"]) for row in rows]
