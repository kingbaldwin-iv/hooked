#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "matplotlib",
#   "tqdm",
# ]
# ///

import json
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock, Thread

import matplotlib.pyplot as plt
import tqdm

BASE_RPC_URL = ""
FORK_BLOCK = 50_401_381
TARGET_TIMESTAMP = 1_787_592_111
TARGET_PREVRANDAO = (
    "0xe5e6271b9492284695247d190a3da8dee871f79dbdc9e03375f98dbc6f1807b9"
)
TARGET_BASE_FEE = 5_000_000
TARGET_GAS_LIMIT = 400_000_000
TARGET_COINBASE = "0x4200000000000000000000000000000000000011"

EOA = "0x4bbdc70d780980bccbc3c8cc348c92ce1e1f8e01"
DO_ONE_THING = "0xA9595eF01554fF0DE2ba6b5dc23E05a670C371f3"
DO_ONE_THING_SELECTOR = "0x9dd0b032"
DEFAULT_SQRT_PRICE_LIMIT_X96 = (
    1_461_446_703_485_210_103_287_273_052_203_988_822_378_723_970_341
)
POOL_MANAGER = "0x498581fF718922c3f8e6A244956aF099B2652b2b"
SWAP_TOPIC = "0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"

# The canonical Base deposit transaction at index 0 of block 50,401,382.
SYSTEM_TRANSACTION = (
    "0x7ef90106a0f7c95944672f72e31ce06a5c4c46557d4fd4163d4b77455fdf09ef5145e4966"
    "294deaddeaddeaddeaddeaddeaddeaddeaddead000194420000000000000000000000000000000"
    "00000158080830f424080b8b23db6be2b000008dd00101c120000000000000005000000006a8c"
    "7d6f00000000018a14c100000000000000000000000000000000000000000000000000000001"
    "48b44d7b00000000000000000000000000000000000000000000000000000000105a1b6076a9"
    "22ba7a2d7a24b78e04f20b2349f94b59f18ab3e746ee2e3ba16999717a8d0000000000000000"
    "000000005050f69a9786f081509234f1a7f4684b5e5b76c90000000000000000000000000094"
)

# Runtime bytecode compiled from src/do_one_thing.sol. It is embedded so this
# script never needs to read the Solidity source or invoke Forge.
DO_ONE_THING_RUNTIME = (
    "0x608060405234801561000f575f80fd5b5060043610610034575f3560e01c806391dd7346146100"
    "385780639dd0b03214610061575b5f80fd5b61004b610046366004610478565b610076565b604051"
    "6100589190610514565b60405180910390f35b61007461006f366004610544565b6103d5565b005b"
    "60605f806100868486018661055f565b6040805160a0810182525f8082526878ee7ce2fe4908108c"
    "605960991b016020808401919091526280000083850152600260608085019190915273800cef53c3"
    "fd41109dffec62e5251bdd7acba5c760808501528451908101909452818452949650929450928101"
    "6100fb63471618db610596565b81526001600160a01b038516602091820152604080519182018152"
    "5f8083529051633cf3645360e21b81529293509173498581ff718922c3f8e6a244956af099b2652b"
    "2b9163f3cd914c916101579187918791906004016105bc565b6020604051808303815f875af11580"
    "15610173573d5f803e3d5ffd5b505050506040513d601f19601f8201168201806040525081019061"
    "0197919061063b565b90505f6101a482600f0b90565b600f0b6101b090610596565b90505f6101bd"
    "8360801d90565b604051632961046560e21b81526878ee7ce2fe4908108c605960991b0160048201"
    "819052600f9290920b925073498581ff718922c3f8e6a244956af099b2652b2b9063a58411949060"
    "24015f604051808303815f87803b15801561021f575f80fd5b505af1158015610231573d5f803e3d"
    "5ffd5b50506040516323b872dd60e01b81526001600160a01b038b16600482015273498581ff7189"
    "22c3f8e6a244956af099b2652b2b6024820152604481018690526878ee7ce2fe4908108c60596099"
    "1b0192506323b872dd91506064016020604051808303815f875af11580156102a8573d5f803e3d5f"
    "fd5b505050506040513d601f19601f820116820180604052508101906102cc9190610652565b5073"
    "498581ff718922c3f8e6a244956af099b2652b2b6001600160a01b03166311da60b46040518163ff"
    "ffffff1660e01b81526004016020604051808303815f875af115801561031e573d5f803e3d5ffd5b"
    "505050506040513d601f19601f82011682018060405250810190610342919061063b565b50604051"
    "630b0d9c0960e01b81525f60048201526001600160a01b0389166024820152604481018390527349"
    "8581ff718922c3f8e6a244956af099b2652b2b90630b0d9c09906064015f604051808303815f8780"
    "3b1580156103a2575f80fd5b505af11580156103b4573d5f803e3d5ffd5b50506040805160208101"
    "9091525f81529d9c50505050505050505050505050565b604080513360208201526001600160a01b"
    "0383168183015281518082038301815260608201928390526348c8949160e01b90925273498581ff"
    "718922c3f8e6a244956af099b2652b2b916348c89491916104329190606401610514565b5f604051"
    "808303815f875af115801561044d573d5f803e3d5ffd5b505050506040513d5f823e601f3d908101"
    "601f191682016040526104749190810190610685565b5050565b5f8060208385031215610489575f"
    "80fd5b823567ffffffffffffffff81111561049f575f80fd5b8301601f810185136104af575f80fd"
    "5b803567ffffffffffffffff8111156104c5575f80fd5b8560208284010111156104d6575f80fd5b"
    "6020919091019590945092505050565b5f81518084528060208401602086015e5f60208286010152"
    "6020601f19601f83011685010191505092915050565b602081525f61052660208301846104e6565b"
    "9392505050565b6001600160a01b0381168114610541575f80fd5b50565b5f602082840312156105"
    "54575f80fd5b81356105268161052d565b5f8060408385031215610570575f80fd5b823561057b81"
    "61052d565b9150602083013561058b8161052d565b809150509250929050565b5f600160ff1b8201"
    "6105b657634e487b7160e01b5f52601160045260245ffd5b505f0390565b83516001600160a01b03"
    "908116825260208086015182168184015260408087015162ffffff16818501526060808801516002"
    "0b908501526080808801518416908501528551151560a08501529085015160c08401528401511660"
    "e08201526101206101008201525f6106326101208301846104e6565b95945050505050565b5f6020"
    "828403121561064b575f80fd5b5051919050565b5f60208284031215610662575f80fd5b81518015"
    "158114610526575f80fd5b634e487b7160e01b5f52604160045260245ffd5b5f6020828403121561"
    "0695575f80fd5b815167ffffffffffffffff8111156106ab575f80fd5b8201601f810184136106bb"
    "575f80fd5b805167ffffffffffffffff8111156106d5576106d5610671565b604051601f8201601f"
    "19908116603f0116810167ffffffffffffffff8111828210171561070457610704610671565b6040"
    "5281815282820160200186101561071b575f80fd5b8160208401602083015e5f9181016020019190"
    "915294935050505056fea2646970667358221220a685df68ebc9766d36803c6f635b32fd01248bc2"
    "35485a29d47de6497d06935364736f6c634300081a0033"
)


def rpc(url: str, method: str, params: list[object]) -> object:
    request = urllib.request.Request(
        url,
        data=json.dumps(
            {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        ).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        message = json.load(response)
    if "error" in message:
        raise RuntimeError(f"{method}: {message['error']}")
    return message["result"]


def unused_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def start_fork_rpc_cache() -> tuple[ThreadingHTTPServer, Thread, str]:
    cache = {}
    cache_lock = Lock()
    request_locks = {}

    class ForkRpcCache(BaseHTTPRequestHandler):
        def do_POST(self):
            size = int(self.headers["Content-Length"])
            body = self.rfile.read(size)
            message = json.loads(body)
            calls = message if isinstance(message, list) else [message]
            keys = [
                json.dumps(
                    [call["method"], call.get("params", [])],
                    sort_keys=True,
                    separators=(",", ":"),
                )
                for call in calls
            ]

            def response_from_cache():
                with cache_lock:
                    cached = [cache.get(key) for key in keys]
                if not all(response is not None for response in cached):
                    return None
                responses = [
                    {"id": call.get("id"), **response}
                    for call, response in zip(calls, cached, strict=True)
                ]
                return json.dumps(
                    responses if isinstance(message, list) else responses[0]
                ).encode()

            response_body = response_from_cache()
            if response_body is None:
                # Coalesce identical cold requests from the Anvil workers, while
                # still allowing different RPC reads to run concurrently.
                request_key = tuple(keys)
                with cache_lock:
                    request_lock = request_locks.setdefault(request_key, Lock())
                with request_lock:
                    response_body = response_from_cache()
                    if response_body is None:
                        upstream_request = urllib.request.Request(
                            BASE_RPC_URL,
                            data=body,
                            headers={"Content-Type": "application/json"},
                        )
                        for attempt in range(5):
                            try:
                                with urllib.request.urlopen(
                                    upstream_request,
                                    timeout=60,
                                ) as upstream:
                                    response_body = upstream.read()
                                break
                            except OSError:
                                if attempt == 4:
                                    self.send_error(502, "Upstream RPC unavailable")
                                    return
                                time.sleep(0.25 * 2**attempt)

                        upstream_message = json.loads(response_body)
                        upstream_responses = (
                            upstream_message
                            if isinstance(upstream_message, list)
                            else [upstream_message]
                        )
                        responses_by_id = {
                            json.dumps(response.get("id"), sort_keys=True): response
                            for response in upstream_responses
                        }
                        with cache_lock:
                            for call, key in zip(calls, keys, strict=True):
                                response = responses_by_id.get(
                                    json.dumps(call.get("id"), sort_keys=True)
                                )
                                if response is not None:
                                    cache[key] = {
                                        name: value
                                        for name, value in response.items()
                                        if name != "id"
                                    }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_body)))
            self.end_headers()
            try:
                self.wfile.write(response_body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, *_):
            pass

    class ForkRpcCacheServer(ThreadingHTTPServer):
        request_queue_size = 128
        daemon_threads = True

    server = ForkRpcCacheServer(("127.0.0.1", 0), ForkRpcCache)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, thread, f"http://{host}:{port}"


def start_anvil(fork_rpc: str = BASE_RPC_URL) -> tuple[subprocess.Popen[bytes], str]:
    binary = shutil.which("base-anvil-replay")
    if binary is None:
        raise RuntimeError("base-anvil-replay is not installed")

    local_rpc = f"http://127.0.0.1:{unused_port()}"
    port = local_rpc.rsplit(":", 1)[1]
    process = subprocess.Popen(
        [
            binary,
            "--base",
            "beryl",
            "--optimism",
            "--fork-url",
            fork_rpc,
            "--fork-block-number",
            str(FORK_BLOCK),
            "--no-rate-limit",
            "--no-storage-caching",
            "--chain-id",
            "8453",
            "--auto-impersonate",
            "--order",
            "fifo",
            "--port",
            port,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    for _ in range(120):
        if process.poll() is not None:
            stderr = process.stderr.read().decode(errors="replace").strip()
            raise RuntimeError(f"Anvil exited during startup: {stderr}")
        try:
            rpc(local_rpc, "eth_chainId", [])
            return process, local_rpc
        except Exception:
            time.sleep(0.25)

    process.terminate()
    raise RuntimeError("Anvil did not start")


def signed(value: int, bits: int) -> int:
    value &= (1 << bits) - 1
    return value - (1 << bits) if value >= 1 << (bits - 1) else value


def decode_swap(receipt: dict[str, object]) -> dict[str, object]:
    for log in receipt["logs"]:
        topics = log["topics"]
        if (
            log["address"].lower() == POOL_MANAGER.lower()
            and topics[0].lower() == SWAP_TOPIC
        ):
            data = log["data"][2:]
            words = [int(data[index : index + 64], 16) for index in range(0, len(data), 64)]
            return {
                "pool_id": topics[1],
                "sender": "0x" + topics[2][-40:],
                "amount0": signed(words[0], 128),
                "amount1": signed(words[1], 128),
                "sqrt_price_x96": words[2],
                "liquidity": words[3],
                "tick": signed(words[4], 24),
                "fee": words[5],
                "block_number": int(log["blockNumber"], 16),
                "transaction_index": int(log["transactionIndex"], 16),
                "transaction_hash": log["transactionHash"],
            }
    raise RuntimeError("PoolManager.Swap log not found")


def wait_for_receipt(local_rpc: str, transaction_hash: str) -> dict[str, object]:
    for _ in range(600):
        receipt = rpc(local_rpc, "eth_getTransactionReceipt", [transaction_hash])
        if receipt is not None:
            return receipt
        time.sleep(0.1)
    raise RuntimeError("Transaction receipt timed out")


def format_units(amount: int, decimals: int) -> str:
    whole, fraction = divmod(amount, 10**decimals)
    if fraction == 0:
        return str(whole)
    return f"{whole}.{fraction:0{decimals}d}".rstrip("0")


def execute_swap(local_rpc: str, sqrt_price_limit_x96: int) -> dict[str, object]:
    rpc(local_rpc, "evm_setAutomine", [False])
    rpc(local_rpc, "evm_setNextBlockTimestamp", [TARGET_TIMESTAMP])
    rpc(local_rpc, "anvil_setNextBlockPrevRandao", [TARGET_PREVRANDAO])
    rpc(local_rpc, "anvil_setNextBlockBaseFeePerGas", [hex(TARGET_BASE_FEE)])
    rpc(local_rpc, "anvil_setCoinbase", [TARGET_COINBASE])
    rpc(local_rpc, "evm_setBlockGasLimit", [hex(TARGET_GAS_LIMIT)])

    rpc(local_rpc, "eth_sendRawTransaction", [SYSTEM_TRANSACTION])
    transaction_hash = rpc(
        local_rpc,
        "eth_sendTransaction",
        [
            {
                "from": EOA,
                "to": DO_ONE_THING,
                "nonce": "0x24",
                "gas": "0x9611a",
                "gasPrice": "0xfad3f5f",
                "value": "0x0",
                "data": DO_ONE_THING_SELECTOR
                + sqrt_price_limit_x96.to_bytes(32, "big").hex(),
            }
        ],
    )
    rpc(local_rpc, "evm_setAutomine", [True])

    receipt = wait_for_receipt(local_rpc, transaction_hash)
    if int(receipt["status"], 16) != 1:
        raise RuntimeError("doOneThing reverted")

    swap = decode_swap(receipt)
    swap["sqrt_price_limit_x96_input"] = sqrt_price_limit_x96
    swap["NVDA_input"] = format_units(-swap["amount1"], 8)
    swap["ETH_output"] = format_units(swap["amount0"], 18)
    return swap


def replay_many(
    sqrt_price_limits_x96,
    on_result=None,
    fork_rpc: str = BASE_RPC_URL,
) -> list[dict[str, object]]:
    process, local_rpc = start_anvil(fork_rpc)
    try:
        rpc(local_rpc, "anvil_setCode", [DO_ONE_THING, DO_ONE_THING_RUNTIME])
        outputs = []
        for sqrt_price_limit_x96 in sqrt_price_limits_x96:
            snapshot = rpc(local_rpc, "evm_snapshot", [])
            try:
                outputs.append(execute_swap(local_rpc, sqrt_price_limit_x96))
                if on_result is not None:
                    on_result()
            finally:
                rpc(local_rpc, "evm_revert", [snapshot])
        return outputs
    finally:
        process.terminate()
        process.communicate(timeout=5)


def replay(
    sqrt_price_limit_x96: int = DEFAULT_SQRT_PRICE_LIMIT_X96,
) -> dict[str, object]:
    return replay_many([sqrt_price_limit_x96])[0]


def replay_parallel(
    sqrt_price_limits_x96: list[int],
    max_workers: int = 4,
) -> list[dict[str, object]]:
    if not sqrt_price_limits_x96:
        return []

    worker_count = min(max_workers, len(sqrt_price_limits_x96))
    chunk_size = (len(sqrt_price_limits_x96) + worker_count - 1) // worker_count
    chunks = [
        sqrt_price_limits_x96[index : index + chunk_size]
        for index in range(0, len(sqrt_price_limits_x96), chunk_size)
    ]

    cache_server, cache_thread, fork_rpc = start_fork_rpc_cache()
    try:
        with tqdm.tqdm(total=len(sqrt_price_limits_x96)) as progress:
            def replay_chunk(chunk):
                return replay_many(chunk, progress.update, fork_rpc)

            with ThreadPoolExecutor(max_workers=worker_count) as executor:
                output_chunks = executor.map(replay_chunk, chunks)
                return [output for chunk in output_chunks for output in chunk]
    finally:
        cache_server.shutdown()
        cache_server.server_close()
        cache_thread.join()


if __name__ == "__main__":
    limit = (
        int(sys.argv[1], 0)
        if len(sys.argv) > 1
        else DEFAULT_SQRT_PRICE_LIMIT_X96
    )
    x = []
    y = []

    limits = [limit - i for i in range(50)]
    outputs = replay_parallel(limits)
    for output in outputs:
        x.append(limit - output["sqrt_price_limit_x96_input"])
        y.append(float(output["ETH_output"]))

    figure, axes = plt.subplots()
    actual_transaction_x = limit - DEFAULT_SQRT_PRICE_LIMIT_X96
    axes.axvline(
        actual_transaction_x,
        color="red",
        linestyle="--",
        label="Actual on-chain transaction",
        zorder=1,
    )
    axes.step(
        x,
        y,
        where="mid",
        color="tab:blue",
        linewidth=1.5,
        label="ETH output",
        zorder=2,
    )
    axes.scatter(x, y, color="tab:blue", s=20, zorder=3)
    axes.set_ylabel("ETH output")
    axes.set_xlabel("sqrtPriceLimitX96 decrease (0 = starting limit)")
    x_ticks = list(range(0, len(limits), 5))
    if x_ticks[-1] != len(limits) - 1:
        x_ticks.append(len(limits) - 1)
    axes.set_xticks(x_ticks)
    axes.ticklabel_format(axis="y", style="plain", useOffset=False)
    axes.grid(alpha=0.25)
    axes.legend()
    figure.tight_layout()
    figure.savefig("execution.png", dpi=1000, bbox_inches="tight")
    plt.show()
