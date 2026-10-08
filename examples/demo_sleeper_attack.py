"""Reputation-driven vs. score-driven committee election under a sleeper attack.

Simulates a 12-hospital federated diagnosis-prediction task in which 3
hospitals behave honestly for the first 6 rounds (long enough to build up
either a good score or a good reputation) and then alternate honest/
malicious updates every subsequent round. Compares how often these
"sleeper" attackers still make it onto the consensus committee under the
two election rules bundled with medchain: BFLC's original "elect by this
round's score" (Li et al., 2021) and this package's reputation-driven
election using the multidimensional model of Liu et al. (2024). A third
arm (reputation election with ``reelect_incumbents=False``) removes the
committee stickiness the default reputation rule has, so that the two
rules differ only in ranking quantity; the script also prints how many
seats each arm carries over from one round to the next.

Note on the p-value: with all 20 paired differences of one sign, the
exact one-sided Wilcoxon test returns its floor, 2**-20 = 9.54e-7; two
arms reporting the same p-value therefore both dominate on every seed --
the test is saturated, not evidence that they are equal.

Run: python examples/demo_sleeper_attack.py
"""
import numpy as np
from scipy import stats

from medchain.consensus.reputation import HCReputationState
from medchain.recipes.trustworthy_fl import Node, TrustworthyFLSimulator


def make_hospital_data(rng, n=150, d=6, shift=0.0):
    X = rng.normal(0, 1, (n, d))
    X = np.hstack([X, np.ones((n, 1))])
    true_w = np.array([1.5, -1.0, 0.8, 0.5, -0.6, 1.2, shift])
    p = 1 / (1 + np.exp(-(X @ true_w)))
    y = (rng.uniform(size=n) < p).astype(float)
    return X, y


def build_nodes(rng, n_hospitals=12, n_sleepers=3, defect_after=6):
    nodes = []
    for i in range(n_hospitals):
        X, y = make_hospital_data(rng, shift=rng.normal(0, 0.3))
        nodes.append(Node(node_id=f"H{i}", X=X, y=y,
                           reputation_state=HCReputationState(reputation=0.5),
                           defect_after_round=defect_after if i < n_sleepers else None))
    rng.shuffle(nodes)
    return nodes


if __name__ == "__main__":
    n_seeds = 20
    # Three arms (the third since audit round 27): BFLC's score rule, this
    # package's reputation rule, and the reputation rule with incumbents
    # excluded from re-election (reelect_incumbents=False). Under the default
    # reputation rule incumbents stay eligible on their persisted reputation
    # and most seats carry over between rounds, so the first two arms differ
    # in rotation as well as in ranking quantity; the third arm has the same
    # forced rotation as the score baseline and isolates the ranking effect.
    arms = {"score": dict(election="score"),
            "reputation": dict(election="reputation"),
            "reputation, no re-election": dict(election="reputation", reelect_incumbents=False)}
    infiltration = {arm: [] for arm in arms}   # rounds with >= 1 sleeper on the committee
    seats = {arm: [] for arm in arms}          # total sleeper seats (a round with 2 sleepers counts 2)
    carried = {arm: 0 for arm in arms}         # seats carried over from the previous round
    for seed in range(n_seeds):
        for arm, kwargs in arms.items():
            rng = np.random.default_rng(seed)
            nodes = build_nodes(rng)
            sleeper_ids = {n.node_id for n in nodes if n.defect_after_round is not None}
            sim = TrustworthyFLSimulator(nodes=nodes, c_num=3, threshold=0.55, seed=seed, **kwargs)
            sim.run(n_rounds=40)
            # Two related but distinct statistics (audit, round 19): the raw
            # number of sleeper seats (the headline metric, tested and reported
            # in the manuscript) and the number of post-defection rounds in
            # which at least one sleeper held a seat (reported as a secondary
            # view; this was the quantity behind the pre-round-19 "12.95").
            post_rounds = sum(1 for i, h in enumerate(sim.history)
                              if i >= 6 and (sleeper_ids & set(h["committee"])))
            post_seats = sum(len(sleeper_ids & set(h["committee"]))
                             for i, h in enumerate(sim.history) if i >= 6)
            infiltration[arm].append(post_rounds)
            seats[arm].append(post_seats)
            committees = [set(h["committee"]) for h in sim.history]
            carried[arm] += sum(len(a & b) for a, b in zip(committees, committees[1:]))

    score_arr = np.array(seats["score"])            # headline metric: sleeper seats
    rep_arr = np.array(seats["reputation"])
    rot_arr = np.array(seats["reputation, no re-election"])
    round_s, round_r = np.array(infiltration["score"]), np.array(infiltration["reputation"])
    n_transitions = n_seeds * 39 * 3                 # 39 round-to-round transitions x 3 seats per run
    # method="exact" chosen explicitly rather than relying on the default
    # "auto": the paired differences here contain many tied absolute
    # values (found during audit, round 17), and scipy's auto-selection
    # falls back to a normal approximation whenever ties are present,
    # giving a p-value about 45x (more than an order of magnitude) larger
    # than the exact calculation (still supported here at n=20). Both reach the
    # same qualitative conclusion, but only one of them is what "the
    # Wilcoxon test" actually means without further qualification.
    # (The keyword is `method` since scipy 1.9; `mode` survives only as an
    # undocumented alias -- switched in round 19.)
    _, p = stats.wilcoxon(score_arr, rep_arr, alternative="greater", method="exact")
    _, p_rot = stats.wilcoxon(score_arr, rot_arr, alternative="greater", method="exact")

    print("Committee seats held by sleeper nodes in the 34 post-defection rounds (102 possible), "
          "mean over 20 seeds (sample SD, ddof=1):")
    print(f"  score-based election:       {score_arr.mean():.2f} (SD {score_arr.std(ddof=1):.2f})")
    print(f"  reputation-based election:  {rep_arr.mean():.2f} (SD {rep_arr.std(ddof=1):.2f})")
    print(f"  reduction {100 * (1 - rep_arr.mean() / score_arr.mean()):.1f}%; "
          f"reputation < score on {int(np.sum(rep_arr < score_arr))}/{n_seeds} seeds; "
          f"{int(np.sum(rep_arr == 0))}/{n_seeds} seeds with zero infiltration under reputation")
    print(f"  one-sided exact Wilcoxon signed-rank test (score > reputation): p = {p:.2e}"
          + ("  (= 2^-20, the floor for 20 same-signed differences)" if np.all(rep_arr < score_arr) else ""))
    print("Committee seats carried over from the previous round (of "
          f"{n_transitions} across the 20 runs):")
    for arm in arms:
        print(f"  {arm + ':':29s} {carried[arm]:5d} ({100 * carried[arm] / n_transitions:.1f}%)")
    print("Robustness check -- reputation election with incumbents excluded "
          "(reelect_incumbents=False, i.e. the score baseline's forced rotation):")
    print(f"  sleeper seats {rot_arr.mean():.2f} (SD {rot_arr.std(ddof=1):.2f}); "
          f"reduction {100 * (1 - rot_arr.mean() / score_arr.mean()):.1f}%; "
          f"{int(np.sum(rot_arr == 0))}/{n_seeds} zero-infiltration seeds; exact Wilcoxon p = {p_rot:.2e}"
          + ("  (= 2^-20, the floor)" if np.all(rot_arr < score_arr) else ""))
    print("Secondary view -- post-defection rounds (of 34) with >= 1 sleeper on the committee:")
    print(f"  score-based election:       {round_s.mean():.2f} (SD {round_s.std(ddof=1):.2f})")
    print(f"  reputation-based election:  {round_r.mean():.2f} (SD {round_r.std(ddof=1):.2f})")
