"""Multidimensional reputation assessment (Liu, Liu, Zhang, Su, Cai & Li, 2024).

Implements the comprehensive reputation model of "Blockchain and trusted
reputation assessment-based incentive mechanism for healthcare services"
(BtRaI), *Future Generation Computer Systems* 154:59-71, Eq. (1)-(9).

Three entity types are scored: Healthcare Centers (HC), Patients-and-Family
groups (PnF), and the Cloud Service Platform (CSP). Each entity's reputation
at round t+1 blends its own history with peer assessments, discounted by a
credibility factor that penalises ratings far from the group consensus
(Eq. 2), and combined with an asymmetric learning rate that lets reputation
rise slowly but fall quickly (the paper's central design goal: "reputation
values are not easily accumulated but quickly degraded by malicious
behavior").
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "credibility_weighted_score",
    "behavior_score",
    "adaptive_learning_rate",
    "HCReputationState",
    "PnFReputationState",
    "CSPReputationState",
    "update_hc_reputation",
    "update_pnf_reputation",
    "update_csp_reputation",
]


def credibility_weighted_score(scores: np.ndarray) -> tuple[float, np.ndarray]:
    """Aggregate a vector of peer ratings into one credibility-weighted score.

    Implements Eq. (2)-(3) (and, by the same pattern, Eq. (4), (8)-(9)):
    each nonzero rating's credibility is ``1 - sqrt((r_i - mean(r))**2)``,
    i.e. ratings far from the group's own consensus are downweighted before
    being averaged back together. Zero entries (no interaction) are excluded
    from both the mean and the aggregate, matching the paper's ``n'``
    (count of nonzero assessments).

    Parameters
    ----------
    scores : array_like
        Raw ratings from each peer/assessor, each either 0 ("no
        interaction") or in (0, 1] (the paper's rating scale). Values
        outside this domain raise ``ValueError``: the credibility formula
        ``1 - |r - mean(r)|`` can go negative once a deviation exceeds 1,
        silently producing a nonsensical weighted aggregate for
        out-of-domain input rather than a clear error (found during
        audit; see CHANGELOG).

    Returns
    -------
    aggregate : float
        The credibility-weighted mean rating; 0.0 if no nonzero ratings.
    credibility : ndarray
        Per-rater credibility weights (same length as the nonzero subset).
    """
    scores = np.asarray(scores, dtype=float)
    if not np.all(np.isfinite(scores)):
        raise ValueError("ratings must be finite; got NaN/Inf entries. A NaN rating passes "
                         "every ordinary range comparison (NaN < 0 and NaN > 1 are both False) "
                         "and would silently make the aggregate, and every reputation built on "
                         "it, NaN (found during audit, round 19; see CHANGELOG).")
    if np.any((scores < 0) | (scores > 1)):
        raise ValueError("ratings must be 0 (no interaction) or in (0, 1]; "
                          f"got values outside this range: {scores[(scores < 0) | (scores > 1)]}")
    nonzero = scores[scores != 0]
    if nonzero.size == 0:
        return 0.0, np.array([])
    mean_r = nonzero.mean()
    credibility = 1.0 - np.sqrt((nonzero - mean_r) ** 2)
    aggregate = float(np.sum(credibility * nonzero) / nonzero.size)
    return aggregate, credibility


def behavior_score(ac_num: float, f_bar: float, ac_val: float, wr_num: float,
                    wr_val: float, omega: float = 1.0) -> float:
    """Consortium-chain maintenance score (Eq. 5).

    ``Beh`` rewards correctly generated/validated blocks (weighted by
    generation speed ``f_bar``) and is penalised by incorrect ones; the
    sigmoid squashes it to [0.5, 1), where ``omega`` (the "gap modifier")
    controls how sharply behaviour separates good from bad actors.

    ``omega`` must be strictly positive: the sigmoid's monotonicity (worse
    behaviour must never score higher than better behaviour) depends on
    it, and a negative value silently inverts that direction with no
    error -- found during audit (see CHANGELOG), the same failure mode as
    the alpha/beta/delta weight-direction defect fixed one round earlier.
    """
    if not np.isfinite(omega) or omega <= 0:
        raise ValueError(
            f"omega must be > 0; got {omega}. omega <= 0 inverts or flattens the "
            f"behaviour score's monotonicity (worse behaviour could score higher "
            f"than better behaviour), the same class of direction-reversal defect "
            f"found in the alpha/beta/delta weights.")
    for name, val in (("ac_num", ac_num), ("f_bar", f_bar), ("ac_val", ac_val),
                      ("wr_num", wr_num), ("wr_val", wr_val)):
        if not np.isfinite(val) or val < 0:
            raise ValueError(
                f"{name} must be a finite, non-negative number; got {val}. These are block "
                f"counts (and, for f_bar, the paper's 1-5 generation-speed scale); a negative "
                f"value can push the score below the documented [0.5, 1) range or make the "
                f"denominator zero (found during audit, round 19; see CHANGELOG).")
    beh = (ac_num * f_bar + ac_val) / (wr_num + wr_val + 1.0)
    return float(1.0 / (1.0 + np.exp(-omega * beh)))


def adaptive_learning_rate(historical: float, current: float,
                            gamma_up: float, gamma_down: float) -> float:
    """Asymmetric learning-rate rule used throughout Section 4.1.

    If the freshly computed performance score exceeds the historical
    reputation, use the *smaller* rate ``gamma_down`` so that reputation
    climbs slowly (discourages "short-term honest service" gaming); if
    current performance is below history, use the *larger* rate
    ``gamma_up`` so reputation falls quickly. Requires
    ``0 < gamma_down < gamma_up < 1`` per the paper's convention
    (named gamma_2 < gamma_1 there).

    Naming note (audit, round 20): the suffixes describe the *size* of the
    rate, not the direction of the reputation change -- ``gamma_up`` is
    the rate used when reputation goes *down*. It is kept for backward
    compatibility; ``gamma_up`` = the paper's gamma_1 and ``gamma_down`` =
    gamma_2, and the loss/gain asymmetry for symmetric inputs equals
    ``gamma_up / gamma_down`` (1.5 with the paper's defaults).
    """
    if not (0.0 < gamma_down < gamma_up < 1.0):
        raise ValueError("require 0 < gamma_down < gamma_up < 1")
    return gamma_down if current > historical else gamma_up


# --------------------------------------------------------------------- #
# Entity reputation states and update rules (Eq. 6-9)
# --------------------------------------------------------------------- #

def _check_convex_weights(name: str, weights: tuple) -> None:
    """Shared validation for the alpha/beta/delta weight tuples.

    Requires every component to be non-negative *and* the components to
    sum to 1 -- i.e. a genuine convex combination. Checking only the sum
    (as an earlier version of this module did, independently in all three
    reputation-state classes) admits weight tuples with negative
    components that still sum to 1, e.g. alpha=(1.5, -0.3, -0.1, -0.1):
    such a tuple silently reverses the sign of the corresponding
    sub-score's contribution, so a *worse* peer or CSP rating can produce
    a *higher* comprehensive reputation with no error raised -- found
    during audit; see CHANGELOG. Centralised here (rather than repeating
    the check three times) specifically because the missing
    non-negativity check had already been copy-pasted into all three
    classes once.
    """
    if any(not np.isfinite(w) for w in weights):
        raise ValueError(f"{name} weights must all be finite; got {weights} (a NaN component "
                         f"passes both the sign and the sum-to-1 check, found during audit, round 19)")
    if any(w < 0 for w in weights):
        raise ValueError(f"{name} weights must all be non-negative; got {weights}")
    if abs(sum(weights) - 1.0) > 1e-9:
        raise ValueError(f"{name} weights must sum to 1; got {weights} (sum={sum(weights)})")


def _check_positive_omega(omega: float) -> None:
    """Shared validation for the omega ("gap modifier") field.

    omega must be strictly positive: behavior_score's sigmoid depends on
    a positive omega for its monotonicity (worse chain behaviour must
    never score higher than better behaviour). A negative omega silently
    inverts that direction -- the same class of direction-reversal defect
    as the alpha/beta/delta weights, found one round later during audit
    (see CHANGELOG). Shared across all three reputation-state classes
    rather than repeated, learning directly from the alpha/beta/delta
    fix having to consolidate three copies of a check after the fact.
    """
    if not np.isfinite(omega) or omega <= 0:
        raise ValueError(f"omega must be > 0 and finite; got {omega}")


def _check_reputation_range(reputation: float) -> None:
    """Shared validation that a reputation value lies in [0, 1].

    Found during a systematic audit sweep (round 10) that this field was
    never validated at all, unlike the scalar rating inputs
    (credibility_weighted_score, csp_rating) which were validated to the
    same range starting in an earlier round. An out-of-range starting
    reputation is not a direction-reversal defect (the convex-combination
    update rule pulls it back toward [0, 1] over several rounds), but
    every round before it converges reports a reputation with no physical
    meaning under the paper's [0, 1] definition, e.g. 2.49 after the
    first update from a starting value of 5.0.
    """
    if not np.isfinite(reputation) or not (0.0 <= reputation <= 1.0):
        raise ValueError(f"reputation must be in [0, 1] and finite; got {reputation}")


def _check_gamma_order(gamma_up: float, gamma_down: float) -> None:
    """Shared, eager validation that 0 < gamma_down < gamma_up < 1.

    adaptive_learning_rate() already enforces this, but only when actually
    called (i.e. only once update_hc/pnf/csp_reputation runs) -- found
    during a systematic audit sweep (round 10) that a reputation-state
    object with the gammas swapped could be constructed without error and
    would only fail later, on first use, unlike alpha/omega which fail
    immediately at construction. This function lets the three classes
    fail at the same eager point in the object's lifecycle as alpha/omega
    do; adaptive_learning_rate's own check is left in place as a second
    line of defence for callers who invoke it directly.
    """
    if not (np.isfinite(gamma_down) and np.isfinite(gamma_up)) or not (0.0 < gamma_down < gamma_up < 1.0):
        raise ValueError(f"require 0 < gamma_down < gamma_up < 1; got gamma_down={gamma_down}, gamma_up={gamma_up}")


@dataclass
class HCReputationState:
    """Healthcare Center reputation, Eq. (1)-(6)."""
    reputation: float
    alpha: tuple[float, float, float, float] = (0.4, 0.2, 0.2, 0.2)  # PnF, peer-HC, CSP, chain
    gamma_up: float = 0.6     # paper's gamma_1: the LARGER rate, applied when reputation FALLS
    gamma_down: float = 0.4   # paper's gamma_2: the SMALLER rate, applied when reputation RISES
    omega: float = 1.0

    def __post_init__(self):
        _check_convex_weights("alpha", self.alpha)
        _check_positive_omega(self.omega)
        _check_reputation_range(self.reputation)
        _check_gamma_order(self.gamma_up, self.gamma_down)


@dataclass
class PnFReputationState:
    """Patient-and-Family reputation, Eq. (7)-(8)."""
    reputation: float
    beta: tuple[float, float, float] = (0.3, 0.3, 0.4)  # HC, CSP, chain
    gamma_up: float = 0.6     # paper's gamma_1: the LARGER rate, applied when reputation FALLS
    gamma_down: float = 0.4   # paper's gamma_2: the SMALLER rate, applied when reputation RISES
    omega: float = 1.0

    def __post_init__(self):
        _check_convex_weights("beta", self.beta)
        _check_positive_omega(self.omega)
        _check_reputation_range(self.reputation)
        _check_gamma_order(self.gamma_up, self.gamma_down)


@dataclass
class CSPReputationState:
    """Cloud Service Platform reputation, Eq. (9)."""
    reputation: float
    delta: tuple[float, float, float] = (0.5, 0.2, 0.3)  # PnF, HC, chain
    gamma_up: float = 0.6     # paper's gamma_1: the LARGER rate, applied when reputation FALLS
    gamma_down: float = 0.4   # paper's gamma_2: the SMALLER rate, applied when reputation RISES
    omega: float = 1.0

    def __post_init__(self):
        _check_convex_weights("delta", self.delta)
        _check_positive_omega(self.omega)
        _check_reputation_range(self.reputation)
        _check_gamma_order(self.gamma_up, self.gamma_down)


def _check_unit_interval(name: str, value: float) -> None:
    """Shared validation for scalar rating/reputation inputs in [0, 1].

    0 is a legitimate value (e.g. a validation accuracy of exactly 0, or
    "complete distrust"), matching the array-input convention in
    :func:`credibility_weighted_score` where 0 is accepted (there meaning
    "no interaction" rather than "zero score", but either reading treats 0
    as in-domain, not an error). An earlier version of this check used the
    open interval (0, 1], which rejected the legitimate value 0.0 and
    could crash ``update_hc_reputation`` / ``update_pnf_reputation`` mid
    simulation the first time a committee validation score was exactly
    zero; found and corrected during audit (see CHANGELOG).
    """
    if not np.isfinite(value) or not (0.0 <= value <= 1.0):
        raise ValueError(f"{name} must be in [0, 1] and finite; got {value}")


def update_hc_reputation(state: HCReputationState, *, pnf_ratings: np.ndarray,
                          peer_hc_ratings: np.ndarray, csp_rating: float,
                          csp_reputation: float, chain_behavior: dict) -> float:
    """Advance one HC's reputation by one round (Eq. 1, 3, 4, 5, 6).

    Parameters
    ----------
    pnf_ratings : array_like
        Raw ratings this HC received from each PnF this round (0 = none).
    peer_hc_ratings : array_like
        Raw ratings this HC received from each other HC this round.
    csp_rating : float
        The CSP's direct rating of this HC, in [0, 1].
    csp_reputation : float
        The CSP's own current comprehensive reputation (used as a
        credibility multiplier on its rating, per Eq. in Section 4.1.1(4)).
    chain_behavior : dict
        Keys ``ac_num, f_bar, ac_val, wr_num, wr_val`` for Eq. (5).

    Returns
    -------
    New comprehensive reputation for this HC; ``state.reputation`` is also
    updated in place.
    """
    pr_hc, _ = credibility_weighted_score(pnf_ratings)
    hr_hc, _ = credibility_weighted_score(peer_hc_ratings)
    _check_unit_interval("csp_rating", csp_rating)
    _check_unit_interval("csp_reputation", csp_reputation)
    cr_hc = csp_reputation * csp_rating
    br_hc = behavior_score(omega=state.omega, **chain_behavior)

    current = (state.alpha[0] * pr_hc + state.alpha[1] * hr_hc
               + state.alpha[2] * cr_hc + state.alpha[3] * br_hc)
    gamma = adaptive_learning_rate(state.reputation, current,
                                    state.gamma_up, state.gamma_down)
    state.reputation = (1 - gamma) * state.reputation + gamma * current
    return state.reputation


def update_pnf_reputation(state: PnFReputationState, *, hc_ratings: np.ndarray,
                           waste_penalty: np.ndarray | None, csp_rating: float,
                           chain_behavior: dict) -> float:
    """Advance one PnF's reputation by one round (Eq. 7-8).

    ``waste_penalty`` is the per-HC penalty factor eta (>1 if this PnF
    wasted that HC's resources with an invalid request); pass ``None`` or
    an all-ones array for no penalty. Values below 1 are rejected: they
    would silently *divide* the rating by a fraction, i.e. increase it,
    inverting a penalty into a reward with no warning (found during
    audit; see CHANGELOG). If a caller genuinely wants a bonus rather
    than a penalty, scale ``hc_ratings`` directly instead.
    """
    hc_ratings = np.asarray(hc_ratings, dtype=float)
    if waste_penalty is None:
        waste_penalty = np.ones_like(hc_ratings)
    waste_penalty = np.broadcast_to(np.asarray(waste_penalty, dtype=float), hc_ratings.shape)
    if not np.all(np.isfinite(waste_penalty)) or np.any(waste_penalty < 1):
        raise ValueError("waste_penalty must be finite and >= 1 for every entry (it divides the "
                          f"rating, so values < 1 would invert the intended penalty); got {waste_penalty}")
    # Eq. (8): the credibility Hcr is computed from the *raw* ratings Hr (their
    # deviation from the raw group mean); the penalty eta divides only inside
    # the weighted sum, (sum_i Hcr_i * Hr_i / eta_i) / m'. An earlier version
    # penalised first and then fed the penalised vector to
    # credibility_weighted_score, so a rating that carried a per-HC penalty was
    # also treated as an outlier and down-weighted a second time (identical
    # only when eta is uniform; found by cross-checking the paper's full text
    # during audit, round 19 -- see CHANGELOG).
    _, cred = credibility_weighted_score(hc_ratings)  # validates domain, credibility from raw Hr
    nonzero = hc_ratings != 0
    if nonzero.any():
        hr_pnf = float(np.sum(cred * hc_ratings[nonzero] / waste_penalty[nonzero]) / nonzero.sum())
    else:
        hr_pnf = 0.0
    _check_unit_interval("csp_rating", csp_rating)
    # CR_PnF: the paper lists "assessment from CSP" for PnF but gives no formula
    # (Section 4.1.2); the CSP's direct rating is used as-is here, unlike the HC
    # case where the paper explicitly multiplies by the CSP's own reputation.
    cr_pnf = csp_rating
    br_pnf = behavior_score(omega=state.omega, **chain_behavior)

    current = state.beta[0] * hr_pnf + state.beta[1] * cr_pnf + state.beta[2] * br_pnf
    gamma = adaptive_learning_rate(state.reputation, current,
                                    state.gamma_up, state.gamma_down)
    state.reputation = (1 - gamma) * state.reputation + gamma * current
    return state.reputation


def update_csp_reputation(state: CSPReputationState, *, pnf_ratings: np.ndarray,
                           hc_ratings: np.ndarray, chain_behavior: dict) -> float:
    """Advance the CSP's reputation by one round (Eq. 9).

    Simplification relative to the paper: Eq. (9) averages over *all* n PnFs
    and m HCs (and computes the credibility mean over all of them), on the
    grounds that every entity interacts with the CSP so the ratings are
    "usually non-zero". This implementation reuses the n'-based aggregate
    of :func:`credibility_weighted_score`, which excludes zero ("no
    interaction") entries. The two coincide whenever every rating is
    non-zero, which is the case the paper describes; they differ when some
    ratings are 0 (noted during the round-19 audit; see CHANGELOG).
    """
    pr_csp, _ = credibility_weighted_score(pnf_ratings)
    hr_csp, _ = credibility_weighted_score(hc_ratings)
    br_csp = behavior_score(omega=state.omega, **chain_behavior)

    current = state.delta[0] * pr_csp + state.delta[1] * hr_csp + state.delta[2] * br_csp
    gamma = adaptive_learning_rate(state.reputation, current,
                                    state.gamma_up, state.gamma_down)
    state.reputation = (1 - gamma) * state.reputation + gamma * current
    return state.reputation
