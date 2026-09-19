# P1 DISCOVERY RUNTIME DESIGN

## Goal
Turn the low-latency data plane into a replayable Polygon liquidity discovery system.

## Event-driven sequence

NEW HEAD
-> scan only the new/overlap block range
-> decode verified factory/pool events
-> register newly discovered pools
-> discover token contracts
-> read pool state
-> update state cache
-> identify affected tokens
-> route layer receives invalidation set

## Discovery sources

Primary:
- direct on-chain logs
- factory/pool contract reads

Secondary:
- free indexers/subgraphs/APIs

Secondary sources can accelerate discovery but cannot become execution truth.

## Adaptive log scanning

The scanner expands block ranges when the provider is healthy and shrinks ranges after RPC/log-limit errors. It is replayable so reorg recovery can rescan an overlap.

## Reorg policy

A new head must link to the previous canonical head. Parent mismatch or a gap triggers an overlap rescan.

## Event decoding policy

Event signatures and topic0 values must be generated/verified from canonical protocol ABIs before being activated.

This avoids silently trusting guessed event topics.

## Protocol adapter boundary

Every venue adapter must implement:
- factory discovery
- pool-created event decoder
- token extraction
- pool state reader
- pool type
- fee extraction
- execution metadata

The adapter must expose evidence for every normalized field.

## Next adapter order

1. V2-style factory/pair adapter
2. Uniswap/Algebra concentrated-liquidity adapter
3. Balancer Vault adapter
4. Curve factory adapters
5. additional Polygon venues discovered through verified deployment data

## Zero-cost constraint

No paid indexer is required. The primary discovery path is direct RPC + logs + local state.
