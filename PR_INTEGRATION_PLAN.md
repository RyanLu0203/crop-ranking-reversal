# Pull-request integration plan — Issue #38

## Dependency chain

The finalization branch starts exactly at Issue #36 commit
`d058f0764e42e994bf2c1c00b48cbde3622f96c6`. That commit descends from:

- PR #37 / Issue #36 scientific repair;
- PR #35 / Issue #34 reconstruction;
- commit `1262b19150fd1e63f549d3511ba478b003b08d9e`, the PR #33 head;
- the complete GOAL-16 and GOAL-17 dependency history.

Both ancestry checks pass with `git merge-base --is-ancestor`.

## Selected strategy

Open the Issue #38 Draft PR directly against `main`. Its diff intentionally
contains the stacked GOAL-16, GOAL-17, Issue #34, Issue #36 and Issue #38 work so no
required official-data, theory, figure or reproducibility asset is omitted.
The full repository gates validate that combined history.

PR #33 and PR #35 remain historical Drafts and are not merged. PR #37 also
remains an unmerged historical Draft until the Issue #38 candidate is accepted
or explicitly superseded. The new direct-to-main Draft is the proposed
integration vehicle after review.

## Safe reviewer sequence

1. Review PR #33 as historical GOAL-17 context only.
2. Review PR #35 as the Issue #34 reconstruction checkpoint.
3. Review PR #37 as the Issue #36 repair checkpoint.
4. Review the new Issue #38 Draft against `main` as the complete integration
   diff, with special attention to the finalization commit.
5. Merge nothing automatically. After approvals, maintainers may merge only
   the direct-to-main PR and close the older Drafts as superseded.

This avoids double-merging stacked commits and provides one complete,
reviewable path to `main`.
