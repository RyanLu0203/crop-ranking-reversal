# Information--flexibility framework

## Timing and policy space

The canonical timing is:

1. a prior joint profit law and operational state are fixed;
2. experiment \(q\) generates signal \(Z_q\);
3. the producer observes the signal and chooses acreage policy
   \(\delta(Z_q)\in X(\phi)\);
4. prices/yields/profits realize;
5. expected profit and the ex-ante loss-CVaR of the policy are evaluated.

The informed problem and the constant-policy problem use the same probability
law, risk sign, confidence level and risk limit. Constant policies are a subset
of signal-contingent policies. This policy inclusion—not the phrase “better
forecast”—is the source of nonnegative information value.

## Information order

Precision labels alone do not order experiments. GOAL-12 must use either:

- an explicit stochastic garbling matrix showing that the less informative
  signal is reproducible from the more informative one; or
- a finite set of experiments treated as unordered sensitivity cases.

Under a verified garbling and admissible independent randomization, the more
informative policy space can reproduce every less informative policy and its
joint action/outcome distribution. This proves weak information-value
monotonicity without importing a teacher-draft citation.

## Flexibility order

Flexibility means a registered nesting of action sets,
\(X(\phi_1)\subseteq X(\phi_2)\), not an arbitrary scalar relaxation score.
For each adjacent level, record which budget, rotation, contract or bound row
changes and verify set inclusion. Both informed and uninformed values weakly
increase under preserved feasibility. VOI need not.

## Conditional complementarity gate

Complementarity is theorem-admissible only when all of the following are proved:

1. precision \(\mathcal Q\) and flexibility \(\Phi\) have declared lattice orders;
2. policies/actions form a lattice under declared meet and join;
3. every feasible-policy set is a nonempty compact sublattice;
4. the feasible correspondence increases in the strong set order;
5. the informed policy payoff is jointly supermodular in policy, precision and flexibility;
6. the prior/constant-policy value is independent of precision;
7. strict language is used only when a strict cross-difference is proved.

The fixed-land multi-crop simplex fails the componentwise lattice-closure check:
the join of two feasible acreage vectors can exceed total land. A restricted
two-crop scalar-share interval may satisfy lattice closure and is the preferred
analytic special case. The general multi-crop interaction remains a numerical
hypothesis unless another valid order is constructed.

## Finite-design interaction estimand

For ordered precisions \(q_1<q_2\) and nested flexibility levels
\(\phi_1<\phi_2\), define

\[
\Delta_{q\times\phi}=
[\operatorname{VOI}(q_2,\phi_2)-\operatorname{VOI}(q_1,\phi_2)]
-[\operatorname{VOI}(q_2,\phi_1)-\operatorname{VOI}(q_1,\phi_1)].
\]

Report the policy in every signal state, both informed and uninformed values,
the interaction contrast and a simultaneous uncertainty interval. Promotion
rules:

- lower bound above zero: positive interaction for the frozen design;
- interval containing zero: unresolved/null interaction;
- upper bound below zero: substitution;
- violated garbling or set nesting: contrast is not interpretable as precision
  by flexibility.

No empirical complementarity claim follows from this synthetic design.
