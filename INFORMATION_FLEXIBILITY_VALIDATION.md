# Information--flexibility validation — Issue #36

## Model and theorem scope

The numerical programme uses two signal-contingent acreage vectors, one VaR
variable and one combined set of excess variables. Both actions therefore
share one ex-ante loss-CVaR budget.

The strict theorem is restricted to a posterior-separable model or a
nonbinding shared-risk submodel. No posterior-optimum strictness argument is
used for the binding coupled programme.

## Numerical definition

For adjacent \(q_1<q_2\), \(\phi_1<\phi_2\),
\[
\Delta_{q,\phi}V=
[V(q_2,\phi_2)-V(q_1,\phi_2)]
-[V(q_2,\phi_1)-V(q_1,\phi_1)].
\]
The registered sign tolerance is \(10^{-7}\). Zero information has precedence
as a separate classification; grid edges and numerical zero
cross-differences are `zero_or_boundary`.

## Results

Across 72 solved value cells, the classifications are:

- positive cross-difference: 32;
- negative cross-difference: 17;
- zero information: 18;
- zero or boundary: 5.

For post-signal acreage reallocation, finite cross-differences range from
-0.060402 to 0.726767 US$/acre. For state-shock buffering they range from
-1.748747 to 1.360842 US$/acre. The mixed signs are retained and are numerical
evidence, not a universal monotonicity claim.

Every reported cross-difference is independently reconstructed from the four
corresponding solved values in
`tests/test_issue36_scientific_claim_repair.py`.
