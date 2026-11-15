# ADR 0009: Token ledger

## Status

Proposed

## Context

No token ledger code exists on main at 7ef6012, and services/ai does not exist on main. A FastAPI AI assistant service exists on an unmerged branch at 0e95267, with a persisted ledger and a 402 response at zero balance for AI calls. The ledger fields are not pinned in the data dictionary yet, and no token pricing is recorded anywhere in the repo.

## Decision

Proposed. A token ledger records each account balance and each charge for an AI call, and an AI call checks the balance first and returns 402 at zero balance. The ledger persists between calls. The shape stays proposed until the service is merged and its fields are recorded in the data dictionary.

## Consequences

- Spending is bounded by balance, and a zero balance fails with 402 instead of serving on credit.
- The ledger is the only record of charges, so a lost ledger means lost billing history, and its persistence must be tested.
- No price per call is set, so no cost figure can be quoted until the pack and pricing fields are pinned.
- The service on the unmerged branch runs in stub mode with a fallback when serving is unreachable, so ledger charges must be labelled by serving mode.
