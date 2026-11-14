# Runbook: release to the public repo

## Purpose

Move finished worker branch work onto main. A release is a merge, not a deploy. There is no deployment step in this runbook.

## State of release tooling

No git remote and no tags are configured on main at 7ef6012. The worker never merges to main and never pushes. The manager merges one branch at a time after rebase, per ADR 0001.

## Pre-merge checklist

The worker confirms each item before handing the branch to the manager:

- The branch touches only the worker subtree. For this worker that is docs/platform/.
- The area tests pass in the worktree, with the command and result recorded in the status log.
- The unslop check passes: no emoji, no exclamation marks, no hype words, no unverifiable claims in docs, README text, CLI output or commit messages.
- The status log carries a DONE line with the branch, the commit hash, the commands run and their results.
- Commits are small, styled as area and change, with no Co-Authored-By, no Generated with and no tool or agent names anywhere in the repo.
- Synthetic data only. No credentials, no real company or personal data, no scraped content.

## Merge steps

1. The worker rebases the branch onto current main and resolves conflicts inside the own subtree only. A conflict outside the own subtree goes to the manager.
2. The worker reruns the area tests after the rebase and records the result.
3. The manager merges the branch into main, one branch at a time, and confirms the merge commit on main.
4. The manager verifies main after the merge: the merge commit is present in git log, and the affected area tests pass on main.
5. The worker worktree and branch stay in place until the manager confirms the merge. Deleting either before that point removes the only copy of the work.

## If the merge fails

Stop and read the incident response runbook for a bad merge. Do not merge a second branch while the first is unresolved, and do not force-push or reset main.

## After the release

The manager records the merge commit hash in the status log. The next worker rebases its branch onto the new main before continuing, so work always starts from the latest merged state.
