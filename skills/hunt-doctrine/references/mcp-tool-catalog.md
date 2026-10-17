# MCP TOOL CATALOG — the real tool names (read before calling any MCP tool)

WHY THIS FILE EXISTS: the fleet recorded **38 failures** of the form
`Access denied: tool 'search' is not enabled on server 'exasearch'`. The servers were fine — the
agents invented tool names. `Access denied: tool '<X>' is not enabled on server '<Y>'` means
**X does not exist on Y**. It does NOT mean quota, payment or permissions. Before calling a tool,
check its real name here. If a name is not listed, it does not exist.

## If you are unsure of a tool's name

Do not guess and do not retry variations. Use the discovery endpoints instead:
- list the servers and their tools: `GET /api/v1/mcp-servers` , `GET /api/v1/mcp-servers/<name>/tools`
A name-guess costs a turn and pollutes the failure ledger with a fake "MCP is broken" signal.

## The servers and their REAL tools

**exasearch** (3) — `web_search_exa` , `web_fetch_exa` , `agent_run`
  ⚠ Do NOT call `search`, `exa_search`, `search_exa` — they do not exist. Web search here is
  `web_search_exa`.

**parallel-web** (2) — `web_search` , `web_fetch`
  ⚠ There are TWO search servers with DIFFERENT names. If you want a plain web search use
  `parallel-web.web_search`. Do not assume the name carries across servers.

**blockscout** (16+) — `get_block_info` , `get_block_number` , `get_address_by_ens_name` ,
  `get_transactions_by_address` , `get_token_transfers_by_address` , `lookup_token_by_symbol` ,
  `get_contract_abi` , `inspect_contract_code` , `read_contract` , `get_address_info` ,
  `get_tokens_by_address` , `nft_tokens_by_address` , `get_transaction_info`
  (call the tools endpoint for the full list; names change as the server updates)

**github** (46) — read-side includes `get_file_contents` , `get_commit` , `get_latest_release` ,
  `get_me` ; write-side includes `create_or_update_file` , `create_branch` , `create_pull_request` ,
  `add_issue_comment`. Write/destructive tools may return `Access denied` when the agent's config
  lists them under `require_approval_for_tools` — that is an approval gate, not a quota.

**fork-ops** (8) — `fork_run` , `local_worker` , `fork_status` , `fork_jobs` , `fork_cleanup` ,
  `cleanup_sandboxes` , `forge_poc_run` , `dupe_precheck`
  ⚠ This is the PROOF PATH. `forge_poc_run` runs a Foundry PoC; `dupe_precheck` checks a lead
  against public sources before a PoC is written. Route blocked RPC/fork/solc work here instead of
  trying it in the sandbox.

**deepwiki** (3) — `ask_wiki_question` , `read_wiki_contents` , `read_wiki_structure`

## READING A FAILURE CORRECTLY (this matters for the ledger)

- `tool '<X>' is not enabled on server '<Y>'` → WRONG TOOL NAME. Your fault. Fix the call.
- `NATS bridge setup failed` → you used CODE-MODE MCP. Use native tool calls instead; the bridge is
  an optional path and it is the single largest recorded error class. Doctrine §20.
- `Access denied` on a `@write`/`@destructive` github tool → approval gate, not quota.
- Only after ruling out all three should you record an environment fault — and record which one
  you ruled out, because a misfiled fault becomes a false "the machine is broken" belief that
  later runs act on.
