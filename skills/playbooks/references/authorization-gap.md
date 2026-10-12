# PLAYBOOK: authorization-gap (missing / incorrect authorization)

CLASS: A state-changing or value-moving path reachable by the wrong principal: unguarded admin fn, wrong origin check, role confusion, signature replay/no-nonce, cross-chain origin spoof (XCM/CCIP/LayerZero/Wormhole sender checks), upgrade/initializer exposure.

ARCHETYPES: pallets/contracts with privileged setters, proxy/initializer patterns, cross-chain receivers, signature-gated actions (permits, meta-tx), role systems.

## DETECT (in order)
1. Enumerate every state-changing external fn. Mark which ones MOVE VALUE or CHANGE CONFIG (oracle, fee, owner, pause, mint, upgrade).
2. For each, find the guard: `ensure_signed` vs `ensure_root`/`ensure_origin`, `onlyOwner`, role checks, capability checks. Missing guard = instant lead.
3. WRONG guard: origin conversions (`ConvertOrigin`, `LocationToAccountId`, `ensure_origin` with weak variants), `Caller`→AccountId conversions that default to a common account, relayed messages without sender validation.
4. Signature paths: nonce/chainId/domain separation present? Replayable across chains/contracts? ecrecover vs smart-wallet mismatches?
5. Initializer/proxy: can `initialize()` be called by anyone post-deploy, or front-run the deployer?

## EXPLOIT RECIPE
- Call the unguarded/wrongly-guarded fn as an unprivileged account. If value moves: route it to yourself. If config changes: set oracle/fee/owner to attacker-controlled values, then exploit downstream (e.g. set fee→0, oracle→self, pause→on).
- For cross-chain: craft the message with spoofed origin (direct call if receiver is a contract; via the real bridge's remote-execution path if permissioned).

## POC SHAPE
1. Fork test. 2. Attacker EOA (no roles). 3. Call the path; assert privileged state changed / value moved. 4. For oracle/config takeovers: chain a second call showing profit or protocol breakage (impact, not just "state changed"). 5. Negative control: fixed build reverts.

## REAL CASES
- (fleet) Class ranked TIER 1 in fast-criticals: unguarded/first-guard checks are the single fastest-to-prove critical family on fresh deploys.
- Public pattern references: cross-chain origin conversion bugs (bridge receivers accepting spoofed senders), initializer front-running on fresh proxy deploys, permit replay without nonce.

## KILL SIGNALS
- Guard exists AND caller must be a genuinely privileged key you don't control (check multisig/DAO thresholds — "owner is a contract" often means timelock → delay makes it low).
- State change has no downstream value or breakage (pure griefing under program's own severity bar).
- Cross-chain sender is validated against the canonical bridge module (not user-supplied).
