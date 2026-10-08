"""Committee-consensus federated learning aggregation (Li et al., 2021).

Implements the core mechanism of "A Blockchain-based Decentralized Federated
Learning Framework with Committee Consensus" (BFLC), *IEEE Network* 35(1):
234-241 (doi:10.1109/MNET.011.2000263). (An earlier version of this
docstring also cited a medical-data-sharing extension in *IEEE JBHI*
25(10):3640-3651; that reference could not be located during the round-19
audit and its DOI was found unregistered in round 27, so it has been
removed from the package and manuscript -- see CHANGELOG.)

Each round: non-committee nodes train locally and submit updates; committee
members validate every update by scoring it against their *own* local data
(so the committee doubles as a rotating k-fold validation set) and combine
per-update scores via the median; only updates whose score clears a
threshold are aggregated into the next global model. The next committee is
then elected from the best-scoring contributors.

This module is deliberately agnostic to the model class: an "update" is any
object the caller's ``committee_score_fn`` (the scoring callable passed to
:func:`validate_updates`) knows how to handle -- a gradient array, a
state_dict, a scikit-learn estimator, ...; :func:`elect_committee` only
ever sees a dict of scores. Aggregating the accepted updates is likewise
the caller's job (this module has no aggregation function; the recipe in
:mod:`medchain.recipes` uses a plain mean). An earlier version of this
paragraph referred to ``score_fn`` and a non-existent ``aggregate_fn``
(corrected in audit round 32). See :mod:`medchain.recipes` for a concrete
worked example with linear models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np

__all__ = [
    "CommitteeValidationResult",
    "validate_updates",
    "elect_committee",
    "malicious_attack_success_probability",
]


#: Rejection reasons that describe a failure on the committee's side rather than the submitter's.
COMMITTEE_SIDE_REASONS = frozenset({"no_finite_member_score", "too_few_member_scores"})


@dataclass
class CommitteeValidationResult:
    """One submitted update's committee verdict.

    ``n_scored`` is the number of committee members whose score was finite
    and therefore entered the median; ``reason`` is ``None`` for an
    ordinary verdict, ``"non_finite_update"`` when the update itself was
    NaN/Inf (rejected before scoring, the submitter's fault),
    ``"no_finite_member_score"`` when no committee member produced a finite
    score, or ``"too_few_member_scores"`` when fewer than ``min_scored``
    did. The last two are *not* attributable to the submitter (they are
    collected in :data:`COMMITTEE_SIDE_REASONS`); callers that update
    reputations should treat them as committee-side failures, see
    :class:`medchain.recipes.trustworthy_fl.TrustworthyFLSimulator`.
    Both fields were added in v0.1.20 so that dropped member scores leave a
    trace (audit, round 20); ``too_few_member_scores`` in v0.1.21.
    """
    node_id: object
    score: float
    accepted: bool
    n_scored: int = 0
    reason: str | None = None


def validate_updates(updates: dict, committee_score_fn: Callable[[object, object], float],
                      committee_local_data: dict, threshold: float = 0.0,
                      min_scored: int | None = None) -> list[CommitteeValidationResult]:
    """Score each submitted update against every committee member's local data.

    Parameters
    ----------
    updates : dict
        ``{node_id: update}`` submitted by non-committee (training) nodes
        this round.
    committee_score_fn : callable
        ``committee_score_fn(update, local_data) -> float`` — e.g. validation
        accuracy of ``update`` evaluated on one committee member's
        ``local_data``. Higher is better.
    committee_local_data : dict
        ``{committee_node_id: local_data}`` for every current committee
        member; each member independently scores every update.
    threshold : float
        Minimum *median* score (across committee members) required for an
        update to be accepted. The paper's minimal instantiation uses
        validation accuracy directly as the score with no explicit
        threshold (equivalent to ``threshold=0``); callers targeting a
        specific quality bar can raise it.

    Returns
    -------
    list of :class:`CommitteeValidationResult`, one per submitted update,
    each carrying the cross-committee median score and accept/reject flag.

    Notes
    -----
    Non-finite updates (NaN/Inf) are rejected before scoring, not merely
    by the resulting score. Found during audit: a corrupted update (e.g.
    a weight vector containing NaN, from a malformed local dataset or a
    diverging local fit) does not necessarily produce a NaN *score* --
    demonstrated for this package's own ``_validation_accuracy``, where
    ``NaN >= 0.5`` evaluates to ``False`` under IEEE 754 comparison rules,
    silently turning an all-NaN weight vector into "predict the negative
    class everywhere," which can score as an ordinary, plausible, and
    thus *accepted* number depending on the validation set's class
    balance. Checking the score alone cannot catch this, since the score
    itself is no longer NaN by the time ``committee_score_fn`` returns
    it; the update must be checked before scoring. This check is applied
    to array-like updates (anything exposing ``np.asarray``); updates of
    other types are left to ``committee_score_fn`` to validate, since
    "finite" is not a meaningful concept for an arbitrary object.
    """
    if min_scored is not None and not (1 <= min_scored <= len(committee_local_data)):
        raise ValueError(
            f"min_scored must be in [1, number of committee members] = [1, {len(committee_local_data)}]; "
            f"got {min_scored}. 0 is equivalent to None, and a value above the committee size makes "
            f"every update a committee-side failure (found during audit, round 22).")
    results = []
    for node_id, update in updates.items():
        try:
            update_arr = np.asarray(update, dtype=float)
            is_finite = np.all(np.isfinite(update_arr))
        except (TypeError, ValueError):
            is_finite = True  # not array-like; not this function's concern
        if not is_finite:
            results.append(CommitteeValidationResult(node_id=node_id, score=float("-inf"), accepted=False,
                                                     n_scored=0, reason="non_finite_update"))
            continue
        member_scores = np.asarray([committee_score_fn(update, data) for data in committee_local_data.values()],
                                   dtype=float)
        finite_scores = member_scores[np.isfinite(member_scores)]
        if finite_scores.size == 0:
            results.append(CommitteeValidationResult(node_id=node_id, score=float("-inf"), accepted=False,
                                                     n_scored=0, reason="no_finite_member_score"))
            continue
        if min_scored is not None and finite_scores.size < min_scored:
            results.append(CommitteeValidationResult(node_id=node_id, score=float("-inf"), accepted=False,
                                                     n_scored=int(finite_scores.size), reason="too_few_member_scores"))
            continue
        median_score = float(np.median(finite_scores))
        results.append(CommitteeValidationResult(node_id=node_id, score=median_score,
                                                   accepted=median_score >= threshold,
                                                   n_scored=int(finite_scores.size)))
    return results


def elect_committee(candidates: Sequence, scores: dict, c_num: int,
                     strategy: str = "by_score", rng: np.random.Generator | None = None,
                     secondary_factor: dict | None = None, factor_weight: float = 0.0) -> list:
    """Elect the next committee from this round's validated contributors.

    Implements the three election strategies discussed in Section IV-B of
    Li et al. (2021):

    - ``"random"``: uniform random draw from ``candidates`` (best
      generalisation / worst adversarial resistance).
    - ``"by_score"`` (default): the ``c_num`` candidates with the highest
      validation score become the committee (strongest adversarial
      resistance, the paper's recommended default).
    - ``"multi_factor"``: ranks by ``factor_weight * secondary_factor +
      (1 - factor_weight) * normalized_score``, e.g. blending in a
      transmission-rate or reputation factor alongside the raw score.

    Parameters
    ----------
    candidates : sequence
        Node IDs eligible for election (typically this round's validated
        contributors).
    scores : dict
        ``{node_id: score}`` for each candidate (e.g. the median validation
        score from :func:`validate_updates`).
    c_num : int
        Committee size to elect; silently capped at ``len(candidates)``.
    """
    candidates = list(candidates)
    c_num = min(c_num, len(candidates))
    if c_num == 0:
        return []
    if strategy == "random":
        rng = rng or np.random.default_rng()
        idx = rng.choice(len(candidates), size=c_num, replace=False)
        return [candidates[int(i)] for i in idx]   # keep the caller's id types (choice on the list yielded np.str_/np.int64)
    if strategy == "by_score":
        missing = [n for n in candidates if scores is None or n not in scores]
        if missing:
            raise ValueError(f"by_score election: no score for candidate(s) {missing}")
        return sorted(candidates, key=lambda n: -scores[n])[:c_num]
    if strategy == "multi_factor":
        if secondary_factor is None:
            raise ValueError("multi_factor strategy requires secondary_factor")
        if not (0.0 <= factor_weight <= 1.0):
            raise ValueError(
                f"factor_weight must be in [0, 1] to remain a weighted blend of the two "
                f"normalized factors; got {factor_weight}. Values outside this range silently "
                f"reverse the intended ranking (e.g. favouring lower scores), found during audit.")
        missing = [n for n in candidates if scores is None or n not in scores]
        if missing:
            raise ValueError(f"multi_factor election: no score for candidate(s) {missing}")
        raw = np.array([scores[n] for n in candidates], dtype=float)
        rng_ = raw.max() - raw.min()
        norm_score = (raw - raw.min()) / rng_ if rng_ > 0 else np.zeros_like(raw)
        sec = np.array([secondary_factor.get(n, 0.0) for n in candidates], dtype=float)
        sec_rng = sec.max() - sec.min()
        norm_sec = (sec - sec.min()) / sec_rng if sec_rng > 0 else np.zeros_like(sec)
        combined = factor_weight * norm_sec + (1 - factor_weight) * norm_score
        order = np.argsort(-combined)
        return [candidates[i] for i in order[:c_num]]
    raise ValueError(f"unknown strategy {strategy!r}; choose random/by_score/multi_factor")


def malicious_attack_success_probability(n_participating: int, malicious_fraction: float,
                                          committee_fraction: float) -> float:
    """Theoretical committee-takeover probability (Li et al. 2021, Section IV-C).

    A malicious coalition needs to capture more than half the committee
    seats. With ``A`` participating nodes, a malicious fraction ``q``, and
    committee fraction ``p``, this is the probability that, drawing
    ``A*p`` committee seats from ``A`` nodes, more than half of the drawn
    seats come from the ``A*q`` malicious ones — a hypergeometric tail
    probability, reproducing the paper's Fig. 3.

    Returns 0.0 whenever a majority-malicious committee is combinatorially
    impossible (e.g. ``malicious_fraction`` too small relative to the
    committee size needed for a majority).

    ``n_participating`` must be a positive integer and both fractions must
    lie in [0, 1]: a fraction above 1 made the malicious pool or the
    committee larger than the network and scipy returned ``nan`` with no
    error (audit, round 27) -- for a function the manuscript recommends as
    a pre-deployment parameter check.
    """
    from scipy import stats

    if isinstance(n_participating, bool) or not isinstance(n_participating, (int, np.integer)) \
            or n_participating < 1:
        raise ValueError(f"n_participating must be a positive integer; got {n_participating!r}")
    for name, val in (("malicious_fraction", malicious_fraction), ("committee_fraction", committee_fraction)):
        if not np.isfinite(val) or not (0.0 <= val <= 1.0):
            raise ValueError(f"{name} must be a finite fraction in [0, 1]; got {val}")

    A = n_participating
    K = int(round(A * malicious_fraction))   # malicious pool size
    n_draw = int(round(A * committee_fraction))  # committee size
    if n_draw == 0 or K == 0:
        return 0.0
    majority = n_draw // 2 + 1
    # P(X > n_draw/2) for X ~ Hypergeometric(A, K, n_draw)
    dist = stats.hypergeom(A, K, n_draw)
    return float(dist.sf(majority - 1))
