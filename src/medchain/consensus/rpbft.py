"""Reputation-based PBFT consensus (RPBFT), Liu et al. (2024), Section 4.2.

Nodes are ranked by comprehensive reputation (highest first); the top
``c_num`` become the consensus committee (who run classical PBFT among
themselves, leader = highest reputation) and the rest become validators
(who check the committee's blocks; a majority rejection forces an early
rotation via :func:`record_block`). After ``epoch_num`` blocks the
committee is re-ranked and rotated, with an anti-collusion rule that caps
the number of seats carried over from the previous committee at
``collusion_cap`` (default ceil((c_num-1)/2)); excess carryover seats,
lowest reputation first, are swapped for the best-ranked validators.

Two deliberate deviations from the paper's Section 4.2 text, made explicit
here after cross-checking the full text during audit (round 19):

- Step (4) as written replaces a *fixed* ceil((c_num-1)/2) carryover
  nodes whenever more than that many carry over. This module instead
  replaces exactly ``carryover - collusion_cap`` of them, i.e. it enforces
  "at most collusion_cap carryovers" as a hard cap. The two rules agree
  when the excess is exactly one; the cap variant is stricter otherwise
  and is what ``test_anti_collusion_caps_carryover`` asserts.
- Step (3)'s collective reputation penalty ``phi`` on a rejected block is
  *not* implemented; reputations are owned by the caller (see
  ``medchain.consensus.reputation``) and only the rotation side effect is
  modelled. An earlier version of this docstring claimed otherwise.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

__all__ = ["RPBFTState", "select_committee", "rotate_committee", "record_block", "leader", "max_fault_tolerance"]


@dataclass
class RPBFTState:
    node_ids: list
    reputations: dict  # node_id -> float
    c_num: int
    epoch_num: int = 10
    committee: list = field(default_factory=list)
    validators: list = field(default_factory=list)
    blocks_this_epoch: int = 0
    collusion_cap: int | None = None  # defaults to ceil((c_num-1)/2)

    def __post_init__(self):
        if len(set(self.node_ids)) != len(self.node_ids):
            dupes = sorted({n for n in self.node_ids if self.node_ids.count(n) > 1}, key=repr)
            raise ValueError(
                f"node_ids must be unique; duplicated: {dupes}. A duplicated id ends up on both the "
                f"committee and the validator side at once (found during audit, round 21; the "
                f"simulator has checked this since round 7, the direct API had not).")
        missing = [n for n in self.node_ids if n not in self.reputations]
        if missing:
            raise ValueError(f"reputations has no entry for node id(s) {missing}")
        if self.c_num < 1 or self.c_num >= len(self.node_ids):
            raise ValueError("require 1 <= c_num < number of nodes")
        if self.epoch_num < 1:
            raise ValueError(
                f"epoch_num must be a positive integer; got {self.epoch_num}. A "
                f"non-positive value forces committee rotation on every single block "
                f"(found during audit sweep, round 10), which is a degenerate "
                f"configuration rather than the intended periodic rotation.")
        if self.collusion_cap is None:
            self.collusion_cap = math.ceil((self.c_num - 1) / 2)
        elif not (0 <= self.collusion_cap <= self.c_num - 1):
            raise ValueError(
                f"collusion_cap must be in [0, c_num - 1] = [0, {self.c_num - 1}]; got "
                f"{self.collusion_cap}. A negative cap forces eviction on every rotation "
                f"regardless of actual carryover (the committee can be driven into a permanent "
                f"non-converging oscillation between two fixed groups, found during audit); a cap "
                f"of c_num or larger makes the anti-collusion rule a no-op.")
        n_validators = len(self.node_ids) - self.c_num
        worst_case_excess = self.c_num - self.collusion_cap   # every seat carried over
        if n_validators < worst_case_excess:
            raise ValueError(
                f"anti-collusion rule is not enforceable for this configuration: if the whole "
                f"committee carries over, {worst_case_excess} seat(s) must be replaced but only "
                f"{n_validators} validator(s) exist (n_nodes={len(self.node_ids)}, c_num={self.c_num}, "
                f"collusion_cap={self.collusion_cap}). Require n_nodes - c_num >= c_num - collusion_cap, "
                f"i.e. n_nodes >= {2 * self.c_num - self.collusion_cap} or collusion_cap >= "
                f"{2 * self.c_num - len(self.node_ids)}. (v0.1.19 raised only when a rotation actually "
                f"hit the shortfall, i.e. in the middle of a rejected-block recovery; this check "
                f"moves the failure to construction, audit round 20.)")
        self.committee, self.validators = select_committee(self.node_ids, self.reputations, self.c_num)


def _ranked_ids(node_ids, reputations):
    """Sort node IDs by reputation descending (ties broken by id for determinism).

    The tie-break compares ids with their own ``<`` -- for string ids that
    is lexicographic, so ``"H10"`` ranks before ``"H2"``. With every
    reputation equal at start-up (the usual initial state) the first
    committee is therefore the ``c_num`` lexicographically smallest ids,
    not a random draw; renaming or renumbering nodes changes it. Harmless
    for a paired comparison in which both arms share the same ids (as in
    ``examples/demo_sleeper_attack.py``), but worth knowing (audit, round
    27).
    """
    return sorted(node_ids, key=lambda nid: (-reputations[nid], nid))


def select_committee(node_ids, reputations, c_num):
    """Split ranked nodes into (committee, validators); committee = top c_num."""
    ranked = _ranked_ids(node_ids, reputations)
    return ranked[:c_num], ranked[c_num:]


def rotate_committee(state: RPBFTState) -> tuple[list, list]:
    """Re-rank by current reputation and elect a new committee (step 4).

    Applies the anti-collusion rule: if the freshly-ranked top ``c_num``
    would carry over more than ``collusion_cap`` members from the outgoing
    committee, the excess carryover members (highest-index, i.e. lowest
    reputation among the carryovers) are swapped out for the
    lowest-index (highest-reputation) validators not already selected.
    """
    old_committee = set(state.committee)
    ranked = _ranked_ids(state.node_ids, state.reputations)
    new_committee = ranked[:state.c_num]
    new_validators = ranked[state.c_num:]

    carryover = [nid for nid in new_committee if nid in old_committee]
    if len(carryover) > state.collusion_cap:
        # indices within new_committee, ordered by rank (low index = high reputation)
        carryover_positions = [i for i, nid in enumerate(new_committee) if nid in old_committee]
        n_excess = len(carryover) - state.collusion_cap
        # remove the *worst-ranked* (highest-index) carryover seats first
        to_remove_positions = sorted(carryover_positions, reverse=True)[:n_excess]
        # Replacements must come from validators who were NOT on the previous
        # committee: a previous member who just dropped out of the top c_num
        # is often the best-ranked validator, and swapping it back in leaves
        # the carryover count unchanged. Until v0.1.26 this filter was
        # missing and, under drifting reputations, ~47% of rotations breached
        # the cap (fuzz test, audit round 26). The construction-time
        # enforceability check needs no change: with K carryovers the pool
        # has n - 2*c_num + K members and K - cap are needed, so the
        # condition is n >= 2*c_num - cap regardless of K.
        replacements = [nid for nid in new_validators
                        if nid not in new_committee and nid not in old_committee][:n_excess]
        if len(replacements) < n_excess:   # unreachable after the construction-time check; kept as a guard
            raise ValueError(
                f"anti-collusion rule cannot be enforced: {n_excess} carryover seat(s) must be "
                f"replaced but only {len(replacements)} validator(s) are available "
                f"(n_nodes={len(state.node_ids)}, c_num={state.c_num}, "
                f"collusion_cap={state.collusion_cap}).")
        for pos, repl in zip(to_remove_positions, replacements):
            evicted = new_committee[pos]
            new_committee[pos] = repl
            new_validators.remove(repl)
            new_validators.append(evicted)
        new_committee = sorted(new_committee, key=lambda nid: (-state.reputations[nid], nid))
        new_validators = sorted(new_validators, key=lambda nid: (-state.reputations[nid], nid))

    state.committee, state.validators = new_committee, new_validators
    state.blocks_this_epoch = 0
    return state.committee, state.validators


def leader(state: RPBFTState):
    """Current committee leader = highest-reputation committee member."""
    return state.committee[0] if state.committee else None


def record_block(state: RPBFTState, accepted: bool) -> bool:
    """Advance one consensus round; returns True if the committee rotates.

    A rejected block (majority of validators voted against) forces an
    immediate rotation (paper step 3: "the node replacement phase begins
    in advance"); otherwise the committee continues until ``epoch_num``
    blocks have been produced.
    """
    if not accepted:
        rotate_committee(state)
        return True
    state.blocks_this_epoch += 1
    if state.blocks_this_epoch >= state.epoch_num:
        rotate_committee(state)
        return True
    return False


def max_fault_tolerance(n_total: int, c_num: int) -> dict:
    """RPBFT's fault-tolerance bound vs. plain PBFT (paper Section 5(3)).

    All four formulas below are the paper's, verbatim (verified against
    the published text during audit, round 19): maximum tolerable
    faulty/malicious committee members ``floor((c_num-1)/3)``, maximum
    tolerable faulty validators ``floor((n_total-c_num)/2)``, the paper's
    combined closed form ``floor((3*n_total - c_num - 1)/6)``, and the
    plain-PBFT bound ``floor((n_total-1)/3)``.

    The paper's closed form is *not* algebraically equal to the sum of its
    two component bounds (the exact sum of the un-floored terms is
    (3n - c - 2)/6, and the floor of a sum is not the sum of floors); for
    roughly one third of all (n_total, c_num) pairs the two differ by 1.
    Both are therefore returned: ``rpbft_total_fault_tolerance`` is the
    paper's closed form (kept for continuity with earlier releases and the
    manuscript's Example 3, where n=100/c=4 happens to agree), and
    ``rpbft_total_exact_fault_tolerance`` is the component sum, which is
    the quantity the paper's own argument actually justifies.
    ``improvement`` uses the closed form, ``improvement_exact`` the sum.

    Both arguments must be integers (Python or NumPy) with
    ``1 <= c_num < n_total``; anything else raises ``ValueError`` (not
    ``TypeError`` -- v0.1.27 briefly used the latter for non-integers,
    out of step with every other validator in the package and with
    ``malicious_attack_success_probability``; audit, round 28). Before
    round 27 the function had no validation at all and, e.g.,
    ``max_fault_tolerance(4, 10)`` returned a negative validator bound.
    """
    for name, val in (("n_total", n_total), ("c_num", c_num)):
        if isinstance(val, bool) or not isinstance(val, (int, np.integer)):
            raise ValueError(f"{name} must be an integer node count; got {val!r}")
    if not (1 <= c_num < n_total):
        raise ValueError(
            f"require 1 <= c_num < n_total; got c_num={c_num}, n_total={n_total}. Outside this "
            f"range the bounds are meaningless -- e.g. max_fault_tolerance(4, 10) silently "
            f"returned validator_fault_tolerance=-3 and improvement=-1 before this check "
            f"(audit, round 27), for a function the manuscript recommends as a pre-deployment "
            f"parameter check.")
    committee_f = (c_num - 1) // 3
    validator_f = (n_total - c_num) // 2
    rpbft_total = (3 * n_total - c_num - 1) // 6
    rpbft_exact = committee_f + validator_f
    pbft_total = (n_total - 1) // 3
    return {
        "committee_fault_tolerance": committee_f,
        "validator_fault_tolerance": validator_f,
        "rpbft_total_fault_tolerance": rpbft_total,
        "rpbft_total_exact_fault_tolerance": rpbft_exact,
        "plain_pbft_fault_tolerance": pbft_total,
        "improvement": rpbft_total - pbft_total,
        "improvement_exact": rpbft_exact - pbft_total,
    }
