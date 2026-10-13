---
name: foundry-poc
description: "Build forge PoCs that prove exploit impact on a pinned fork block. Use when turning a vulnerability hypothesis into a runnable, green reproduction — or when a repro must be made bulletproof for a bounty submission."
---

# Foundry PoC Playbook (green-or-it-didn't-happen)

## The rule
A finding exists only when `forge test` is GREEN and the test asserts the actual impact
(funds moved / invariant broken / legit path reverts) — on a **pinned fork block**.
No green output = no finding. Every artifact ships with `reproduce.sh`.

## 0. SANDBOX NETWORK REALITY (Tier-1 — read before §2)
The sandbox's internet = GitHub/PyPI only. **`cast --rpc-url` and `forge --fork-url` FAIL inside the
sandbox** (connection reset) — do not burn cycles retrying. Split the workflow:
- **In-sandbox (works):** source analysis, blockscout MCP calls (server-side — live chain data, ABIs,
  txs, balances), writing + compiling the test (`forge build`; solc from the 8 pre-installed versions).
- **Fork execution (local rig):** deliver the test file + ONE exact command
  (`forge test --fork-url <RPC> --fork-block-number <N> --match-test <name> -vvv`, N pinned from the
  blockscout latest block) and tag the packet `FORK-PENDING-LOCAL`. The operator runs it on the local
  rig (full RPC) and returns raw output. That output is the round-trip evidence.
- If a boot test ever shows RPC reachable again (tier upgraded), delete this section and fork normally.

## 1. Project bootstrap (fresh sandbox)
```bash
forge init poc && cd poc
# if a bare repo: create foundry.toml + src/ + test/ manually
```
`foundry.toml` baseline:
```toml
[profile.default]
src = "src"; test = "test"; out = "out"; libs = ["lib"]
optimizer = true; optimizer_runs = 200
remappings = ["forge-std/=lib/forge-std/src/", "ds-test/=lib/forge-std/lib/ds-test/src/"]
[rpc_endpoints]
mainnet = "${ETH_RPC_URL}"
```
If forge-std missing: `git clone --depth 1 https://github.com/foundry-rs/forge-std lib/forge-std`.
**Compiler pin (required — solc autodownload is blocked in-sandbox):** `cp /opt/hunt-cache/poc-template/foundry.toml .`
— it sets `solc = "/usr/local/bin/solc"` (0.8.28 via solc-select). Different pragma: `solc-select use 0.8.19` first — the same path then serves that version. If your project already has a foundry.toml, just add the `solc` line.

## 2. Pin the fork (always)
```bash
forge test --fork-url $RPC --fork-block-number <N> -vvv
```
- Record `N` in the test file header AND in the report. Never rely on "latest".
- Verify the fork works first on the LOCAL RIG: `cast block-number --rpc-url $RPC` (§0 — not in-sandbox).
- Free RPCs: ethereum-rpc.publicnode.com · base-rpc.publicnode.com · bsc-rpc.publicnode.com ·
  rpc.gnosischain.com · eth.drpc.org · solana-rpc.publicnode.com (solana = different toolchain).

## 3. Cheatcode cookbook (the 12 that matter)
```solidity
vm.createSelectFork(RPC, BLOCK);                 // or via CLI flag
vm.deal(alice, 100 ether);                       // ETH to anyone
deal(token, alice, 1e24);                        // ERC20 (forge-std)
vm.prank(alice); / vm.startPrank(alice, alice);  // msg.sender (2nd arg = tx.origin)
vm.warp(block.timestamp + 7 days);               // time travel (cooldowns, windows)
vm.roll(block.number + 100);
vm.expectRevert(bytes4(0x...)); / expectRevert("msg");
vm.expectEmit(true,true,false,true, addr); emit TargetEvent(...);   // BEFORE the call
vm.load(addr, bytes32(slot)); / vm.store(addr, slot, value);        // raw state surgery
uint256 s = stdstore.target(tok).sig("balanceOf(address)").with_key(alice).find();
vm.snapshot(); / vm.revertTo(id);                // multi-scenario tests
vm.label(addr, "Vault");                          // traces readable
```

## 4. The five attack patterns (reuse these skeletons)
1. **Flash-loan funded:** `vm.deal` or flash-mint → attack → assert profit > 0 in one tx.
2. **Reentrancy:** attacker contract with `receive()`/callback re-entering; assert drained balance.
3. **Oracle manipulation:** mock or manipulate the price source within the tx; assert mispricing.
4. **Access-control probe:** `vm.prank(randomUser)` on every privileged entry; assert success where it should revert.
5. **Invariant (stateful fuzz):** `invariant_*()` + a handler contract that calls only the protocol's own functions; run `forge test --match-test invariant -vv`. Broken invariant = the bug; shrink with `--fuzz-seed`.

## 5. Negative control (mandatory)
The same test must NOT demonstrate impact when the vulnerability is absent (original/fixed code).
Options: (a) run against a block BEFORE the vulnerable deploy; (b) patch the single line in a copied
source and show impact disappears; (c) for fix-seam findings: deployed (vulnerable) vs repo (fixed).
Document the control's output too — triagers trust findings that show they can fail.

## 6. reproduce.sh template
```bash
#!/usr/bin/env bash
set -e
# ONE command to reproduce — pin everything
forge test --fork-url https://ethereum-rpc.publicnode.com --fork-block-number 26165833 \
  --match-test test_exploit -vvv | tee repro-output.txt
# expected: [PASS] test_exploit — see repro-output.txt for raw run
```

## 7. Submission-grade hygiene
- Title = vulnerability + impact. Impact section = the program's own impact title, verbatim.
- Attach: test file, raw output, pinned block, RPC used, and the negative control output.
- State the funds-at-risk number and how you derived it.
- If the fix is merged but undeployed: say so — the deployed build is the vulnerable one.
- Never claim more severity than the impact shown by the green test.

## 8. When forge fights you (fallbacks)
- Remappings broken → set them explicitly in foundry.toml (see §1); never fight the compiler.
- A dependency won't compile → pin solc (`foundry.toml` `solc = "0.8.x"`); try `--use <path-to-solc>`.
- Fork RPC flaky → retry with a second RPC; record which one produced the output.
- Still blocked → fall back to a raw `cast` call sequence that demonstrates the same state change,
  and document exactly why forge was unusable. A cast sequence is a weaker but valid artifact.

## RPC PRESETS (fork tests — no keys needed)
The sandbox bakes keyless public RPCs for 12 chains at `/opt/hunt-cache/rpcs.json` (2+ endpoints each).
Pick a chain, take the first endpoint, fall back to the second on flake:

```bash
RPC=$(python3 -c "import json;print(json.load(open('/opt/hunt-cache/rpcs.json'))['base'][0])")
forge test --match-test test_exploit -vvv --fork-url "$RPC" --fork-block-number <recent-block>
# cast fallback:
cast call <addr> "fn()" --rpc-url "$RPC"
```

Chains: ethereum, arbitrum, base, optimism, polygon, bsc, avalanche, gnosis, scroll, linea, blast, mantle.
Public RPCs serve RECENT blocks well (fresh-deploy targets = perfect). For deep archive needs, note it in the candidate and use blockscout MCP source/state instead.
