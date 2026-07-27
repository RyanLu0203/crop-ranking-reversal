# Mechanism isolation audit — Issue #36

## A. Margin-induced Kansas inversion

The official 2016--2023 score order is Winter Wheat (0.893658), Soybean
(0.755591), Corn (0.748444). Mean real operating margins are respectively
US$138.34, US$228.99 and US$199.77 per acre. The top-score crop therefore has
the lowest mean margin.

The no-CVaR endpoint allocates 0.070028 to Winter Wheat. The full CVaR model
allocates 0.247831. Risk raises, rather than displaces, the top-score crop.
Kansas is consequently evidence of score--margin separation and
margin-induced complete rank inversion.

## B. Risk-induced crossing

Focal pair: Soybean (higher score) versus Corn (lower score). The official
mean-margin gap is +US$29.22 per acre. The registered path uses 4,096
Student-\(t\)-copula scenarios at Kendall's \(\tau=0.25\), then applies a 10%
Soybean-specific adverse event equal to one-third of historical mean real
gross revenue (US$154.683 per acre). Non-adverse observations receive an exact
finite-sample compensation, so the Soybean scenario mean is unchanged.

At loose risk tolerance \(\rho=1\), Soybean/Corn shares are 0.650000/0.279972.
At tight \(\rho=0\), they are 0.180654/0.219346. Reversal remains at
\(\rho=0.1\) and \(0.2\), and disappears by \(0.3\). The crossing therefore
occurs with both \(s_{\rm Soy}>s_{\rm Corn}\) and
\(\mu_{\rm Soy}>\mu_{\rm Corn}\).

This is a controlled drought-or-basis stress, not an estimated event
frequency or claim about Kansas farms.

## C. Operational crossing

The scenario law, score, means and a fixed provably nonbinding CVaR ceiling
remain unchanged. Seven stages add land-only, crop bounds, budget, Corn
rotation, Soybean contract, planting-labour and harvest-equipment restrictions.
Those stages change active sets but do not reverse the Soybean--Corn pair.

A registered Soybean rotation-cap grid then tightens from 0.65 to 0.10. The
pair first crosses at cap 0.35: Soybean receives 0.350000 and Corn 0.375324.
The active set is land, budget and rotation. All looser null cells and tighter
reversal cells remain in `operational_mechanism.csv`.

## Evidence paths

- `reconstruction/issue34/outputs/margin_mechanism.csv`
- `reconstruction/issue34/outputs/risk_induced_reversal.csv`
- `reconstruction/issue34/outputs/operational_mechanism.csv`
- `figures/issue34/Figure4.*`
