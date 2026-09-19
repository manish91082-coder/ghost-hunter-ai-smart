# ZERO-COST RESOURCE ARCHITECTURE

## Policy
**ZERO-COST-FIRST is a non-negotiable project constraint.**

Core development, research, discovery, simulation, testing and shadow-mode operation must use local/open-source/free-tier resources wherever technically possible.

No paid SaaS, paid AI model, paid RPC, paid database, paid cloud or paid monitoring service is a mandatory dependency.

## Free-First Stack
- Local PC compute
- Python / Node.js
- Docker
- GitHub and applicable free GitHub Actions allowance
- Open-source libraries
- Local AI models where hardware permits
- Free provider tiers where their current terms permit
- SQLite / DuckDB / JSONL / Parquet
- Foundry / Anvil / pytest and other open-source testing tools

## RPC Strategy
Use a provider abstraction with multiple free sources and automatic fallback.

Alchemy currently advertises a free tier of 30M compute units/month and 25 requests/second with Polygon support. These quotas can change and must be checked at runtime.

QuickNode documents Polygon endpoints and free-trial functionality. Trial quotas are not treated as permanent guarantees.

No single provider is a hard dependency.

## Data Strategy
Priority:
1. Direct RPC
2. On-chain event/log indexing
3. Local SQLite/DuckDB
4. Free public indexer APIs
5. Free subgraphs/APIs for discovery cross-checks

The system must remain useful without a paid indexer.

## Provider Interface
Required abstraction:
- get_block
- get_logs
- call
- estimate_gas
- get_transaction_receipt
- subscribe_new_heads
- send_raw_transaction

Provider manager must maintain:
- health score
- latency score
- quota tracking
- automatic rotation
- backoff
- circuit breaker
- consistency comparison

## AI Cost Rule
AI is not required for execution-critical mathematics.

Use deterministic code for:
- AMM math
- fee calculation
- gas calculation
- flash-loan repayment
- profitability gate
- transaction invariants
- authorization

Use free/local AI for:
- research
- strategy discovery
- candidate ranking
- anomaly detection
- code/document analysis
- adaptive parameter suggestions

## Capital Preservation
The user's reported approximately $5-$6 POL balance is a constrained execution budget, not a development budget.

Before live execution:
- local simulation first
- testnet where practical
- shadow/paper mode
- native balance floor
- hard gas cap
- no speculative transaction submission

## Zero-Cost Development Ladder
### Stage 1
Local-only development, math, strategy research, tests, historical replay and fork simulation.

### Stage 2
Free RPC + live Polygon discovery + shadow execution.

### Stage 3
Free/local AI for ranking, anomaly detection and research.

### Stage 4
Controlled mainnet validation only after deterministic and security acceptance gates.

## Cost Firewall
Every external dependency must declare:
- free-tier status
- quota
- rate limit
- API-key requirement
- failure behavior
- fallback provider
- execution criticality

Introducing a paid-only dependency requires explicit project-governance approval.

## Zero-Cost Acceptance Criterion
The project must reach a complete discovery prototype, strategy engine, exact math engine, simulation engine, security suite and shadow-mode engine without purchasing infrastructure.

Live execution is a separate risk and capital decision.

## Research Sources
- Alchemy pricing: https://www.alchemy.com/pricing
- Alchemy Polygon: https://www.alchemy.com/polygon
- QuickNode Polygon: https://www.quicknode.com/docs/polygon
