# Uniswap v4 NVDAc → ETH replay

This script recreates one historical Base transaction on a local fork, runs 50
variants of the swap, and writes the results to `execution.png`.

https://basescan.org/tx/0xe94212cf3972d35e86dd51c9825bf96ee6286b4e903a909e1e89a00f3bb8fa78

## Requirements

- `uv`
- A compatible `base-anvil-replay` executable on your `PATH`

The Anvil build must support Base's `beryl` upgrade and the
`anvil_setNextBlockPrevRandao` RPC method. Use a binary built for your operating
system and CPU architecture.

## Run

```bash
uv run --script replay_nvda_swap_with_my_router.py
```

To start from a different `sqrtPriceLimitX96`:

```bash
uv run --script replay_nvda_swap_with_my_router.py <sqrtPriceLimitX96>
```

## Summary
The hook in 0x tweet does 
```
h = keccak256(abi.encode(
    block.prevrandao,
    blockhash(block.number - 1),
    block.timestamp,
    block.chainid,
    address(this),                 // hook proxy address
    keccak256(abi.encode(poolKey)), // pool ID
    sender,                        // caller of PoolManager.swap
    params.zeroForOne,
    params.amountSpecified,
    params.sqrtPriceLimitX96
))
```
and then it does  k = h mod 10_000 and then if k <= 7999 it gets charged 18% but if k >= 9000 it gets 0%. As an example this executes from that pool with 18% fees https://basescan.org/tx/0xe94212cf3972d35e86dd51c9825bf96ee6286b4e903a909e1e89a00f3bb8fa78 and it sells NVDA for ETH sets the sqrtPriceLimitX96 price at 3.40256787 * 10^48 NVDA per ETH (-> infinite slippage). If it had set the worst price as 3.402567868363881 * 10^48 it would get 0% fee charge. Also given prevrandao comes from L1 on Base, most of the time exact hash can be computed off chain and aggregator can search for optimal sqrt price which will route with 0% fees. But this can be done on chain as well relatively cheaply. This is specific for the hook in the tweet but bunch of similar hooks exists i think. (e
