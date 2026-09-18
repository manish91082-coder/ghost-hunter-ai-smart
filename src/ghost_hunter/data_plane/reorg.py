from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CanonicalHead:
    number: int
    hash: str
    parent_hash: str


class ReorgGuard:
    def __init__(self) -> None:
        self.head: CanonicalHead | None = None

    def accept(self, head: CanonicalHead) -> bool:
        if self.head is None:
            self.head = head
            return True
        if head.number == self.head.number + 1 and head.parent_hash == self.head.hash:
            self.head = head
            return True
        if head.number <= self.head.number:
            return False
        # Gap or parent mismatch: caller must resync from a safe overlap.
        self.head = head
        return False

    def rescan_start(self, current_number: int, overlap: int = 12) -> int:
        return max(0, current_number - overlap)
