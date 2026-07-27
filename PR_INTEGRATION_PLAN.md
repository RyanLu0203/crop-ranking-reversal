# Pull-request integration plan — Issue #36

## Dependency chain

The repair branch starts exactly at Issue #34 commit
`12fe6b4a3717ef5602b3d31558fd66424287f7d4`. That commit descends from:

- PR #35 / Issue #34 reconstruction;
- commit `1262b19150fd1e63f549d3511ba478b003b08d9e`, the PR #33 head;
- the complete GOAL-16 and GOAL-17 dependency history.

Both ancestry checks pass with `git merge-base --is-ancestor`.

## Selected strategy

Open the Issue #36 Draft PR directly against `main`. Its diff intentionally
contains the stacked GOAL-16, GOAL-17, Issue #34 and Issue #36 work so no
required official-data, theory, figure or reproducibility asset is omitted.
The full repository gates validate that combined history.

PR #33 and PR #35 remain open Drafts and are not merged. The new direct-to-main
Draft supersedes them as the proposed integration vehicle after review. They
remain useful as review checkpoints until maintainers decide whether to close
them.

## Safe reviewer sequence

1. Review PR #33 as historical GOAL-17 context only.
2. Review PR #35 as the Issue #34 reconstruction checkpoint.
3. Review the new Issue #36 Draft against `main` as the complete integration
   diff, with special attention to its final repair commits.
4. Merge nothing automatically. After approvals, maintainers may merge only
   the direct-to-main PR and close the older Drafts as superseded.

This avoids double-merging stacked commits and provides one complete,
reviewable path to `main`.
