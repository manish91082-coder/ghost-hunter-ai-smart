from __future__ import annotations

from dataclasses import dataclass

from .store import DiscoveryStore


@dataclass(frozen=True)
class CanonicalHead:
    number: int
    hash: str
    parent_hash: str


class ReorgGuard:
    """Tracks canonical ancestry and requests overlap replay on discontinuity."""

    def __init__(self, overlap: int = 12) -> None:
        if overlap < 1:
            raise ValueError("overlap must be positive")
        self.head: CanonicalHead | None = None
        self.overlap = overlap

    def accept(self, head: CanonicalHead) -> bool:
        if self.head is None:
            self.head = head
            return True
        if head.number <= self.head.number:
            return head.number == self.head.number and head.hash == self.head.hash
        if head.number == self.head.number + 1 and head.parent_hash == self.head.hash:
            self.head = head
            return True
        return False

    def rescan_start(self, current_number: int) -> int:
        return max(0, current_number - self.overlap)


class CanonicalCoordinator:
    """Coordinates block ancestry with durable evidence.

    A discontinuity never advances canonical state. The caller must replay from
    the returned overlap point after fetching a trusted replacement chain.
    """

    def __init__(self, store: DiscoveryStore, overlap: int = 12) -> None:
        self.store = store
        self.guard = ReorgGuard(overlap)
        durable = self.store.latest_canonical_head()
        if durable is not None:
            number, block_hash, parent_hash = durable
            self.guard.head = CanonicalHead(number, block_hash, parent_hash)

    def observe(self, head: CanonicalHead) -> tuple[bool, int | None]:
        if self.guard.accept(head):
            self.store.record_block(head.number, head.hash, head.parent_hash)
            return True, None

        if self.guard.head is None:
            return False, self.guard.rescan_start(head.number)

        fork_start = min(head.number, self.guard.head.number)
        self.store.rewind_from(fork_start)
        self.guard.head = None
        return False, self.guard.rescan_start(head.number)

    def record_replayed_block(self, head: CanonicalHead) -> bool:
        if not self.guard.accept(head):
            return False
        self.store.record_block(head.number, head.hash, head.parent_hash)
        return True
