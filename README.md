# medchain

Reputation-driven committee-consensus federated learning for trustworthy
healthcare blockchains.

`medchain` implements and integrates two published mechanisms:

- **Committee-consensus federated learning** (Li, Chen, Liu, Huang, Zheng &
  Yan, *IEEE Network* 35(1):234-241, 2021) — a small elected committee
  validates and aggregates federated-learning updates on a blockchain,
  avoiding both a trusted central server and full-network consensus
  overhead.
- **Multidimensional reputation assessment** (Liu, Liu, Zhang, Su, Cai &
  Li, "BtRaI", *Future Generation Computer Systems* 154:59-71, 2024) — a
  credibility-weighted, asymmetrically-updated reputation score plus a
  reputation-ranked PBFT variant (RPBFT). (BtRaI's third mechanism, token
  incentives, is *not* implemented; it is listed as future work in the
  manuscript's Section 5.)

Yang & Li (*Connection Science* 36(1), 2024,
[doi:10.1080/09540091.2024.2316018](https://doi.org/10.1080/09540091.2024.2316018))
note that committee-consensus federated learning is "susceptible to mixing
malicious nodes into the committee," since the original election rule looks
only at a single round's score (they go on to propose their own quality-based
reputation consensus for the problem). `medchain.recipes.trustworthy_fl`
addresses the same gap by adopting BtRaI's published multidimensional model
rather than designing a new reputation formula (three documented deviations
from the paper's text: see the `rpbft.py` and `reputation.py` docstrings):
committees are elected by accumulated reputation (which the source
paper designs to rise slowly and fall quickly) rather than by a single round's
score, measurably reducing how often an intermittent ("sleeper") attacker
regains a committee seat after defecting (see
`examples/demo_sleeper_attack.py`; over 20 seeds, the mean number of
committee seats the attackers hold in the 34 post-defection rounds falls
from 17.30 to 1.10 of 102 possible, strictly better on every seed, one-sided
exact Wilcoxon signed-rank p = 2^-20 = 9.5e-7 -- the smallest value the exact
test can return for 20 same-signed differences). Under reputation election
incumbents stay eligible and 77% of seats carry over between rounds;
re-running with `reelect_incumbents=False` (election restricted to each
round's trainers, the same forced rotation as the score baseline) gives 0.90
seats, again strictly better on every seed, so the reduction is not an
artefact of the committee simply not rotating.

A public BFLC implementation on FISCO-BCOS exists
([iammcy/BFLC-demo](https://github.com/iammcy/BFLC-demo)); it is coupled to
that chain stack rather than being an importable library, which is the niche
`medchain` fills.

## Install

```bash
pip install -e ".[dev]"
```

Requires Python 3.10+ (3.9 reached end-of-life in October 2025), NumPy >= 1.22
(tested on 1.26 and 2.4) and SciPy >= 1.9 (tested on 1.13 and 1.17).

## Quick start

```python
import numpy as np
from medchain.consensus.reputation import HCReputationState
from medchain.recipes.trustworthy_fl import Node, TrustworthyFLSimulator

rng = np.random.default_rng(0)
nodes = [
    Node(node_id=f"H{i}",
         X=np.hstack([rng.normal(0, 1, (150, 6)), np.ones((150, 1))]),
         y=rng.integers(0, 2, 150).astype(float),
         reputation_state=HCReputationState(reputation=0.5))
    for i in range(10)
]
sim = TrustworthyFLSimulator(nodes=nodes, c_num=3, election="reputation", seed=0)
sim.run(n_rounds=20)
```

## Package layout

```
src/medchain/
  consensus/
    reputation.py   # BtRaI multidimensional reputation (Liu et al. 2024, Eq. 1-9)
    rpbft.py         # Reputation-ranked PBFT committee/validator split (Section 4.2)
                     #   (needs n_nodes >= 2*c_num - collusion_cap; ~1.5*c_num with the default cap)
  aggregation/
    bflc.py          # Committee validation, election strategies, attack analysis (Li et al. 2021)
  recipes/
    trustworthy_fl.py  # End-to-end simulator combining both papers
                       #   (election="reputation"|"score"; reelect_incumbents=False for forced rotation)
tests/                 # Property tests tied to paper claims/figures, plus one regression test per audit finding
examples/               # Runnable demonstrations
```

## Tests

```bash
python -m pytest tests/ -v
```

62 tests covering: reputation formula correctness against the source
paper's equations and convergence (within 0.04 in the shipped run; the test
allows 0.06; order preserved) when the six steady-state levels it reports for
its Fig. 4 are fed as inputs -- a contraction check, not a reproduction of
that figure -- the asymmetric
learning-rate rule, RPBFT's fault-tolerance bound versus plain
PBFT, the anti-collusion committee-rotation rule, Byzantine-robust median
validation, all three committee-election strategies, the malicious-attack
success-probability formula (reproducing Fig. 3's qualitative pattern), the
core integration claim above together with its forced-rotation robustness
arm, and one regression test per defect found in the audit rounds recorded
in `CHANGELOG.md`.

## Citing

See `CITATION.cff`. Please also cite the two source papers listed there.
