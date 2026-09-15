// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {IUnlockCallback} from "@uniswap/v4-core/src/interfaces/callback/IUnlockCallback.sol";
import {IHooks} from "@uniswap/v4-core/src/interfaces/IHooks.sol";
import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {SwapParams} from "@uniswap/v4-core/src/types/PoolOperation.sol";
import {BalanceDelta} from "@uniswap/v4-core/src/types/BalanceDelta.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {IERC20Minimal} from "@uniswap/v4-core/src/interfaces/external/IERC20Minimal.sol";

/// @notice Reproduces one specific historical NVDAc -> ETH v4 swap.
/// @dev Intended only for local Anvil state injection at the original router address.
contract DoOneThing is IUnlockCallback {
    IPoolManager private constant POOL_MANAGER =
        IPoolManager(0x498581fF718922c3f8e6A244956aF099B2652b2b);
    address private constant NVDA_TOKEN =
        0xb20000000000000000000078ee7ce2fE4908108C;
    IHooks private constant HOOK =
        IHooks(0x800CEF53c3Fd41109dFfeC62E5251BDD7Acba5c7);

    uint128 private constant AMOUNT_IN = 1_192_630_491;

    /// @notice Execute the swap, paying from and sending ETH to the caller.
    function doOneThing(uint160 sqrtPriceLimitX96) external {
        POOL_MANAGER.unlock(abi.encode(msg.sender, sqrtPriceLimitX96));
    }

    /// @inheritdoc IUnlockCallback
    function unlockCallback(bytes calldata data) external returns (bytes memory) {
        (address payer, uint160 sqrtPriceLimitX96) =
            abi.decode(data, (address, uint160));

        PoolKey memory key = PoolKey({
            currency0: Currency.wrap(address(0)),
            currency1: Currency.wrap(NVDA_TOKEN),
            fee: 0x800000,
            tickSpacing: 2,
            hooks: HOOK
        });
        SwapParams memory params = SwapParams({
            zeroForOne: false,
            amountSpecified: -int256(uint256(AMOUNT_IN)),
            sqrtPriceLimitX96: sqrtPriceLimitX96
        });

        BalanceDelta delta = POOL_MANAGER.swap(key, params, bytes(""));
        uint256 amountIn = uint256(-int256(delta.amount1()));
        uint256 amountOut = uint256(int256(delta.amount0()));

        Currency inputCurrency = Currency.wrap(NVDA_TOKEN);
        POOL_MANAGER.sync(inputCurrency);
        IERC20Minimal(NVDA_TOKEN).transferFrom(payer, address(POOL_MANAGER), amountIn);
        POOL_MANAGER.settle();
        POOL_MANAGER.take(Currency.wrap(address(0)), payer, amountOut);

        return "";
    }
}
