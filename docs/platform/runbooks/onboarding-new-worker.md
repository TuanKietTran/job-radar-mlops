# Runbook: onboarding a new worker

## Purpose

Bring a new worker from a fresh checkout to its first small commit, following the same working pattern every worker uses.

## Read the briefs first

Read in this order, in full, before touching the repo:

1. briefs/common.md
2. briefs/x2-common.md
3. briefs/unslop.md
4. The worker brief for the assigned track and wave.

The briefs carry the working rules. The unslop brief applies to all docs, README text, CLI output and commit messages: no emoji, no exclamation marks, no hype words, no unverifiable claims.

## Set up the worktree

```
git worktree add wt/<worker-name> -b <branch-name> main
```

Work only in that worktree, and only in the assigned subtree. Never touch another worker subtree, services, web, tests, ops, Makefile, docker-compose.yml, .github, README.md or mlops outside the assignment. Never merge to main and never push.

## Working pattern

- Keep the shared todo queue current. The human orders it. Start the first unfinished item, mark it done right after, and add follow-ups when they appear. One-step requests stay out of the queue.
- Keep the handoff current with the goal, decisions, files, verification and next steps, so another session can continue without re-asking.
- Append one line per event to the status log at status/<worker-name>.log, and finish with a DONE line carrying the branch, the commit hash, the commands run and their results.
- Small commits on the branch, styled as area and change. No Co-Authored-By, no Generated with and no tool or agent names anywhere in the repo.
- Synthetic data only. Zero credentials, no scraping real sites, no real company or personal data, no copied content or branding.
- Base every decision on the code and briefs actually in the repo. Mark anything not yet built as proposed, not decided.
- Do not end a turn while the worker tests are still running.

## First tasks

1. Inspect the repo structure, the fixtures and the brief for any neighbouring worker the assignment depends on.
2. Confirm the assigned subtree exists and the branch is clean.
3. Make the first small change in the assigned subtree, run the area tests and record the result in the status log.

## Where to get help

The manager is mz-managers-1. A question about the assignment goes to the manager with the brief section it concerns and the file it touches. A question about another worker subtree goes to that worker owner, not to a file edit in their subtree.
