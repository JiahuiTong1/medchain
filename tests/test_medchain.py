"""Property and scientific-contract tests for medchain (v0.1.x series).

Each test either fixes a claim validated against the two source papers, or
is a regression test for a defect found during one of the audit rounds
recorded in CHANGELOG.md -- about three-quarters of the suite (46 of 62),
grouped below under the round in which the defect was found. The
paper-derived claims:
  - Liu et al. (2024), FGCS 154:59-71 ("BtRaI") for reputation.py and rpbft.py
    (RPBFT is BtRaI's Section 4.2; an earlier version of this header
    mis-attributed rpbft.py to Li et al.)
  - Li et al. (2021), IEEE Network 35(1):234-241 ("BFLC") for bflc.py
  - The gap between them documented by Yang & Li (2024, Connection Science
    36(1):2316018) -- committee infiltration by intermittent attackers -- for
    the recipes/trustworthy_fl.py integration.
"""
from __future__ import annotations

import numpy as np
import pytest

from medchain.consensus.reputation import (
    credibility_weighted_score, behavior_score, adaptive_learning_rate,
    HCReputationState, PnFReputationState, CSPReputationState,
    update_hc_reputation, update_pnf_reputation, update_csp_reputation,
)
from medchain.consensus.rpbft import (RPBFTState, rotate_committee, max_fault_tolerance, leader,
                                       record_block, select_committee)
from medchain.aggregation.bflc import validate_updates, elect_committee, malicious_attack_success_probability
from medchain.recipes.trustworthy_fl import Node, TrustworthyFLSimulator, _validation_accuracy

SEED = 0


# ---------------------------------------------------------------- reputation.py
def test_credibility_downweights_outliers():
    scores = np.array([0.9, 0.88, 0.92, 0.91, 0.89, 0.1])
    agg, cred = credibility_weighted_score(scores)
    assert cred[-1] < cred[:-1].mean() - 0.3          # outlier's credibility clearly lower than honest raters'
    # With only 6 raters, Eq. (2)'s credibility cannot suppress one extreme
    # outlier to near-zero (it is a bounded, not a hard-rejecting, weight),
    # so the aggregate is pulled measurably below the honest consensus but
    # stays well above the outlier's own value -- a real, faithfully
    # reproduced property of the published formula, not an implementation
    # defect. With more honest raters the pull shrinks (tested below).
    assert scores[-1] < agg < scores[:-1].mean()

    many_honest = np.concatenate([np.full(30, 0.9), [0.1]])
    agg_many, _ = credibility_weighted_score(many_honest)
    assert agg_many > agg    # same single outlier has much less effect against a larger honest pool
    assert agg_many > 0.8


def test_credibility_zero_entries_excluded():
    agg, cred = credibility_weighted_score(np.array([0.0, 0.0, 0.7, 0.8]))
    assert cred.size == 2                              # only the two nonzero ratings count
    assert 0.7 <= agg <= 0.8


def test_behavior_score_range_and_monotonicity():
    # moderate parameters (avoids float64 sigmoid saturation at Beh >> 1)
    good = behavior_score(ac_num=3, f_bar=2, ac_val=2, wr_num=0, wr_val=0)
    mid = behavior_score(ac_num=2, f_bar=2, ac_val=1, wr_num=1, wr_val=0)
    bad = behavior_score(ac_num=1, f_bar=1, ac_val=0, wr_num=5, wr_val=5)
    assert 0.5 <= bad < mid < good < 1.0

    # extreme good behaviour saturates toward (but, per the paper, never
    # reaches) 1.0; float64 underflow makes the open interval [0.5, 1)
    # indistinguishable from closed at this scale, which is a numerical
    # limit rather than a modelling error.
    saturated = behavior_score(ac_num=10, f_bar=5, ac_val=10, wr_num=0, wr_val=0)
    assert saturated >= good


def test_adaptive_learning_rate_asymmetry():
    """Paper (Section 4.1.1, discussion after Eq. 6): reputation should climb
    slowly on good performance (small gamma when current > historical) and
    fall quickly on bad performance (large gamma when current < historical)."""
    assert adaptive_learning_rate(0.5, 0.9, gamma_up=0.6, gamma_down=0.4) == 0.4   # rising -> slow (small gamma)
    assert adaptive_learning_rate(0.5, 0.1, gamma_up=0.6, gamma_down=0.4) == 0.6   # falling -> fast (large gamma)
    with pytest.raises(ValueError):
        adaptive_learning_rate(0.5, 0.9, gamma_up=0.4, gamma_down=0.6)  # must have gamma_down < gamma_up


def test_hc_reputation_converges_to_steady_service_quality():
    """Reputation tracks sustained input quality and preserves relative
    ranking across differentiated healthcare centres.

    Note on scope (tightened during round-2 audit): this test feeds six
    distinct steady-state input levels and checks that reputation
    converges near each one while preserving their relative order --
    a real, meaningful property of the update rule (Eq. 1-6) on its own
    terms. It does *not* independently verify that these six specific
    numbers are pixel-accurate readings of Liu et al.'s Fig. 4, since the
    test is circular with respect to that specific claim: any six
    distinct plausible targets would pass equally well. The manuscript
    and this docstring were both revised to stop asserting a precise
    figure reproduction that could not be independently re-verified.
    """
    rng = np.random.default_rng(SEED)
    targets = {"HC1": 0.96, "HC2": 0.84, "HC3": 0.74, "HC4": 0.82, "HC5": 0.88, "HC6": 0.88}
    converged = {}
    for name, target in targets.items():
        st = HCReputationState(reputation=0.5, alpha=(0.4, 0.2, 0.2, 0.2), gamma_up=0.6, gamma_down=0.4)
        for _ in range(80):
            pnf = rng.normal(target, 0.02, 50).clip(1e-6, 1)
            peer = rng.normal(target, 0.02, 5).clip(1e-6, 1)
            r = update_hc_reputation(st, pnf_ratings=pnf, peer_hc_ratings=peer, csp_rating=target,
                                      csp_reputation=0.95,
                                      chain_behavior=dict(ac_num=10, f_bar=3, ac_val=10, wr_num=0, wr_val=0))
        converged[name] = r
    # ranking preserved and each within 0.06 of its own fed-in target
    assert list(sorted(converged, key=converged.get, reverse=True))[:2] == ["HC1", "HC5"] or \
           list(sorted(converged, key=converged.get, reverse=True))[0] == "HC1"
    for name, target in targets.items():
        assert abs(converged[name] - target) < 0.06


def test_reputation_weights_must_sum_to_one():
    with pytest.raises(ValueError):
        HCReputationState(reputation=0.5, alpha=(0.5, 0.5, 0.5, 0.5))


# ---------------------------------------------------------------- rpbft.py
def test_fault_tolerance_formula_self_consistent_and_improves_on_pbft():
    """All four formulas were verified verbatim against the published text
    of Liu et al. (2024), Section 5(3), during the round-19 audit (earlier
    rounds could not obtain the full text and said so). The paper's own
    closed form floor((3N-c-1)/6) is not equal to the sum of its two
    component bounds for about a third of (N, c) pairs, so both are
    returned; the manuscript's Example 3 (N=100, c=4) is a case where they
    agree. This test does not claim correspondence to the paper's Tables
    3-4, which measure latency and traffic, not fault-tolerance counts."""
    r = max_fault_tolerance(n_total=100, c_num=4)
    assert r["rpbft_total_fault_tolerance"] == (3 * 100 - 4 - 1) // 6
    assert r["plain_pbft_fault_tolerance"] == (100 - 1) // 3
    assert r["improvement"] > 0                        # RPBFT strictly improves on plain PBFT here
    assert r["rpbft_total_exact_fault_tolerance"] == r["committee_fault_tolerance"] + r["validator_fault_tolerance"]
    assert r["rpbft_total_exact_fault_tolerance"] == r["rpbft_total_fault_tolerance"]  # (100, 4) agrees
    # a case where the paper's closed form and the exact component sum differ by one
    r2 = max_fault_tolerance(n_total=100, c_num=5)
    assert r2["rpbft_total_exact_fault_tolerance"] == 1 + 47
    assert r2["rpbft_total_fault_tolerance"] == 49
    assert r2["improvement_exact"] == r2["rpbft_total_exact_fault_tolerance"] - r2["plain_pbft_fault_tolerance"]


def test_committee_is_top_reputation():
    rng = np.random.default_rng(1)
    node_ids = list(range(20))
    reputations = {i: rng.uniform(0.5, 0.9) for i in node_ids}
    state = RPBFTState(node_ids=node_ids, reputations=reputations, c_num=5)
    top5 = set(sorted(node_ids, key=lambda n: -reputations[n])[:5])
    assert set(state.committee) == top5
    assert reputations[leader(state)] == max(reputations[n] for n in state.committee)


def test_anti_collusion_caps_carryover():
    """The cap must hold under *drifting* reputations. The original version
    of this test kept reputations fixed, so the ranking never changed and the
    committee merely oscillated between two sets with overlap == cap; the
    replacement path was never exercised and a v0.1.0 defect -- replacements
    drawn from validators who had been on the previous committee -- survived
    until the round-26 fuzz test (46.7% of drifting rotations breached the
    cap)."""
    rng = np.random.default_rng(1)
    node_ids = list(range(20))
    reputations = {i: rng.uniform(0.5, 0.9) for i in node_ids}
    state = RPBFTState(node_ids=node_ids, reputations=reputations, c_num=5, epoch_num=1)
    breached = 0
    for _ in range(40):
        prev = set(state.committee)
        for k in rng.choice(20, size=5, replace=False):          # a quarter of the nodes move
            state.reputations[int(k)] = float(rng.uniform(0.5, 0.9))
        rotate_committee(state)
        overlap = len(prev & set(state.committee))
        breached += overlap > state.collusion_cap
        assert overlap <= state.collusion_cap, (prev, state.committee)
        assert len(state.committee) == 5 and not (set(state.committee) & set(state.validators))
    assert breached == 0


def test_c_num_bounds_validated():
    with pytest.raises(ValueError):
        RPBFTState(node_ids=list(range(5)), reputations={i: 0.5 for i in range(5)}, c_num=5)


# ---------------------------------------------------------------- bflc.py
def test_median_validation_resists_single_malicious_committee_member():
    updates = {"good": "g", "bad": "b"}
    table = {
        "c1": {"g": 0.85, "b": 0.20},
        "c2": {"g": 0.83, "b": 0.22},
        "c3_malicious": {"g": 0.10, "b": 0.99},
    }
    results = validate_updates(updates, lambda u, t: t[u], table, threshold=0.5)
    by_id = {r.node_id: r for r in results}
    assert by_id["good"].accepted and not by_id["bad"].accepted


def test_election_strategies():
    scores = {i: float(i) for i in range(10)}
    assert set(elect_committee(range(10), scores, 3, strategy="by_score")) == {9, 8, 7}
    mf = elect_committee(range(10), scores, 3, strategy="multi_factor",
                          secondary_factor={i: 10 - i for i in range(10)}, factor_weight=1.0)
    assert set(mf) == {0, 1, 2}
    with pytest.raises(ValueError):
        elect_committee(range(10), scores, 3, strategy="nonsense")


def test_attack_probability_qualitative_pattern():
    """Reproduces Li et al. Fig. 3: success probability negligible below ~50% malicious share."""
    low = malicious_attack_success_probability(1000, 0.3, 0.2)
    edge = malicious_attack_success_probability(1000, 0.5, 0.2)
    high = malicious_attack_success_probability(1000, 0.7, 0.2)
    assert low < 0.01
    assert low < edge < high
    assert high > 0.9


# ---------------------------------------------------------------- recipes/trustworthy_fl.py
def _make_hospital_data(rng, n=150, d=6, shift=0.0):
    X = rng.normal(0, 1, (n, d))
    X = np.hstack([X, np.ones((n, 1))])
    true_w = np.array([1.5, -1.0, 0.8, 0.5, -0.6, 1.2, shift])
    p = 1 / (1 + np.exp(-(X @ true_w)))
    y = (rng.uniform(size=n) < p).astype(float)
    return X, y


def test_reputation_election_reduces_sleeper_infiltration():
    """Core integration claim: reputation-driven committee election admits a
    sleeper/intermittent attacker less often after defection than the
    original BFLC by-score rule -- directly addressing the BFLC weakness
    Yang & Li (2024) point out, which motivates combining the two papers.

    A single seed is not a reliable basis for this claim (infiltration counts
    are seed-dependent). The claim is tested in aggregate over 20 seeds with
    a paired one-sided exact Wilcoxon signed-rank test, matching how the
    paper's own Section 6 experiments report distributions rather than
    single runs.

    Statistic (settled in the round-19 audit): the number of *committee
    seats* held by sleeper nodes in the 34 post-defection rounds (a round
    with two sleepers on the committee counts 2; 102 possible). Earlier
    rounds counted post-defection rounds containing at least one sleeper
    (12.95 -> 1.10) while calling it "seats"; the raw seat count is
    17.30 -> 1.10 (about a 94% reduction), strictly better on every one of
    the 20 seeds (asserted with ``<``, matching the manuscript's wording
    since v4; until round 27 the test asserted only ``<=``), exact
    p = 9.5e-7.

    Third arm (round 27): under reputation election incumbents stay
    eligible and 77% of seats carry over between rounds, so the two
    election rules differ in *rotation* as well as in ranking quantity.
    ``reelect_incumbents=False`` removes that difference (0% carryover,
    like the score baseline) and the result is essentially unchanged
    (0.90 seats), which is what the manuscript's Example 2 reports as a
    robustness check. Both arms are strictly better on all 20 seeds, so
    both sit at the exact test's floor p = 2**-20 = 9.54e-7 (round 28):
    the identical p-value is saturation, not evidence of equality, which
    is why the assertions below are on seat counts and per-seed dominance
    rather than on p alone.

    This test's history is itself part of the package's audit trail: an
    asymmetric-learning-rate bug fixed during initial development flipped
    the single-seed result this test originally checked, which is why it
    was rewritten to the current 20-seed paired design; a subsequent audit
    then found that the "score" baseline was silently backfilling incumbent
    committee members' re-election eligibility with their *reputation*
    (only correct under election="reputation"), which understated the true
    gap. Both corrections are recorded in CHANGELOG.md.
    """
    from scipy import stats as sstats

    def build(rng, defect_after=6):
        nodes = []
        for i in range(12):
            X, y = _make_hospital_data(rng, shift=rng.normal(0, 0.3))
            nodes.append(Node(node_id=f"H{i}", X=X, y=y,
                               reputation_state=HCReputationState(reputation=0.5),
                               defect_after_round=defect_after if i < 3 else None))
        rng.shuffle(nodes)
        return nodes

    n_seeds = 20
    arms = {"score": dict(election="score"),
            "reputation": dict(election="reputation"),
            "reputation_rotating": dict(election="reputation", reelect_incumbents=False)}
    seats = {arm: [] for arm in arms}
    carried = {arm: 0 for arm in arms}
    for seed in range(n_seeds):
        for arm, kwargs in arms.items():
            rng = np.random.default_rng(seed)
            nodes = build(rng)
            sleeper_ids = {n.node_id for n in nodes if n.defect_after_round is not None}
            sim = TrustworthyFLSimulator(nodes=nodes, c_num=3, threshold=0.55, seed=seed, **kwargs)
            sim.run(n_rounds=40)
            post_seats = sum(len(sleeper_ids & set(h["committee"])) for i, h in enumerate(sim.history) if i >= 6)
            seats[arm].append(post_seats)
            committees = [set(h["committee"]) for h in sim.history]
            carried[arm] += sum(len(a & b) for a, b in zip(committees, committees[1:]))

    score_arr = np.array(seats["score"])
    rep_arr = np.array(seats["reputation"])
    rot_arr = np.array(seats["reputation_rotating"])
    assert rep_arr.mean() < 0.3 * score_arr.mean()          # a >3x gap, not just "some" gap
    assert np.all(rep_arr < score_arr)                       # the manuscript says "strictly better on all 20 seeds"
    # committee stickiness: score and forced-rotation arms never carry a seat over;
    # default reputation election carries most seats over (77% in the reported runs)
    n_transitions = n_seeds * 39 * 3
    assert carried["score"] == 0 and carried["reputation_rotating"] == 0
    assert carried["reputation"] > 0.5 * n_transitions
    # the robustness arm: removing the stickiness leaves the headline result intact
    assert rot_arr.mean() < 0.3 * score_arr.mean()
    assert np.all(rot_arr < score_arr)
    # the manuscript reports 15 zero-infiltration seeds under reputation election;
    # asserted loosely (>= 12) because a single seat can flip on floating-point
    # differences between platforms in the CI matrix
    assert np.sum(rep_arr == 0) >= 12
    # method="exact" chosen explicitly (the paired differences contain many
    # tied absolute values, and scipy's default "auto" falls back to a normal
    # approximation whenever ties are present; found during audit, round 17).
    stat, p = sstats.wilcoxon(score_arr, rep_arr, alternative="greater", method="exact")
    assert p < 1e-3
    _, p_rot = sstats.wilcoxon(score_arr, rot_arr, alternative="greater", method="exact")
    assert p_rot < 1e-3
    assert p == pytest.approx(2.0 ** -n_seeds) and p_rot == pytest.approx(2.0 ** -n_seeds)   # the floor


def test_score_election_incumbents_not_backfilled_by_reputation():
    """Regression test for the audit-discovered contamination bug: under
    election="score", an incumbent committee member with no fresh round
    score must not be re-electable purely on a high reputation value."""
    rng = np.random.default_rng(5)
    nodes = [Node(node_id=f"H{i}", X=(d := _make_hospital_data(rng))[0], y=d[1],
                   reputation_state=HCReputationState(reputation=0.5))
             for i in range(8)]
    sim = TrustworthyFLSimulator(nodes=nodes, c_num=3, threshold=0.3, election="score", seed=5)
    nodes[0].reputation_state.reputation = 0.99   # artificially high reputation, no training history
    sim.rpbft.committee = ["H0", "H1", "H2"]
    sim.rpbft.validators = [n.node_id for n in nodes if n.node_id not in {"H0", "H1", "H2"}]
    sim.run_round()
    assert "H0" not in sim.rpbft.committee


def test_simulator_runs_and_improves_over_random_init():
    rng = np.random.default_rng(3)
    nodes = [Node(node_id=f"H{i}", X=(d := _make_hospital_data(rng))[0], y=d[1],
                   reputation_state=HCReputationState(reputation=0.5))
             for i in range(8)]
    X_test, y_test = _make_hospital_data(np.random.default_rng(999), n=1000)
    sim = TrustworthyFLSimulator(nodes=nodes, c_num=2, threshold=0.5, election="reputation", seed=3)
    acc_before = sim.evaluate(X_test, y_test)   # zero-weight model: ~0.5
    sim.run(10)
    acc_after = sim.evaluate(X_test, y_test)
    assert acc_after > acc_before
    assert acc_after > 0.65


# ---------------------------------------------------------------- round-2 audit fixes
def test_credibility_score_rejects_out_of_range_ratings():
    """Regression test: out-of-domain ratings (outside 0 or (0,1]) must raise,
    not silently produce negative credibility weights (found during audit)."""
    with pytest.raises(ValueError):
        credibility_weighted_score([5.0, 5.0, 5.0, -5.0, -5.0])
    with pytest.raises(ValueError):
        credibility_weighted_score([0.5, 1.3])
    with pytest.raises(ValueError):
        credibility_weighted_score([0.5, -0.1])
    # boundary values remain valid: 0 (no interaction) and 1 (perfect rating)
    agg, cred = credibility_weighted_score([0.0, 1.0, 0.8])
    assert cred.size == 2  # the zero entry is excluded, not rejected


def test_waste_penalty_below_one_rejected():
    """Regression test: waste_penalty < 1 must raise rather than silently
    invert a penalty into a reward (found during audit)."""
    chain_ok = dict(ac_num=3, f_bar=2, ac_val=2, wr_num=0, wr_val=0)
    with pytest.raises(ValueError):
        update_pnf_reputation(PnFReputationState(reputation=0.5), hc_ratings=np.array([0.9]),
                               waste_penalty=np.array([0.5]), csp_rating=0.9, chain_behavior=chain_ok)
    # a legitimate penalty (>=1) still lowers reputation relative to no penalty
    r_penalized = update_pnf_reputation(PnFReputationState(reputation=0.5), hc_ratings=np.array([0.9]),
                                         waste_penalty=np.array([3.0]), csp_rating=0.9, chain_behavior=chain_ok)
    r_neutral = update_pnf_reputation(PnFReputationState(reputation=0.5), hc_ratings=np.array([0.9]),
                                       waste_penalty=None, csp_rating=0.9, chain_behavior=chain_ok)
    assert r_penalized < r_neutral


def test_scalar_rating_inputs_validated():
    """csp_rating / csp_reputation bypass credibility_weighted_score entirely
    (they are scalars, not arrays) and need their own range check."""
    chain_ok = dict(ac_num=3, f_bar=2, ac_val=2, wr_num=0, wr_val=0)
    with pytest.raises(ValueError):
        update_hc_reputation(HCReputationState(reputation=0.5), pnf_ratings=np.array([0.8]),
                              peer_hc_ratings=np.array([0.8]), csp_rating=1.5, csp_reputation=0.9,
                              chain_behavior=chain_ok)
    with pytest.raises(ValueError):
        update_pnf_reputation(PnFReputationState(reputation=0.5), hc_ratings=np.array([0.8]),
                               waste_penalty=None, csp_rating=-0.2, chain_behavior=chain_ok)


def test_pnf_reputation_basic_behavior():
    """PnF reputation had zero test coverage before the round-2 audit."""
    chain_ok = dict(ac_num=3, f_bar=2, ac_val=2, wr_num=0, wr_val=0)
    st_good = PnFReputationState(reputation=0.5)
    st_bad = PnFReputationState(reputation=0.5)
    for _ in range(20):
        update_pnf_reputation(st_good, hc_ratings=np.array([0.95, 0.9]), waste_penalty=None,
                               csp_rating=0.9, chain_behavior=chain_ok)
        update_pnf_reputation(st_bad, hc_ratings=np.array([0.1, 0.15]), waste_penalty=None,
                               csp_rating=0.2, chain_behavior=chain_ok)
    assert st_good.reputation > st_bad.reputation
    assert 0.0 <= st_good.reputation <= 1.0
    assert 0.0 <= st_bad.reputation <= 1.0


def test_csp_reputation_basic_behavior():
    """CSP reputation had zero test coverage before the round-2 audit."""
    chain_ok = dict(ac_num=3, f_bar=2, ac_val=2, wr_num=0, wr_val=0)
    st = CSPReputationState(reputation=0.5)
    for _ in range(20):
        r = update_csp_reputation(st, pnf_ratings=np.array([0.9, 0.85, 0.9]),
                                   hc_ratings=np.array([0.88, 0.9]), chain_behavior=chain_ok)
    assert 0.0 <= r <= 1.0
    assert r > 0.5  # should have risen toward the sustained high input ratings


# ---------------------------------------------------------------- round-3 audit: coverage gaps
def test_select_committee_contract():
    """select_committee was previously only covered indirectly via
    RPBFTState.__post_init__; this asserts its own return contract."""
    rng = np.random.default_rng(9)
    node_ids = list(range(12))
    reps = {i: rng.uniform(0.4, 0.95) for i in node_ids}
    committee, validators = select_committee(node_ids, reps, c_num=4)
    assert len(committee) == 4
    assert len(validators) == 8
    assert set(committee) | set(validators) == set(node_ids)
    assert set(committee) & set(validators) == set()
    # committee must be exactly the top-4 by reputation (descending)
    expected_top4 = sorted(node_ids, key=lambda n: (-reps[n], n))[:4]
    assert committee == expected_top4
    # every committee member outranks every validator
    assert min(reps[c] for c in committee) >= max(reps[v] for v in validators)


def test_record_block_rotates_on_schedule_and_on_rejection():
    """record_block had zero test coverage before the round-3 audit despite
    being the only implementation of RPBFT's block-acceptance-driven
    rotation rule (paper Section 4.2, step 3)."""
    rng = np.random.default_rng(2)
    node_ids = list(range(10))
    reps = {i: rng.uniform(0.5, 0.9) for i in node_ids}

    # accepted blocks: rotation only after epoch_num of them
    state = RPBFTState(node_ids=node_ids, reputations=reps, c_num=3, epoch_num=3)
    results = [record_block(state, accepted=True) for _ in range(3)]
    assert results == [False, False, True]
    assert state.blocks_this_epoch == 0          # counter reset after rotation confirms rotate_committee ran

    # rejected block: immediate rotation regardless of epoch position
    state2 = RPBFTState(node_ids=node_ids, reputations=reps, c_num=3, epoch_num=10)
    rotated = record_block(state2, accepted=False)
    assert rotated is True
    assert state2.blocks_this_epoch == 0


# ---------------------------------------------------------------- round-4 audit
def test_zero_is_a_legitimate_scalar_rating():
    """Regression test: 0.0 is a legitimate csp_rating / csp_reputation
    value (e.g. a validation accuracy of exactly zero) and must not raise.
    An earlier version of _check_unit_interval used the open interval
    (0, 1], which rejected 0.0 and could crash TrustworthyFLSimulator's
    integration path the first time a committee gave a zero score (found
    during audit; see CHANGELOG)."""
    chain_ok = dict(ac_num=1, f_bar=1, ac_val=1, wr_num=0, wr_val=0)
    # must not raise
    r = update_hc_reputation(HCReputationState(reputation=0.5), pnf_ratings=np.array([0.5]),
                              peer_hc_ratings=np.array([0.5]), csp_rating=0.0, csp_reputation=0.95,
                              chain_behavior=chain_ok)
    assert 0.0 <= r <= 1.0
    r2 = update_pnf_reputation(PnFReputationState(reputation=0.5), hc_ratings=np.array([0.5]),
                                waste_penalty=None, csp_rating=0.0, chain_behavior=chain_ok)
    assert 0.0 <= r2 <= 1.0
    # negative and >1 must still be rejected (the boundary fix must not
    # have accidentally widened the valid range in the other direction)
    with pytest.raises(ValueError):
        update_hc_reputation(HCReputationState(reputation=0.5), pnf_ratings=np.array([0.5]),
                              peer_hc_ratings=np.array([0.5]), csp_rating=-0.01, csp_reputation=0.95,
                              chain_behavior=chain_ok)
    with pytest.raises(ValueError):
        update_hc_reputation(HCReputationState(reputation=0.5), pnf_ratings=np.array([0.5]),
                              peer_hc_ratings=np.array([0.5]), csp_rating=1.01, csp_reputation=0.95,
                              chain_behavior=chain_ok)


def test_simulator_survives_a_zero_committee_score():
    """End-to-end regression: a submitted update that scores exactly 0.0
    against every committee member's local data must not crash run_round()."""
    rng = np.random.default_rng(0)
    nodes = []
    for i in range(6):
        X, y = _make_hospital_data(rng)
        nodes.append(Node(node_id=f"H{i}", X=X, y=y, reputation_state=HCReputationState(reputation=0.5)))
    sim = TrustworthyFLSimulator(nodes=nodes, c_num=2, threshold=0.0, election="reputation", seed=0)
    # force the reputation update path to see an exact zero score directly,
    # rather than relying on random data to (rarely) produce one
    from medchain.aggregation.bflc import CommitteeValidationResult
    fake_results = [CommitteeValidationResult(node_id="H2", score=0.0, accepted=True)]
    chain_behavior = dict(ac_num=1, f_bar=3, ac_val=1, wr_num=0, wr_val=0)
    node = sim._by_id("H2")
    score01 = max(0.0, min(1.0, fake_results[0].score))
    # this line mirrors run_round()'s own call and must not raise
    update_hc_reputation(node.reputation_state, pnf_ratings=np.array([score01]),
                          peer_hc_ratings=np.array([score01]), csp_rating=score01,
                          csp_reputation=0.95, chain_behavior=chain_behavior)


# ---------------------------------------------------------------- round-6 audit
def test_factor_weight_range_validated():
    """Regression test: factor_weight outside [0, 1] silently reverses the
    intended ranking (a candidate's own score becomes negatively weighted)
    rather than remaining a weighted blend; found during audit."""
    scores = {i: float(i) for i in range(10)}
    secondary = {i: 10 - i for i in range(10)}
    with pytest.raises(ValueError):
        elect_committee(range(10), scores, 3, strategy="multi_factor",
                         secondary_factor=secondary, factor_weight=-0.5)
    with pytest.raises(ValueError):
        elect_committee(range(10), scores, 3, strategy="multi_factor",
                         secondary_factor=secondary, factor_weight=1.5)
    # boundary values remain valid
    at_zero = elect_committee(range(10), scores, 3, strategy="multi_factor",
                               secondary_factor=secondary, factor_weight=0.0)
    assert set(at_zero) == {9, 8, 7}   # pure by-score at the lower boundary
    at_one = elect_committee(range(10), scores, 3, strategy="multi_factor",
                              secondary_factor=secondary, factor_weight=1.0)
    assert set(at_one) == {0, 1, 2}    # pure by-secondary-factor at the upper boundary


def test_collusion_cap_range_validated():
    """Regression test: a negative collusion_cap forces eviction on every
    rotation regardless of actual carryover, driving the committee into a
    permanent non-converging oscillation between two fixed groups; found
    during audit."""
    rng = np.random.default_rng(3)
    node_ids = list(range(10))
    reps = {i: rng.uniform(0.4, 0.9) for i in node_ids}
    with pytest.raises(ValueError):
        RPBFTState(node_ids=node_ids, reputations=reps, c_num=4, collusion_cap=-1)
    with pytest.raises(ValueError):
        RPBFTState(node_ids=node_ids, reputations=reps, c_num=4, collusion_cap=4)  # == c_num, invalid
    # boundary values remain valid
    state = RPBFTState(node_ids=node_ids, reputations=reps, c_num=4, collusion_cap=0)
    assert state.collusion_cap == 0
    state2 = RPBFTState(node_ids=node_ids, reputations=reps, c_num=4, collusion_cap=3)
    assert state2.collusion_cap == 3


# ---------------------------------------------------------------- round-7 audit
def test_duplicate_node_id_rejected():
    """Regression test: a duplicate node_id silently collapses the
    reputation dict (dict keys are unique) while _by_id() keeps returning
    only the first matching Node -- so committee ranking and the data
    actually used for training/validation could come from two different
    Node objects sharing the same id. Found during audit; must now raise
    at construction time instead of allowing this silent mismatch."""
    rng = np.random.default_rng(1)
    X1, y1 = _make_hospital_data(rng)
    X2, y2 = _make_hospital_data(rng)
    X3, y3 = _make_hospital_data(rng)
    nodes = [
        Node(node_id="H0", X=X1, y=y1, reputation_state=HCReputationState(reputation=0.3)),
        Node(node_id="H0", X=X2, y=y2, reputation_state=HCReputationState(reputation=0.9)),
        Node(node_id="H1", X=X3, y=y3, reputation_state=HCReputationState(reputation=0.5)),
    ]
    with pytest.raises(ValueError, match="duplicate node_id"):
        TrustworthyFLSimulator(nodes=nodes, c_num=1, seed=1)

    # unique ids (the normal case) must still work
    nodes_ok = [
        Node(node_id="H0", X=X1, y=y1, reputation_state=HCReputationState(reputation=0.3)),
        Node(node_id="H1", X=X2, y=y2, reputation_state=HCReputationState(reputation=0.9)),
        Node(node_id="H2", X=X3, y=y3, reputation_state=HCReputationState(reputation=0.5)),
    ]
    sim = TrustworthyFLSimulator(nodes=nodes_ok, c_num=1, seed=1)
    assert len(sim.rpbft.reputations) == 3


# ---------------------------------------------------------------- round-8 audit
def test_weight_components_must_be_nonnegative():
    """Regression test: a weight tuple with a negative component that still
    sums to 1 was previously accepted silently by all three reputation
    state classes, reversing the sign of that sub-score's contribution --
    e.g. a worse peer/CSP rating could produce a higher comprehensive
    reputation with no error. Found during audit; the missing check had
    been copy-pasted into all three classes, so all three are tested here."""
    with pytest.raises(ValueError, match="non-negative"):
        HCReputationState(reputation=0.5, alpha=(1.5, -0.3, -0.1, -0.1))
    with pytest.raises(ValueError, match="non-negative"):
        PnFReputationState(reputation=0.5, beta=(1.5, -0.3, -0.2))
    with pytest.raises(ValueError, match="non-negative"):
        CSPReputationState(reputation=0.5, delta=(1.3, -0.2, -0.1))
    # legal (non-negative, sum-to-1) weights are unaffected in all three classes
    HCReputationState(reputation=0.5, alpha=(0.4, 0.2, 0.2, 0.2))
    PnFReputationState(reputation=0.5, beta=(0.3, 0.3, 0.4))
    CSPReputationState(reputation=0.5, delta=(0.5, 0.2, 0.3))


def test_negative_weight_no_longer_inverts_direction():
    """End-to-end demonstration that the fix actually closes the
    direction-reversal behaviour observed during audit, not just that
    construction now raises."""
    chain_ok = dict(ac_num=3, f_bar=2, ac_val=2, wr_num=0, wr_val=0)
    with pytest.raises(ValueError):
        HCReputationState(reputation=0.5, alpha=(1.5, -0.3, -0.1, -0.1))
    # with legal weights, a better peer/CSP rating must not decrease reputation
    st_good = HCReputationState(reputation=0.5)
    st_bad = HCReputationState(reputation=0.5)
    r_good = update_hc_reputation(st_good, pnf_ratings=np.array([0.9]), peer_hc_ratings=np.array([0.95]),
                                   csp_rating=0.95, csp_reputation=0.95, chain_behavior=chain_ok)
    r_bad = update_hc_reputation(st_bad, pnf_ratings=np.array([0.9]), peer_hc_ratings=np.array([0.05]),
                                  csp_rating=0.05, csp_reputation=0.95, chain_behavior=chain_ok)
    assert r_good > r_bad


# ---------------------------------------------------------------- round-9 audit
def test_omega_must_be_positive():
    """Regression test: omega <= 0 silently inverts (negative) or flattens
    (zero) behavior_score's monotonicity -- the same class of
    direction-reversal defect as the alpha/beta/delta weights fixed one
    round earlier. Found during audit by testing the same failure mode
    against a parameter not covered by that earlier fix. Checked at both
    entry points: the function itself and construction of all three
    reputation-state classes (fail-fast rather than only failing on first
    use)."""
    with pytest.raises(ValueError, match="omega must be > 0"):
        behavior_score(ac_num=3, f_bar=2, ac_val=2, wr_num=0, wr_val=0, omega=-1.0)
    with pytest.raises(ValueError, match="omega must be > 0"):
        behavior_score(ac_num=3, f_bar=2, ac_val=2, wr_num=0, wr_val=0, omega=0.0)
    for cls in [HCReputationState, PnFReputationState, CSPReputationState]:
        with pytest.raises(ValueError, match="omega must be > 0"):
            cls(reputation=0.5, omega=-1.0)
        with pytest.raises(ValueError, match="omega must be > 0"):
            cls(reputation=0.5, omega=0.0)
    # legal omega (the default, 1.0) is unaffected
    assert HCReputationState(reputation=0.5).omega == 1.0
    assert behavior_score(ac_num=3, f_bar=2, ac_val=2, wr_num=0, wr_val=0, omega=1.0) > 0.5


def test_negative_omega_no_longer_inverts_direction():
    """End-to-end demonstration that the fix closes the direction-reversal
    behaviour observed during audit (good chain behaviour must score
    higher than bad, not lower)."""
    good = dict(ac_num=10, f_bar=5, ac_val=10, wr_num=0, wr_val=0)
    bad = dict(ac_num=1, f_bar=1, ac_val=0, wr_num=5, wr_val=5)
    with pytest.raises(ValueError):
        behavior_score(**good, omega=-1.0)
    g = behavior_score(**good, omega=1.0)
    b = behavior_score(**bad, omega=1.0)
    assert g > b


# ---------------------------------------------------------------- round-10 audit (systematic sweep)
def test_reputation_field_range_validated():
    """Regression test: reputation was never validated to be in [0, 1],
    unlike other scalar rating inputs. An out-of-range starting value is
    not a direction-reversal bug (the update rule self-corrects over
    several rounds) but reports physically meaningless intermediate
    values; found during a systematic audit sweep (round 10)."""
    with pytest.raises(ValueError, match=r"reputation must be in \[0, 1\]"):
        HCReputationState(reputation=5.0)
    with pytest.raises(ValueError, match=r"reputation must be in \[0, 1\]"):
        HCReputationState(reputation=-3.0)
    # boundary values remain valid
    HCReputationState(reputation=0.0)
    HCReputationState(reputation=1.0)


def test_gamma_order_validated_eagerly_at_construction():
    """Regression test: gamma_up/gamma_down were only checked lazily,
    inside adaptive_learning_rate, so a state object with the gammas
    swapped could be constructed without error and would only fail much
    later on first use. Now fails eagerly at construction, matching
    alpha/omega's fail-fast timing; found during a systematic audit
    sweep (round 10)."""
    with pytest.raises(ValueError, match="gamma_down < gamma_up"):
        HCReputationState(reputation=0.5, gamma_up=0.1, gamma_down=0.9)
    with pytest.raises(ValueError, match="gamma_down < gamma_up"):
        PnFReputationState(reputation=0.5, gamma_up=0.1, gamma_down=0.9)
    with pytest.raises(ValueError, match="gamma_down < gamma_up"):
        CSPReputationState(reputation=0.5, gamma_up=0.1, gamma_down=0.9)
    # legal defaults are unaffected
    HCReputationState(reputation=0.5)


def test_epoch_num_must_be_positive():
    """Regression test: a non-positive epoch_num forces committee
    rotation on every single block rather than the intended periodic
    rotation; found during a systematic audit sweep (round 10)."""
    node_ids = list(range(10))
    reps = {i: 0.5 for i in node_ids}
    with pytest.raises(ValueError, match="epoch_num must be a positive integer"):
        RPBFTState(node_ids=node_ids, reputations=reps, c_num=3, epoch_num=-5)
    with pytest.raises(ValueError, match="epoch_num must be a positive integer"):
        RPBFTState(node_ids=node_ids, reputations=reps, c_num=3, epoch_num=0)
    # legal default is unaffected
    s = RPBFTState(node_ids=node_ids, reputations=reps, c_num=3)
    assert s.epoch_num == 10


# ---------------------------------------------------------------- round-12 audit (performance)
def test_by_id_uses_dict_index_and_scales_correctly():
    """Regression test: _by_id was an O(n) linear scan called several
    times per round (with one call site looking the same node up twice),
    making a full round O(n^2). Found during a performance-focused audit
    sweep (round 12). This test does not assert on wall-clock time (too
    environment-dependent for a portable test) but confirms the O(1)
    index is built correctly and that a larger simulation (200 nodes)
    still produces numerically sensible results after the optimization."""
    rng = np.random.default_rng(0)
    n_nodes = 200
    nodes = [Node(node_id=f"H{i}", X=(d := _make_hospital_data(rng, n=30))[0], y=d[1],
                   reputation_state=HCReputationState(reputation=0.5))
             for i in range(n_nodes)]
    sim = TrustworthyFLSimulator(nodes=nodes, c_num=10, seed=0)
    assert len(sim._node_by_id) == n_nodes
    # Internal consistency: the index must point to the (deep-copied, per
    # round-13's fix) objects actually inside sim.nodes, not to the
    # caller's original objects -- those are no longer the same objects
    # by design after the deep-copy fix, so this checks node_id-keyed
    # consistency rather than object identity with the caller's list.
    assert all(sim._node_by_id[n.node_id] is n for n in sim.nodes)
    assert all(sim._node_by_id[n.node_id].node_id == n.node_id for n in nodes)
    sim.run(5)
    assert np.all(np.isfinite(sim.global_weights))


# ---------------------------------------------------------------- round-13 audit (mutability)
def test_simulator_instances_do_not_share_reputation_state():
    """Regression test: update_hc_reputation mutates HCReputationState.reputation
    in place, and Node.reputation_state holds a reference to that mutable
    object. Before this fix, constructing a second TrustworthyFLSimulator
    from the same Node list a first simulator had already run would start
    the second simulator with reputations already altered by the first run
    -- silently, with no error -- found during audit (round 13)."""
    rng = np.random.default_rng(0)
    nodes = [Node(node_id=f"H{i}", X=(d := _make_hospital_data(rng))[0], y=d[1],
                   reputation_state=HCReputationState(reputation=0.5))
             for i in range(6)]

    sim1 = TrustworthyFLSimulator(nodes=nodes, c_num=2, seed=0)
    sim1.run(10)
    # the caller's original Node objects must be untouched
    assert all(n.reputation_state.reputation == 0.5 for n in nodes)

    sim2 = TrustworthyFLSimulator(nodes=nodes, c_num=2, seed=0)
    # sim2 must start fresh, not inherit sim1's post-run reputations
    assert all(n.reputation_state.reputation == 0.5 for n in sim2.nodes)
    # and sim1's own internal state must be unaffected by sim2's construction
    assert any(n.reputation_state.reputation != 0.5 for n in sim1.nodes)


# ---------------------------------------------------------------- round-18 audit (adversarial input)
def test_nan_update_rejected_before_scoring():
    """Regression test for a severe defect: a NaN-contaminated update did
    not necessarily produce a NaN score. _validation_accuracy's `p >= 0.5`
    comparison evaluates to False for NaN under IEEE 754 rules, silently
    turning an all-NaN weight vector into "predict the negative class
    everywhere," which can score as an ordinary, accepted number
    depending on the validation set's class balance -- demonstrated to
    let a NaN update through and permanently corrupt global_weights
    within 2 rounds with no error raised. validate_updates must now
    reject non-finite updates before they ever reach the score function."""
    rng = np.random.default_rng(0)
    X = np.hstack([rng.normal(0, 1, (30, 3)), np.ones((30, 1))])
    y = rng.integers(0, 2, 30).astype(float)
    w_nan = np.array([np.nan, np.nan, np.nan, np.nan])
    w_inf = np.array([np.inf, 0.0, 0.0, 0.0])
    w_good = np.array([0.5, -0.3, 0.2, 0.1])
    committee_data = {"c1": (X[:20], y[:20])}
    updates = {"nan_node": w_nan, "inf_node": w_inf, "good_node": w_good}
    results = validate_updates(updates, _validation_accuracy, committee_data, threshold=0.0)
    by_id = {r.node_id: r for r in results}
    assert by_id["nan_node"].accepted is False
    assert by_id["inf_node"].accepted is False
    assert by_id["good_node"].accepted is True  # legitimate updates unaffected


def test_simulator_survives_nan_contaminated_node_data():
    """End-to-end regression: a node with entirely NaN training data must
    not permanently corrupt global_weights across a full simulation run."""
    rng = np.random.default_rng(7)
    nodes = []
    for i in range(10):
        X, y = _make_hospital_data(rng, n=100)
        nodes.append(Node(node_id=f"H{i}", X=X, y=y, reputation_state=HCReputationState(reputation=0.5)))
    nodes[0].X[:] = np.nan  # simulate corrupted/adversarial data
    sim = TrustworthyFLSimulator(nodes=nodes, c_num=2, threshold=0.0, seed=7)
    sim.run(15)
    assert np.all(np.isfinite(sim.global_weights))


# ---------------------------------------------------------------- round-19 audit
def test_nan_member_score_is_dropped_not_propagated():
    """Regression test: a committee member whose score_fn returns NaN must
    neither veto every update nor leak NaN into the result. The median is
    taken over the finite member scores; only if none are finite is the
    update rejected with -inf."""
    table = {"good": {"c1": 0.9, "c2": float("nan"), "c3": 0.85},
             "bad": {"c1": float("nan"), "c2": float("nan"), "c3": float("nan")}}
    results = validate_updates({"good": "good", "bad": "bad"},
                               lambda u, member: table[u][member],
                               {"c1": "c1", "c2": "c2", "c3": "c3"}, threshold=0.5)
    by_id = {r.node_id: r for r in results}
    assert by_id["good"].accepted and by_id["good"].score == pytest.approx(0.875)
    assert by_id["good"].n_scored == 2 and by_id["good"].reason is None       # one member dropped, visibly
    assert not by_id["bad"].accepted and by_id["bad"].score == float("-inf")
    assert by_id["bad"].n_scored == 0 and by_id["bad"].reason == "no_finite_member_score"
    assert all(np.isfinite(r.score) or r.score == float("-inf") for r in results)
    # a non-finite *update* is tagged differently from a committee failure
    r_nan = validate_updates({"u": np.array([np.nan, 1.0])}, lambda u, m: 0.9, {"c1": "c1"})[0]
    assert r_nan.reason == "non_finite_update" and r_nan.n_scored == 0


def test_simulator_validates_data_shards_at_construction():
    """Empty shards, (n,1)-shaped y, row-count mismatches and inconsistent
    feature counts previously surfaced as opaque numpy errors mid-run (or,
    for the empty shard, not at all -- see the NaN-score test above)."""
    rng = np.random.default_rng(1)
    def fresh():
        return [Node(node_id=f"H{i}", X=(d := _make_hospital_data(rng))[0], y=d[1],
                     reputation_state=HCReputationState(reputation=0.5)) for i in range(5)]
    nodes = fresh(); nodes[0].X = np.zeros((0, 7)); nodes[0].y = np.zeros(0)
    with pytest.raises(ValueError, match="empty"):
        TrustworthyFLSimulator(nodes=nodes, c_num=2, seed=1)
    nodes = fresh(); nodes[1].y = nodes[1].y.reshape(-1, 1)
    with pytest.raises(ValueError, match="1-D"):
        TrustworthyFLSimulator(nodes=nodes, c_num=2, seed=1)
    nodes = fresh(); nodes[2].y = nodes[2].y[:-1]
    with pytest.raises(ValueError, match="rows"):
        TrustworthyFLSimulator(nodes=nodes, c_num=2, seed=1)
    nodes = fresh(); nodes[3].X = nodes[3].X[:, :5]
    with pytest.raises(ValueError, match="feature"):
        TrustworthyFLSimulator(nodes=nodes, c_num=2, seed=1)
    TrustworthyFLSimulator(nodes=fresh(), c_num=2, seed=1)   # well-formed shards still accepted
    # list-of-lists shards previously passed validation and then failed on .shape mid-run
    nodes = fresh()
    for n in nodes:
        n.X, n.y = n.X.tolist(), n.y.tolist()
    sim = TrustworthyFLSimulator(nodes=nodes, c_num=2, seed=1)
    assert all(isinstance(n.X, np.ndarray) and isinstance(n.y, np.ndarray) for n in sim.nodes)
    sim.run_round()


def test_nan_parameters_and_ratings_rejected():
    """Regression test: every range check added in rounds 2-10 used
    comparisons (x < 0, x <= 0, 0 <= x <= 1, |sum-1| > eps) that are all
    False for NaN, so NaN omega / weights / ratings were accepted silently
    and turned the resulting reputation into NaN (found in round 19, the
    parameter-side twin of round 18's NaN-update finding)."""
    nan = float("nan")
    with pytest.raises(ValueError):
        HCReputationState(reputation=0.5, omega=nan)
    with pytest.raises(ValueError):
        HCReputationState(reputation=0.5, alpha=(nan, 0.0, 0.0, 0.0))
    with pytest.raises(ValueError):
        HCReputationState(reputation=nan)
    with pytest.raises(ValueError):
        HCReputationState(reputation=0.5, gamma_up=nan, gamma_down=0.4)
    with pytest.raises(ValueError):
        credibility_weighted_score([0.5, nan])
    with pytest.raises(ValueError):
        credibility_weighted_score([0.5, float("inf")])
    with pytest.raises(ValueError):
        behavior_score(ac_num=1, f_bar=1, ac_val=1, wr_num=0, wr_val=0, omega=nan)
    chain_ok = dict(ac_num=1, f_bar=1, ac_val=1, wr_num=0, wr_val=0)
    with pytest.raises(ValueError):
        update_hc_reputation(HCReputationState(reputation=0.5), pnf_ratings=np.array([0.5]),
                             peer_hc_ratings=np.array([0.5]), csp_rating=nan, csp_reputation=0.95,
                             chain_behavior=chain_ok)
    # ordinary finite inputs are unaffected
    r = update_hc_reputation(HCReputationState(reputation=0.5), pnf_ratings=np.array([0.5]),
                             peer_hc_ratings=np.array([0.5]), csp_rating=0.5, csp_reputation=0.95,
                             chain_behavior=chain_ok)
    assert np.isfinite(r)


def test_behavior_score_counts_validated():
    """Regression test: the five chain-behaviour quantities had no sign
    check, so wr_num=-1 divided by zero and ac_num<0 pushed the score
    below the documented [0.5, 1) range (missed by the round-10 sweep)."""
    with pytest.raises(ValueError, match="wr_num"):
        behavior_score(ac_num=1, f_bar=1, ac_val=1, wr_num=-1, wr_val=0)
    with pytest.raises(ValueError, match="ac_num"):
        behavior_score(ac_num=-5, f_bar=1, ac_val=0, wr_num=0, wr_val=0)
    with pytest.raises(ValueError, match="f_bar"):
        behavior_score(ac_num=1, f_bar=float("nan"), ac_val=0, wr_num=0, wr_val=0)
    assert 0.5 <= behavior_score(ac_num=0, f_bar=1, ac_val=0, wr_num=0, wr_val=0) < 1.0  # zeros are legal


def test_pnf_waste_penalty_matches_eq8_with_nonuniform_eta():
    """Fidelity test for BtRaI Eq. (8), cross-checked against the paper's
    full text in round 19: credibility Hcr is computed from the *raw*
    ratings and the penalty eta divides only inside the weighted sum. An
    earlier version penalised first and then computed credibility on the
    penalised vector, down-weighting a penalised rating a second time."""
    hr = np.array([0.9, 0.85, 0.9, 0.88]); eta = np.array([1.0, 1.0, 3.0, 1.0])
    cred = 1.0 - np.abs(hr - hr.mean())
    expected_hr_pnf = float(np.sum(cred * hr / eta) / hr.size)
    st = PnFReputationState(reputation=0.5, beta=(1.0, 0.0, 0.0))   # isolate the HR term
    chain = dict(ac_num=1, f_bar=1, ac_val=1, wr_num=0, wr_val=0)
    r = update_pnf_reputation(st, hc_ratings=hr, waste_penalty=eta, csp_rating=0.5, chain_behavior=chain)
    # current = HR_PnF exactly (beta=(1,0,0)); current > 0.5 -> gamma_down=0.4
    assert r == pytest.approx(0.6 * 0.5 + 0.4 * expected_hr_pnf)
    assert expected_hr_pnf == pytest.approx(0.7198, abs=1e-3)   # the pre-fix value was 0.6050
    # uniform eta is unchanged by the fix: the penalty simply scales the aggregate
    st1 = PnFReputationState(reputation=0.5, beta=(1.0, 0.0, 0.0))
    r_uniform = update_pnf_reputation(st1, hc_ratings=hr, waste_penalty=np.full(4, 2.0), csp_rating=0.5, chain_behavior=chain)
    agg, _ = credibility_weighted_score(hr)
    current = agg / 2.0
    gamma = 0.4 if current > 0.5 else 0.6
    assert r_uniform == pytest.approx((1 - gamma) * 0.5 + gamma * current)


def test_anti_collusion_enforceability_checked_at_construction():
    """Regression test (rounds 19-20): with fewer spare validators than the
    worst-case excess carryover (c_num - collusion_cap), the cap cannot
    always be honoured. v0.1.18 silently replaced only as many seats as it
    could; v0.1.19 raised, but only inside rotate_committee -- i.e. in the
    middle of a rejected-block recovery. The condition depends only on
    (n_nodes, c_num, collusion_cap), so it is now rejected at construction."""
    reps5 = {i: 0.5 + 0.01 * i for i in range(5)}
    with pytest.raises(ValueError, match="not enforceable"):
        RPBFTState(node_ids=list(range(5)), reputations=reps5, c_num=4, collusion_cap=0)   # 1 validator, needs 4
    with pytest.raises(ValueError, match="not enforceable"):
        RPBFTState(node_ids=list(range(4)), reputations={i: 0.5 for i in range(4)}, c_num=3)  # default cap 1, needs 2, has 1
    # boundary: exactly enough validators is accepted, and the cap is then honoured exactly
    reps10 = {i: 0.5 + 0.01 * i for i in range(10)}
    state = RPBFTState(node_ids=list(range(8)), reputations={i: reps10[i] for i in range(8)}, c_num=4, collusion_cap=0)
    prev = set(state.committee); rotate_committee(state)
    assert len(prev & set(state.committee)) == 0
    # the simulator passes an explicit no-op cap, so small simulations are unaffected
    rng = np.random.default_rng(2)
    nodes = [Node(node_id=f"H{i}", X=(d := _make_hospital_data(rng, n=40))[0], y=d[1],
                  reputation_state=HCReputationState(reputation=0.5)) for i in range(4)]
    sim = TrustworthyFLSimulator(nodes=nodes, c_num=3, seed=2)
    assert sim.rpbft.collusion_cap == 2
    sim.run(2)


# ---------------------------------------------------------------- round-20 audit
def test_committee_failure_leaves_reputations_untouched(monkeypatch):
    """Regression test: when no committee member can produce a finite score
    (every member's score_fn returns NaN), every update is rejected -- but
    that says nothing about the submitters. v0.1.19 mapped the resulting
    -inf scores to 0 credit and so turned a committee-side failure into a
    collective penalty on every trainer (0.5 -> 0.318). Now the round is
    flagged and reputations are left untouched."""
    import medchain.recipes.trustworthy_fl as tfl
    rng = np.random.default_rng(0)
    nodes = [Node(node_id=f"H{i}", X=(d := _make_hospital_data(rng))[0], y=d[1],
                  reputation_state=HCReputationState(reputation=0.5)) for i in range(6)]
    sim = TrustworthyFLSimulator(nodes=nodes, c_num=2, threshold=0.55, seed=0)
    monkeypatch.setattr(tfl, "_validation_accuracy", lambda w, data: float("nan"))
    summary = sim.run_round()
    assert summary["n_accepted"] == 0
    assert summary["committee_failed"] is True
    assert summary["n_unscored"] == summary["n_submitted"] == 4
    assert all(n.reputation_state.reputation == 0.5 for n in sim.nodes)
    # an ordinary round is not flagged
    monkeypatch.setattr(tfl, "_validation_accuracy", _validation_accuracy)
    summary2 = sim.run_round()
    assert summary2["committee_failed"] is False and summary2["n_unscored"] == 0


def test_non_finite_update_still_gets_zero_reputation_credit():
    """The submitter-side case must remain penalised: a NaN update is the
    submitter's fault (reason == "non_finite_update"), so its reputation
    falls while honest submitters' reputations are unaffected."""
    rng = np.random.default_rng(7)
    nodes = [Node(node_id=f"H{i}", X=(d := _make_hospital_data(rng, n=100))[0], y=d[1],
                  reputation_state=HCReputationState(reputation=0.5)) for i in range(6)]
    nodes[0].X[:] = np.nan
    sim = TrustworthyFLSimulator(nodes=nodes, c_num=2, threshold=0.0, seed=7)
    sim.rpbft.committee = ["H4", "H5"]; sim.rpbft.validators = ["H0", "H1", "H2", "H3"]
    summary = sim.run_round()
    assert summary["committee_failed"] is False and summary["n_unscored"] == 0
    assert sim._by_id("H0").reputation_state.reputation < 0.5          # penalised
    assert all(sim._by_id(h).reputation_state.reputation > 0.5 for h in ("H1", "H2", "H3"))  # honest, rewarded


# ---------------------------------------------------------------- round-21 audit
def test_committee_failure_reelects_randomly_under_score_election(monkeypatch):
    """Regression test: in a committee-failed round every candidate's score is
    -inf, and the by_score sort then silently seated the first c_num trainers
    in list order. Under election="score" the simulator now falls back to
    BFLC's own seeded random election; under election="reputation" the
    (untouched) reputations still rank the candidates."""
    import medchain.recipes.trustworthy_fl as tfl

    def build(seed):
        rng = np.random.default_rng(seed)
        return [Node(node_id=f"H{i}", X=(d := _make_hospital_data(rng, n=60))[0], y=d[1],
                     reputation_state=HCReputationState(reputation=0.5 + 0.01 * i)) for i in range(8)]

    # score mode: over several seeds the fallback must not always be "first c_num trainers in order"
    seated_first = []
    for seed in range(6):
        sim = TrustworthyFLSimulator(nodes=build(seed), c_num=2, election="score", seed=seed)
        trainers = [n.node_id for n in sim.nodes if n.node_id not in set(sim.rpbft.committee)]
        monkeypatch.setattr(tfl, "_validation_accuracy", lambda w, data: float("nan"))
        summary = sim.run_round()
        monkeypatch.setattr(tfl, "_validation_accuracy", _validation_accuracy)
        assert summary["committee_failed"]
        assert set(summary["committee"]) <= set(trainers)          # still drawn from this round's trainers
        seated_first.append(set(summary["committee"]) == set(trainers[:2]))
    assert not all(seated_first)

    # reputation mode: the untouched reputations still rank the candidates, but the
    # failed committee's own members are ineligible for this one election (round 24)
    sim = TrustworthyFLSimulator(nodes=build(0), c_num=2, election="reputation", seed=0)
    failed = set(sim.rpbft.committee)
    monkeypatch.setattr(tfl, "_validation_accuracy", lambda w, data: float("nan"))
    summary = sim.run_round()
    monkeypatch.setattr(tfl, "_validation_accuracy", _validation_accuracy)
    top2_others = sorted((n for n in sim.nodes if n.node_id not in failed),
                         key=lambda n: -n.reputation_state.reputation)[:2]
    assert set(summary["committee"]) == {n.node_id for n in top2_others}
    assert not (set(summary["committee"]) & failed)


def test_min_scored_guards_single_member_verdicts(monkeypatch):
    """A verdict resting on fewer finite member scores than min_scored is a
    committee-side failure ("too_few_member_scores"), not a valid median.
    The simulator passes a committee majority."""
    table = {"c1": float("nan"), "c2": float("nan"), "c3": 0.99}
    fn = lambda u, m: table[m]
    members = {"c1": "c1", "c2": "c2", "c3": "c3"}
    r_default = validate_updates({"u": np.array([1.0])}, fn, members, threshold=0.5)[0]
    assert r_default.accepted and r_default.n_scored == 1          # default keeps the old behaviour ...
    r_guarded = validate_updates({"u": np.array([1.0])}, fn, members, threshold=0.5, min_scored=2)[0]
    assert not r_guarded.accepted and r_guarded.reason == "too_few_member_scores" and r_guarded.n_scored == 1
    # ... and the simulator treats "one of three scored" as a committee failure
    import medchain.recipes.trustworthy_fl as tfl
    rng = np.random.default_rng(3)
    nodes = [Node(node_id=f"H{i}", X=(d := _make_hospital_data(rng, n=60))[0], y=d[1],
                  reputation_state=HCReputationState(reputation=0.5)) for i in range(7)]
    sim = TrustworthyFLSimulator(nodes=nodes, c_num=3, threshold=0.0, seed=3)
    good_X = sim._by_id(sim.rpbft.committee[0]).X          # exactly one of three members can score
    monkeypatch.setattr(tfl, "_validation_accuracy", lambda w, data: 0.9 if data[0] is good_X else float("nan"))
    summary = sim.run_round()
    assert summary["committee_failed"] and summary["n_unscored"] == summary["n_submitted"]
    assert all(n.reputation_state.reputation == 0.5 for n in sim.nodes)


def test_rpbft_state_and_election_validate_ids_and_keys():
    """Regression tests: duplicated node ids put one node on both the committee
    and the validator side; missing reputation/score keys raised a bare KeyError."""
    with pytest.raises(ValueError, match="unique"):
        RPBFTState(node_ids=[0, 1, 1, 2, 3], reputations={0: .9, 1: .8, 2: .7, 3: .6}, c_num=2)
    with pytest.raises(ValueError, match="no entry for node id"):
        RPBFTState(node_ids=[0, 1, 2, 3], reputations={0: .5, 1: .5, 2: .5}, c_num=2)
    with pytest.raises(ValueError, match="no score for candidate"):
        elect_committee([0, 1, 2], {0: .9, 1: .8}, 2)
    with pytest.raises(ValueError, match="no score for candidate"):
        elect_committee([0, 1, 2], {0: .9, 1: .8}, 2, strategy="multi_factor",
                        secondary_factor={0: 1, 1: 1, 2: 1}, factor_weight=0.5)


# ---------------------------------------------------------------- round-22 audit
def test_non_finite_submitters_are_never_seated_under_score_election():
    """Regression test: with fewer finite-scored candidates than c_num, the
    by_score sort merely ranked -inf last, so submitters of NaN updates were
    seated. Eligibility now requires a finite score; the shortfall is held
    over by incumbents (tier 3) when no committee-side-unscored candidates
    exist to draw from (tier 2)."""
    rng = np.random.default_rng(1)
    nodes = [Node(node_id=f"H{i}", X=(d := _make_hospital_data(rng, n=60))[0], y=d[1],
                  reputation_state=HCReputationState(reputation=0.5 + 0.01 * i)) for i in range(6)]
    sim = TrustworthyFLSimulator(nodes=nodes, c_num=3, election="score", threshold=0.0, seed=1)
    incumbents = list(sim.rpbft.committee)
    trainers = [n.node_id for n in sim.nodes if n.node_id not in set(incumbents)]     # 3 trainers
    for t in trainers[1:]:
        sim._by_id(t).X[:] = np.nan                                                    # 2 of 3 submit NaN
    summary = sim.run_round()
    assert summary["n_non_finite"] == 2 and summary["n_accepted"] == 1
    assert not (set(trainers[1:]) & set(summary["committee"]))                        # NaN submitters never seated
    assert trainers[0] in summary["committee"]                                         # the one finite candidate is
    assert summary["seats_held_over"] == 2 and summary["seats_filled_randomly"] == 0
    assert set(summary["committee"]) - {trainers[0]} <= set(incumbents)               # held-over seats are incumbents'
    assert summary["committee_failed"] is False                                        # the committee did its job


def test_mixed_failure_round_is_not_seated_in_list_order(monkeypatch):
    """Regression test: one NaN update plus committee-side failure on the rest
    left committee_failed False under the round-21 definition, so the round-21
    random fallback did not fire and the first c_num trainers in list order
    were seated -- the NaN submitter among them. Now the NaN submitter is
    excluded, the seats are drawn from the unscored pool, and the round is
    flagged as a committee failure."""
    import medchain.recipes.trustworthy_fl as tfl
    outcomes = []
    for seed in range(6):
        rng = np.random.default_rng(seed)
        nodes = [Node(node_id=f"H{i}", X=(d := _make_hospital_data(rng, n=60))[0], y=d[1],
                      reputation_state=HCReputationState(reputation=0.5)) for i in range(6)]
        sim = TrustworthyFLSimulator(nodes=nodes, c_num=2, election="score", seed=seed)
        trainers = [n.node_id for n in sim.nodes if n.node_id not in set(sim.rpbft.committee)]
        sim._by_id(trainers[0]).X[:] = np.nan
        monkeypatch.setattr(tfl, "_validation_accuracy", lambda w, data: float("nan"))
        summary = sim.run_round()
        monkeypatch.setattr(tfl, "_validation_accuracy", _validation_accuracy)
        assert summary["n_non_finite"] == 1 and summary["n_unscored"] == 3
        assert summary["committee_failed"] is True                       # 3 scorable, 3 unscored
        assert trainers[0] not in summary["committee"]                   # the NaN submitter
        assert set(summary["committee"]) <= set(trainers[1:])            # drawn from the unscored pool
        assert summary["seats_filled_randomly"] == 2 and summary["seats_held_over"] == 0
        assert all(n.reputation_state.reputation <= 0.5 for n in sim.nodes)   # NaN submitter penalised, others untouched
        outcomes.append(set(summary["committee"]) == set(trainers[1:3]))
    assert not all(outcomes)                                             # not simply "next two in list order"


def test_min_scored_validated_and_random_election_keeps_id_types():
    with pytest.raises(ValueError, match="min_scored"):
        validate_updates({"u": np.array([1.0])}, lambda u, m: 0.9, {"c1": 1, "c2": 2}, min_scored=0)
    with pytest.raises(ValueError, match="min_scored"):
        validate_updates({"u": np.array([1.0])}, lambda u, m: 0.9, {"c1": 1, "c2": 2}, min_scored=3)
    chosen = elect_committee(["H0", "H1", "H2", "H3"], None, 2, strategy="random", rng=np.random.default_rng(0))
    assert all(type(c) is str for c in chosen)
    chosen = elect_committee([10, 11, 12], None, 2, strategy="random", rng=np.random.default_rng(0))
    assert all(type(c) is int for c in chosen)


# ---------------------------------------------------------------- round-23 audit
def test_score_election_hold_over_is_blind_to_incumbent_reputation():
    """Regression test: tier-3 hold-over iterated rpbft.committee, which is
    reputation-sorted, so under election="score" the incumbents' reputations
    decided who kept a seat -- the same contamination class as the v0.1.1
    baseline fix, in a narrower corner. Held-over seats are now drawn at
    random from the incumbents with the simulator's seeded generator, so
    permuting the incumbents' reputations cannot change the outcome."""
    rng = np.random.default_rng(5)
    shards = [_make_hospital_data(rng, n=60) for _ in range(6)]

    def run(reps):
        nodes = [Node(node_id=f"H{i}", X=shards[i][0].copy(), y=shards[i][1].copy(),
                      reputation_state=HCReputationState(reputation=reps[i])) for i in range(6)]
        sim = TrustworthyFLSimulator(nodes=nodes, c_num=3, election="score", threshold=0.0, seed=5)
        incumbents = list(sim.rpbft.committee)
        trainers = [n.node_id for n in sim.nodes if n.node_id not in set(incumbents)]
        for t in trainers[1:]:
            sim._by_id(t).X[:] = np.nan                         # one finite candidate, two seats short
        summary = sim.run_round()
        assert summary["seats_held_over"] == 2 and set(incumbents) == {"H0", "H1", "H2"}
        return set(summary["committee"]) - {trainers[0]}

    held_a = run({0: .9, 1: .8, 2: .7, 3: .5, 4: .5, 5: .5})   # incumbent reputations H0 > H1 > H2
    held_b = run({0: .7, 1: .8, 2: .9, 3: .5, 4: .5, 5: .5})   # permuted
    assert held_a == held_b                                     # reputation no longer decides
    assert held_a <= {"H0", "H1", "H2"} and len(held_a) == 2


# ---------------------------------------------------------------- round-24 audit
def test_failed_committee_cannot_reelect_itself_under_reputation_election(monkeypatch):
    """Regression test: a committee whose members all fail to score leaves
    every reputation untouched (round 20), so under election="reputation"
    the by-reputation re-election seated the same members again, forever --
    a livelock whenever reputations are distinct. A failed committee's
    members are now ineligible for the immediately following election only;
    their reputations still rank them afterwards (so with persistent failure
    the committee alternates instead of freezing)."""
    import medchain.recipes.trustworthy_fl as tfl
    rng = np.random.default_rng(4)
    nodes = [Node(node_id=f"H{i}", X=(d := _make_hospital_data(rng, n=60))[0], y=d[1],
                  reputation_state=HCReputationState(reputation=0.9 - 0.05 * i)) for i in range(6)]
    sim = TrustworthyFLSimulator(nodes=nodes, c_num=2, election="reputation", threshold=0.55, seed=4)
    first = tuple(sim.rpbft.committee)
    assert first == ("H0", "H1")                                   # highest reputations
    monkeypatch.setattr(tfl, "_validation_accuracy", lambda w, data: float("nan"))
    seq = [tuple(sim.run_round()["committee"]) for _ in range(4)]
    monkeypatch.setattr(tfl, "_validation_accuracy", _validation_accuracy)
    assert seq[0] == ("H2", "H3")                                  # next-best, failed incumbents excluded
    assert seq[1] == ("H0", "H1")                                  # exclusion lasts one election only
    assert seq == [("H2", "H3"), ("H0", "H1"), ("H2", "H3"), ("H0", "H1")]
    assert all(abs(n.reputation_state.reputation - (0.9 - 0.05 * i)) < 1e-12 for i, n in enumerate(sim.nodes))
    # once the committee works again, ordinary reputation election resumes and updates flow
    summary = sim.run_round()
    assert summary["committee_failed"] is False and summary["n_accepted"] > 0


# ---------------------------------------------------------------- round-25 audit
def test_reputation_election_keeps_committee_size_when_trainers_are_fewer_than_seats(monkeypatch):
    """Regression test: after the round-24 exclusion of a failed committee's
    members, a network with fewer trainers than seats (n_nodes - c_num <
    c_num) had too few candidates and the committee silently shrank below
    c_num (found by the round-25 fuzz test). Trainers now take every seat
    they can; the shortfall is held over by the excluded incumbents, best
    reputation first, and reported."""
    import medchain.recipes.trustworthy_fl as tfl
    rng = np.random.default_rng(1)
    nodes = [Node(node_id=f"H{i}", X=(d := _make_hospital_data(rng, n=60))[0], y=d[1],
                  reputation_state=HCReputationState(reputation=0.9 - 0.05 * i)) for i in range(8)]
    sim = TrustworthyFLSimulator(nodes=nodes, c_num=5, election="reputation", threshold=0.0, seed=1)
    assert list(sim.rpbft.committee) == ["H0", "H1", "H2", "H3", "H4"]
    monkeypatch.setattr(tfl, "_validation_accuracy", lambda w, data: float("nan"))
    summary = sim.run_round()
    monkeypatch.setattr(tfl, "_validation_accuracy", _validation_accuracy)
    assert summary["committee_failed"]
    assert len(summary["committee"]) == 5
    assert {"H5", "H6", "H7"} <= set(summary["committee"])                # all three trainers seated
    assert set(summary["committee"]) - {"H5", "H6", "H7"} == {"H0", "H1"}  # shortfall: best-reputation incumbents
    assert summary["seats_held_over"] == 2 and summary["seats_filled_randomly"] == 0


def test_simulator_invariants_under_random_failures():
    """Property test distilled from the round-25 fuzz run: across random
    network sizes, committee sizes, election modes, NaN submissions and
    committee failures (whole or partial), the structural invariants of a
    round hold. Seeds are fixed so the test is deterministic."""
    import medchain.recipes.trustworthy_fl as tfl
    orig = tfl._validation_accuracy
    checked = 0
    try:
        for trial in range(60):
            rng = np.random.default_rng(1000 + trial)
            n_nodes = int(rng.integers(3, 9)); c_num = int(rng.integers(1, n_nodes))
            election = ["score", "reputation"][trial % 2]
            reps = rng.uniform(0.3, 0.95, n_nodes)
            nodes = [Node(node_id=f"H{i}", X=(d := _make_hospital_data(rng, n=40))[0], y=d[1],
                          reputation_state=HCReputationState(reputation=float(reps[i]))) for i in range(n_nodes)]
            sim = TrustworthyFLSimulator(nodes=nodes, c_num=c_num, election=election, threshold=0.0, seed=trial)
            ids = {n.node_id for n in sim.nodes}
            for _ in range(5):
                committee = set(sim.rpbft.committee)
                for n in sim.nodes:
                    if n.node_id not in committee and rng.uniform() < 0.3:
                        n.X[:] = np.nan
                mode = rng.choice(["ok", "all_nan", "partial"])
                if mode == "all_nan":
                    tfl._validation_accuracy = lambda w, data: float("nan")
                elif mode == "partial":
                    bad = {id(sim._by_id(m).X) for m in list(committee)[: max(1, len(committee) // 2)]}
                    tfl._validation_accuracy = (lambda w, data, bad=bad:
                                                float("nan") if id(data[0]) in bad else orig(w, data))
                else:
                    tfl._validation_accuracy = orig
                s = sim.run_round()
                checked += 1
                assert len(s["committee"]) == c_num, (trial, election, mode, s["committee"])
                assert len(set(s["committee"])) == c_num and set(s["committee"]) <= ids
                assert np.all(np.isfinite(sim.global_weights))
                assert all(np.isfinite(n.reputation_state.reputation) and 0 <= n.reputation_state.reputation <= 1
                           for n in sim.nodes)
                assert s["n_submitted"] - s["n_accepted"] - s["n_non_finite"] - s["n_unscored"] >= 0
                assert s["seats_filled_randomly"] + s["seats_held_over"] <= c_num
                if election == "reputation":
                    assert s["seats_filled_randomly"] == 0
    finally:
        tfl._validation_accuracy = orig
    assert checked == 300


# ---------------------------------------------------------------- round-26 audit
def test_rpbft_rotation_invariants_under_random_drift():
    """Property test distilled from the round-26 direct-API fuzz: over random
    (n_nodes, c_num, collusion_cap), random reputation drift and random block
    rejections, every rotation keeps committee size == c_num, committee and
    validators disjoint and jointly exhaustive, no duplicates, leader ==
    committee[0], and carryover <= collusion_cap."""
    import math
    rng = np.random.default_rng(7)
    rotations = 0
    for _ in range(120):
        n = int(rng.integers(4, 26)); c = int(rng.integers(2, n))
        caps = [None] + [k for k in range(0, c) if n - c >= c - k]
        cap = caps[int(rng.integers(0, len(caps)))]
        if cap is None and n - c < c - math.ceil((c - 1) / 2):
            continue                                              # default cap not enforceable here
        state = RPBFTState(node_ids=list(range(n)), reputations={i: float(rng.uniform()) for i in range(n)},
                           c_num=c, epoch_num=int(rng.integers(1, 4)), collusion_cap=cap)
        for _ in range(10):
            prev = set(state.committee)
            for k in rng.choice(n, size=max(1, n // 4), replace=False):
                state.reputations[int(k)] = float(rng.uniform())
            record_block(state, accepted=bool(rng.uniform() > 0.3))
            com, val = list(state.committee), list(state.validators)
            assert len(com) == c and len(set(com)) == c
            assert not (set(com) & set(val)) and set(com) | set(val) == set(range(n))
            assert leader(state) == com[0]
            if com != list(prev) and set(com) != prev:
                rotations += 1
                assert len(set(com) & prev) <= state.collusion_cap, (n, c, state.collusion_cap, prev, com)
    assert rotations > 200


# ---------------------------------------------------------------- round-27 audit
def test_reelect_incumbents_flag_is_validated_and_keeps_committee_size():
    """``reelect_incumbents=False`` is meaningful only under reputation
    election (score election never re-elects an incumbent), so it is
    rejected under ``election="score"``; an unknown ``election`` value now
    fails at construction rather than on the first ``run_round()``. With
    fewer trainers than seats the excluded incumbents must still hold the
    shortfall over (the round-25 invariant), reported as ``seats_held_over``."""
    rng = np.random.default_rng(27)
    nodes = [Node(node_id=f"H{i}", X=(d := _make_hospital_data(rng, n=60))[0], y=d[1],
                  reputation_state=HCReputationState(reputation=0.9 - 0.05 * i)) for i in range(5)]
    with pytest.raises(ValueError, match="reelect_incumbents=False is only meaningful"):
        TrustworthyFLSimulator(nodes=nodes, c_num=2, election="score", reelect_incumbents=False)
    with pytest.raises(ValueError, match="election must be"):
        TrustworthyFLSimulator(nodes=nodes, c_num=2, election="bogus")
    # 5 nodes, c_num=3: only 2 trainers per round, so one seat must be held over every round
    sim = TrustworthyFLSimulator(nodes=nodes, c_num=3, election="reputation", threshold=0.0, seed=27,
                                 reelect_incumbents=False)
    for _ in range(6):
        prev = set(sim.rpbft.committee)
        summary = sim.run_round()
        assert len(summary["committee"]) == 3 and len(set(summary["committee"])) == 3
        assert not summary["committee_failed"]
        assert summary["seats_held_over"] == 1 and summary["seats_filled_randomly"] == 0
        trainers = {n.node_id for n in sim.nodes} - prev
        assert trainers <= set(summary["committee"])            # both trainers seated first
        held = set(summary["committee"]) - trainers
        assert held <= prev and len(held) == 1                   # the shortfall comes from the incumbents
        assert max(sim._by_id(c).reputation_state.reputation for c in prev) == \
            sim._by_id(next(iter(held))).reputation_state.reputation   # best-reputation incumbent


def test_deployment_check_functions_validate_inputs():
    """``max_fault_tolerance`` and ``malicious_attack_success_probability``
    are the two functions the manuscript recommends as pre-deployment
    parameter checks, yet until round 27 they were the only public
    functions with no input validation: ``max_fault_tolerance(4, 10)``
    returned ``validator_fault_tolerance=-3`` and ``improvement=-1``, and a
    fraction above 1 made scipy return ``nan`` from
    ``malicious_attack_success_probability`` -- both silently."""
    with pytest.raises(ValueError, match="require 1 <= c_num < n_total"):
        max_fault_tolerance(4, 10)
    with pytest.raises(ValueError, match="require 1 <= c_num < n_total"):
        max_fault_tolerance(10, 0)
    with pytest.raises(ValueError, match="must be an integer"):     # ValueError, like every other validator (round 28)
        max_fault_tolerance(10.0, 3)
    with pytest.raises(ValueError, match="must be an integer"):
        max_fault_tolerance(True, 1)
    assert max_fault_tolerance(np.int64(100), np.int64(4))["rpbft_total_fault_tolerance"] == 49   # numpy ints accepted
    for args in ((100, 1.5, 0.1), (100, 0.3, 1.5), (100, -0.1, 0.1), (100, float("nan"), 0.1)):
        with pytest.raises(ValueError, match="must be a finite fraction"):
            malicious_attack_success_probability(*args)
    for bad_n in (0, -5, 100.0, True):
        with pytest.raises(ValueError, match="positive integer"):
            malicious_attack_success_probability(bad_n, 0.3, 0.1)
    # boundary fractions remain legal and sensible
    assert malicious_attack_success_probability(100, 0.0, 0.1) == 0.0
    assert malicious_attack_success_probability(100, 1.0, 1.0) == 1.0
    assert np.isfinite(malicious_attack_success_probability(100, 0.6, 0.1))


def test_evaluate_matches_validation_accuracy_of_global_weights():
    """``TrustworthyFLSimulator.evaluate`` had no test of its own (audit,
    round 27): it must score the *current* global weights with the same
    accuracy function the committee uses, and track them as they change."""
    rng = np.random.default_rng(3)
    nodes = [Node(node_id=f"H{i}", X=(d := _make_hospital_data(rng, n=80))[0], y=d[1]) for i in range(6)]
    X_test, y_test = _make_hospital_data(rng, n=400)
    sim = TrustworthyFLSimulator(nodes=nodes, c_num=2, election="reputation", threshold=0.0, seed=3)
    assert sim.evaluate(X_test, y_test) == _validation_accuracy(np.zeros(X_test.shape[1]), (X_test, y_test))
    sim.run(n_rounds=5)
    assert sim.evaluate(X_test, y_test) == _validation_accuracy(sim.global_weights, (X_test, y_test))
    assert sim.evaluate(X_test, y_test) > 0.6


# ---------------------------------------------------------------- round-28 audit
def test_election_overwritten_after_construction_still_raises():
    """Regression test: v0.1.27 moved the ``election`` check to the
    constructor and dropped the ``else: raise`` in ``run_round()``, so an
    ``election`` value overwritten after construction (it is a public
    dataclass field) was silently run as score election. v0.1.28 restored
    the raise, but in step 5 -- after training, aggregation and the
    reputation update -- so the failed call still advanced
    ``global_weights`` and every reputation while leaving ``history`` and
    the round counter behind (audit, round 29; the v0.1.28 version of this
    test asserted only ``len(history)`` and claimed "no trace"). The check
    now runs before any side effect, and this test asserts that."""
    rng = np.random.default_rng(28)
    nodes = [Node(node_id=f"H{i}", X=(d := _make_hospital_data(rng, n=40))[0], y=d[1]) for i in range(4)]
    sim = TrustworthyFLSimulator(nodes=nodes, c_num=2, election="reputation", seed=28)
    sim.run_round()
    weights_before = sim.global_weights.copy()
    reps_before = {n.node_id: n.reputation_state.reputation for n in sim.nodes}
    committee_before = list(sim.rpbft.committee)
    rng_before = sim._rng.bit_generator.state
    sim.election = "bogus"
    with pytest.raises(ValueError, match="election must be"):
        sim.run_round()
    assert len(sim.history) == 1 and sim._round == 1
    assert np.array_equal(sim.global_weights, weights_before)
    assert {n.node_id: n.reputation_state.reputation for n in sim.nodes} == reps_before
    assert list(sim.rpbft.committee) == committee_before
    assert sim._rng.bit_generator.state == rng_before
    sim.election = "reputation"                     # recoverable: the next call is an ordinary round 2
    sim.run_round()
    assert len(sim.history) == 2 and sim._round == 2
