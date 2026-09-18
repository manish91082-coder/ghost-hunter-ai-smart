from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


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

    def rewind_from(self, block_number: int) -> int:
        """Mark all discoveries at/after a fork point orphaned and invalidate blocks."""
        cur = self._db.execute(
            "UPDATE discoveries SET status='orphaned' WHERE block_number>=? AND status='canonical'",
            (block_number,),
        )
        self._db.execute(
            "UPDATE blocks SET canonical=0 WHERE number>=?", (block_number,)
        )
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
        if number > 0:
            previous = self._db.execute(
                "SELECT hash FROM blocks WHERE number=? AND canonical=1",
                (number - 1,),
            ).fetchone()
            if not previous or previous["hash"] != row["parent_hash"]:
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
