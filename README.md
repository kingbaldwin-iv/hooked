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
