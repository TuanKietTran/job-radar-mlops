# Runbook: incident response for a bad merge

## Purpose

Recover main after a merge that breaks tests, brings in the wrong subtree or merges the wrong branch. The goal is a working main, with a record of what happened.

## First steps

1. Stop. Do not merge a second branch and do not push while the incident is open.
2. Identify the merge commit with git log --oneline --merges, and list what it touched with git show --stat on that commit.
3. Identify the scope: which subtree changed, which area tests fail, and whether main still starts. Run the failing area tests from the verify failure triage runbook and keep the output.
4. Tell the manager, mz-managers-1, with the merge commit hash, the scope and the failing test output. Do not wait for a fix to report the incident.

## Choose the recovery

Revert the merge when the merge breaks main tests, brings in the wrong subtree or merges the wrong branch. A revert is the default, because it restores main in one recorded commit.

```
git revert -m 1 <merge-commit>
```

The -m 1 flag keeps the main side of the merge and reverts the branch side. After the revert, rerun the affected area tests on main and record the result in the status log.

Fix forward only when the break is a small, understood defect in the merged work, the fix touches the owning subtree only, and the fix can be tested before it lands. A fix-forward commit carries a message naming the merge it repairs and the test that proves the repair.

## What not to do

- Do not force-push main. Main is shared, and a force-push can drop other merged work.
- Do not reset main to an earlier commit. A revert is the recovery that keeps history readable.
- Do not reopen the reverted branch against main without a fix. The branch owner reworks it from the reverted state and hands it back through the release checklist.
- Do not hide the incident. The status log records the merge, the failure, the recovery and the test result.

## After recovery

1. Confirm main is green with the affected area tests.
2. Record the incident in the status log: merge commit, failure, recovery chosen, test result after recovery.
3. The branch owner reworks the branch, reruns its tests and returns it through the release runbook. The manager merges it only after that second pass.
