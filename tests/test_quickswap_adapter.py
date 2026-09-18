[object Object]
@pytest.mark.asyncio
async def test_persist_candidate_requires_canonical_block_evidence():
    from ghost_hunter.data_plane.store import DiscoveryStore
    adapter = make_adapter()
    token0, token1, pool = "0x"+"1"*40, "0x"+"2"*40, "0x"+"3"*40
    candidate = adapter.decode_log("v2", {
        "address": V2_FACTORY,
        "topics": [EVENTS["v2_pair_created"].topic0, topic(token0), topic(token1)],
        "data": "0x"+word(pool)+f"{1:064x}",
        "blockNumber": "0xa", "blockHash": "h10", "transactionHash": "0xtx", "logIndex": "0x3"
    })
    with DiscoveryStore() as store:
        store.record_block(10, "h10", "h9")
        assert adapter.persist_candidate(candidate, store, {"pool": pool})
        assert not adapter.persist_candidate(candidate, store, {"pool": pool})
