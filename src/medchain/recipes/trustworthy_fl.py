"""Reputation-driven trustworthy federated learning.

This recipe is the package's central integration: it drives the
committee-consensus federated learning of Li et al. (2021) with the
multidimensional reputation model of Liu et al. (2024) in place of Li et
al.'s own "elect by this round's validation score" rule.

Why this matters (and is not just gluing two APIs together): Yang & Li
(*Connection Science* 36(1), 2024, doi:10.1080/09540091.2024.2316018) note
in their related-work discussion that Li et al.'s BFLC "is susceptible to
mixing malicious nodes into the committee, which tends to bias the system"
-- because committee eligibility depends only on a single round's score, an
attacker can behave honestly just long enough to win a committee seat and
then defect. (That paper then proposes its own quality-based reputation
consensus for the same problem; medchain differs in adopting BtRaI's
published multidimensional, credibility-weighted model rather than
designing a new reputation formula -- with three documented deviations,
see the ``rpbft.py`` and ``reputation.py`` docstrings; an earlier version
of this paragraph said "unchanged" (corrected in audit round 32) -- and
in shipping both mechanisms as a tested, independently reusable library.)
Liu et al.'s reputation update is explicitly asymmetric for this reason
(reputation climbs slowly, falls fast, Section 4.1's central design goal),
so electing the committee by *reputation* rather than by *this round's
score alone* directly targets the gap the literature identified between
the two papers. ``TrustworthyFLSimulator``
below is the reusable object that makes this combination available as a
few lines of code rather than a from-scratch reimplementation.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
import numpy as np

from ..aggregation.bflc import validate_updates, elect_committee, COMMITTEE_SIDE_REASONS
from ..consensus.reputation import HCReputationState, update_hc_reputation
from ..consensus.rpbft import RPBFTState

__all__ = ["Node", "TrustworthyFLSimulator"]


@dataclass
class Node:
    """One federated participant (e.g. one hospital).

    ``is_malicious`` corrupts every submitted update. ``defect_after_round``
    instead models the *intermittent / sleeper* threat the literature
    specifically flags against BFLC's original committee rule: the node
    behaves honestly (and so earns committee eligibility) until this round
    index, then alternates honest/malicious behaviour every subsequent
    round -- rather than being permanently and obviously malicious.
    """
    node_id: object
    X: np.ndarray
    y: np.ndarray
    reputation_state: HCReputationState = field(default_factory=lambda: HCReputationState(reputation=0.5))
    is_malicious: bool = False
    defect_after_round: int | None = None


def _local_fit(X: np.ndarray, y: np.ndarray, weights: np.ndarray, lr: float = 0.1, steps: int = 50) -> np.ndarray:
    """One node's local logistic-regression update (gradient steps from the current global weights)."""
    w = weights.copy()
    n = X.shape[0]
    for _ in range(steps):
        z = X @ w
        p = 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))
        grad = X.T @ (p - y) / n
        w = w - lr * grad
    return w


def _validation_accuracy(weights: np.ndarray, data: tuple[np.ndarray, np.ndarray]) -> float:
    X, y = data
    z = X @ weights
    p = 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))
    pred = (p >= 0.5).astype(float)
    return float(np.mean(pred == y))


@dataclass
class TrustworthyFLSimulator:
    """End-to-end reputation-driven committee-consensus FL over ``nodes``.

    Parameters
    ----------
    nodes : list of Node
        Participants; each holds its own local ``(X, y)`` shard.
    c_num : int
        Committee size.
    threshold : float
        Minimum median committee validation accuracy for an update to be
        aggregated (BFLC's acceptance rule).
    election : {"reputation", "score"}
        ``"reputation"`` (default): elect next committee by each
        candidate's BtRaI comprehensive reputation (this package's
        integration). ``"score"``: elect by this round's raw validation
        score only, reproducing the original BFLC rule as a baseline for
        comparison. Under ``"score"``, an incumbent committee member who
        did not train this round has no fresh score and is therefore
        *not* eligible for immediate re-election (BFLC's rule has no
        memory across rounds); under ``"reputation"``, incumbents remain
        eligible on their persisted, accumulated reputation, since BtRaI's
        reputation is explicitly designed to persist across rounds. An
        earlier version of this simulator backfilled incumbents' eligibility
        with their reputation under *both* modes, which silently leaked
        this package's own integration into the "score" baseline it is
        meant to be compared against; this was found and corrected during
        audit (see CHANGELOG).
    seed : int, optional
        Seed for (a) the Gaussian noise malicious/defecting nodes add to
        their submitted updates and (b) the random draws the score election
        makes when fewer than ``c_num`` candidates have a finite score
        (tiers 2 and 3 in :meth:`run_round`). Both draw from one generator,
        so a shortfall round shifts the subsequent noise stream. Local
        training is full-batch gradient descent with no random component;
        ordinary rounds under either election mode make no random draws
        beyond (a).
    reelect_incumbents : bool
        Reputation election only (default ``True``). ``True`` keeps the
        sitting committee eligible on its persisted reputation, as
        described under ``election`` above. Because members neither train
        nor have their reputation updated while serving, this makes the
        committee sticky: in the 12-hospital sleeper-attack benchmark
        (``examples/demo_sleeper_attack.py``) 77% of seats carry over from
        one round to the next and one node sits for 34 consecutive rounds
        (audit, round 27). ``False`` restricts each election to the nodes
        that trained this round, i.e. the same forced rotation the score
        baseline has, so the two election rules then differ *only* in the
        ranking quantity; the benchmark result is essentially unchanged
        under this setting (0.90 vs 1.10 sleeper seats, both strictly
        better than the score baseline on every seed and therefore both
        at the exact test's floor, p = 2**-20), which is the robustness
        check the manuscript's Example 2 reports.
        With fewer trainers than seats the shortfall is held over by the
        best-reputation incumbents and reported as ``seats_held_over``.
        Rejected under ``election="score"``, where incumbents are never
        eligible anyway (they have no fresh score).

    Limitations (v0.1.x)
    ---------------------
    The committee is re-elected every round rather than held for a
    multi-round epoch via :func:`medchain.consensus.rpbft.rotate_committee`;
    the anti-collusion carryover cap that function enforces is therefore
    validated in isolation (``tests/test_medchain.py``) but not yet
    exercised by this simulator. Under ``election="score"`` no member can
    serve two consecutive rounds (an incumbent has no fresh score and is
    excluded from the next trainer pool); under ``election="reputation"``
    with the default ``reelect_incumbents=True`` incumbents *do* stay
    eligible and most seats carry over between rounds -- an earlier
    version of this paragraph wrongly claimed the exclusion held under
    either rule (corrected in the round-27 audit; see CHANGELOG). This is
    the reputation-monopolisation risk that BtRaI's carryover cap and
    Yang & Li's design both target; ``reelect_incumbents=False`` is the
    v0.1 stand-in. Epoch-based rotation, and reputation updates for nodes
    while they serve on committee, are planned for v0.2.
    """
    nodes: list[Node]
    c_num: int
    threshold: float = 0.5
    election: str = "reputation"
    seed: int | None = None
    lr: float = 0.1
    local_steps: int = 50
    reelect_incumbents: bool = True

    def __post_init__(self):
        # Deep-copy the caller's Node list (and each Node's mutable
        # HCReputationState) so this simulator instance owns independent
        # state. update_hc_reputation mutates HCReputationState.reputation
        # in place; without this copy, two TrustworthyFLSimulator instances
        # constructed from the same Node objects -- or a second call
        # reusing nodes from a finished simulation -- would silently share
        # reputation state, so a freshly-constructed simulator could start
        # from reputations already altered by a prior run with no error or
        # warning. Found during audit (round 13); see CHANGELOG. The X/y
        # arrays are deep-copied too (copy.deepcopy recurses into them by
        # value), though sharing them would not itself have been unsafe --
        # they are never mutated in place anywhere in this module (see
        # _local_fit: it copies the weight vector, not X or y). Deep-copying
        # everything uniformly, rather than special-casing X/y as safe to
        # share, keeps the invariant simple: nothing in self.nodes is
        # shared with the caller after construction, full stop (an earlier
        # version of this comment inaccurately said the opposite of the
        # arrays' actual copy status; corrected during audit, round 14).
        if self.election not in ("reputation", "score"):
            raise ValueError(f"election must be 'reputation' or 'score'; got {self.election!r}")
        if self.election == "score" and not self.reelect_incumbents:
            raise ValueError(
                "reelect_incumbents=False is only meaningful under election='reputation': BFLC's "
                "score rule never re-elects an incumbent (it has no fresh score), so under "
                "election='score' the flag would silently change nothing (audit, round 27).")
        self.nodes = copy.deepcopy(self.nodes)
        ids = [n.node_id for n in self.nodes]
        if len(ids) != len(set(ids)):
            dupes = sorted({nid for nid in ids if ids.count(nid) > 1}, key=str)
            raise ValueError(
                f"duplicate node_id(s) found: {dupes}. Node.node_id must be unique -- "
                f"reputation lookups and the node index both key on it, so a duplicate "
                f"silently collapses to whichever Node happens to be constructed last "
                f"in both the reputation dict and the id-to-Node index, discarding the "
                f"other same-named Node's data with no error raised (found during "
                f"audit; see CHANGELOG). This check runs before that index is built, so "
                f"it is caught here regardless of which duplicate would otherwise win.")
        # Validate every node's data shard up front (round-19 audit). Without
        # this, a feature-count mismatch or a (n, 1)-shaped y surfaced only as
        # an opaque numpy broadcasting error part-way through run_round(),
        # and an *empty* shard did not error at all: a committee member with
        # zero validation samples returns accuracy mean([]) = NaN, and NaN
        # scores were then clamped by max(0, min(1, nan)) to 1.0 -- so every
        # submitter of a rejected update received the reputation credit of a
        # perfect one. NaN-valued *entries* are deliberately still allowed
        # (they are handled downstream by validate_updates's non-finite
        # update rejection, see the round-18 regression test).
        n_features = None
        for node in self.nodes:
            X, y = np.asarray(node.X, dtype=float), np.asarray(node.y, dtype=float)
            if X.ndim != 2 or y.ndim != 1:
                raise ValueError(
                    f"node {node.node_id!r}: X must be 2-D (samples x features) and y 1-D; "
                    f"got X.shape={X.shape}, y.shape={y.shape}")
            if X.shape[0] == 0:
                raise ValueError(f"node {node.node_id!r}: data shard is empty (0 samples)")
            if X.shape[0] != y.shape[0]:
                raise ValueError(
                    f"node {node.node_id!r}: X has {X.shape[0]} rows but y has {y.shape[0]}")
            if n_features is None:
                n_features = X.shape[1]
            elif X.shape[1] != n_features:
                raise ValueError(
                    f"node {node.node_id!r}: {X.shape[1]} features, but node "
                    f"{self.nodes[0].node_id!r} has {n_features}; all shards must share one feature space")
            # Write the validated arrays back: a list-of-lists shard passed the
            # checks above but failed later on `.shape` (audit, round 20).
            # self.nodes is already a private deep copy, so this is safe.
            node.X, node.y = X, y
        self._rng = np.random.default_rng(self.seed)
        self.global_weights = np.zeros(n_features)
        reps = {n.node_id: n.reputation_state.reputation for n in self.nodes}
        # collusion_cap=c_num-1 is a no-op cap: this simulator re-elects every
        # round and never calls rotate_committee (see Limitations), so the
        # anti-collusion rule is not exercised here. Passing it explicitly
        # keeps RPBFTState's construction-time enforceability check (round 20)
        # from rejecting small simulations such as four hospitals with c_num=3.
        self.rpbft = RPBFTState(node_ids=ids, reputations=reps, c_num=self.c_num, epoch_num=10_000,
                                collusion_cap=self.c_num - 1)
        self._node_by_id = {n.node_id: n for n in self.nodes}
        self.history: list[dict] = []
        self._round = 0

    def _is_defecting_now(self, node: Node) -> bool:
        if node.is_malicious:
            return True
        if node.defect_after_round is not None and self._round >= node.defect_after_round:
            # alternate honest/malicious every other round from defect_after_round onward
            return (self._round - node.defect_after_round) % 2 == 0
        return False

    def _by_id(self, node_id):
        """O(1) lookup via the index built in __post_init__.

        Was previously ``next(n for n in self.nodes if n.node_id ==
        node_id)`` -- an O(n) linear scan called several times per round
        (roughly 2*c_num + 2*(n-c_num) + c_num times), making a full
        round's committee-data/reputation bookkeeping O(n^2) overall.
        Found during a performance-focused audit sweep (round 12); not a
        correctness issue at the demo scale used in the examples and test
        suite, but a real bottleneck at the larger node counts the
        package's design goal of independent reuse (Section 2.1) invites.
        """
        return self._node_by_id[node_id]

    def run_round(self) -> dict:
        """Run one committee-consensus FL round and return its summary.

        Summary keys: ``n_submitted``, ``n_accepted``; ``n_non_finite``
        (NaN/Inf updates rejected before scoring); ``n_unscored`` (updates
        the committee could not validly score, i.e. fewer than a committee
        majority of finite member scores); ``committee_failed`` (every
        scorable update went unscored -- reputations are left untouched for
        that round, and under reputation election the failed committee's
        members are ineligible for the next election only); ``seats_filled_randomly`` and ``seats_held_over``
        (score election: seats filled from unscored candidates at random,
        or kept by incumbents, when fewer than ``c_num`` candidates had a
        finite score; reputation election: ``seats_held_over`` counts
        incumbents re-seated only because fewer trainers than seats remained
        after their exclusion -- following a committee failure, or on every
        round when ``reelect_incumbents=False``; all 0 in ordinary rounds); ``committee`` (the
        committee elected for the *next* round, reputation-ordered);
        ``global_weights``.
        """
        # Validate `election` before any side effect. It is also checked at
        # construction (round 27), but the field is public and can be
        # overwritten afterwards; until v0.1.28 the run-time check sat in
        # step 5, after local training, aggregation and the reputation update
        # had already run, so a failed call left global_weights and every
        # reputation advanced by one round while history/_round were not
        # (audit, round 29).
        if self.election not in ("reputation", "score"):
            raise ValueError(f"election must be 'reputation' or 'score'; got {self.election!r}")
        committee_ids = set(self.rpbft.committee)
        trainers = [n for n in self.nodes if n.node_id not in committee_ids]

        # 1. local training (malicious nodes submit corrupted updates)
        updates = {}
        for node in trainers:
            if self._is_defecting_now(node):
                updates[node.node_id] = self.global_weights + self._rng.normal(0, 5.0, size=self.global_weights.shape)
            else:
                updates[node.node_id] = _local_fit(node.X, node.y, self.global_weights,
                                                     lr=self.lr, steps=self.local_steps)

        # 2. committee validation (median across committee members' local data)
        # Look each committee member up once, not twice (one lookup for
        # .X and a second, separate lookup for .y) -- the second lookup
        # was redundant even before _by_id became O(1); found in the same
        # audit sweep as the O(n) -> O(1) fix above.
        committee_data = {cid: ((member := self._by_id(cid)).X, member.y) for cid in self.rpbft.committee}
        # min_scored = committee majority: the median is only robust to one
        # dishonest member while a majority of members actually scored; a
        # verdict resting on a single finite score is treated as a
        # committee-side failure instead (audit, round 21).
        results = validate_updates(updates, _validation_accuracy, committee_data, threshold=self.threshold,
                                   min_scored=len(committee_ids) // 2 + 1)
        accepted = [r for r in results if r.accepted]

        # 3. aggregate accepted updates (simple mean, i.e. FedAvg over accepted set)
        if accepted:
            stacked = np.stack([updates[r.node_id] for r in accepted])
            self.global_weights = stacked.mean(axis=0)

        # 4. reputation update for every node that submitted this round.
        # An update the committee could not score at all
        # (reason == "no_finite_member_score": every member's score_fn returned
        # NaN/Inf) says nothing about the submitter, so its reputation is left
        # untouched. v0.1.19 mapped that -inf score to 0 credit, which turned
        # a committee-side failure into a collective penalty on every trainer
        # (0.5 -> 0.318 in the audit reproduction, round 20). A non-finite
        # *update* (reason == "non_finite_update") is the submitter's fault
        # and is still penalised with 0 credit.
        # NOTE (audit, round 27): this recipe instantiates BtRaI's three rating
        # channels (PnF, peer-HC, CSP) with the *same* scalar -- the committee's
        # median validation score -- and holds csp_reputation and the
        # chain-behaviour term constant, so within the simulator the
        # comprehensive reputation reduces to current = 0.79*score + 0.196 with
        # the default alpha. The multidimensional structure of reputation.py is
        # exercised only when it is driven directly (Example 1); stated in the
        # manuscript's F7 rather than left implicit.
        chain_behavior = dict(ac_num=1, f_bar=3, ac_val=1, wr_num=0, wr_val=0)
        n_unscored = 0
        n_non_finite = sum(1 for r in results if r.reason == "non_finite_update")
        for r in results:
            if r.reason in COMMITTEE_SIDE_REASONS:
                n_unscored += 1
                continue
            node = self._by_id(r.node_id)
            # A non-finite score (NaN, or the -inf validate_updates assigns to
            # rejected non-finite updates) must map to 0 credit. Python's
            # min(1.0, nan) returns 1.0 (nan < 1.0 is False), so the bare
            # clamp used before round 19 turned NaN into full credit.
            score01 = max(0.0, min(1.0, r.score)) if np.isfinite(r.score) else 0.0
            update_hc_reputation(
                node.reputation_state,
                pnf_ratings=np.array([score01]),
                peer_hc_ratings=np.array([score01]),
                csp_rating=score01,
                csp_reputation=0.95,
                chain_behavior=chain_behavior,
            )

        # "committee failed" = every submission the committee *could* have
        # scored went unscored for a committee-side reason (round 22; the
        # round-21 definition required every submission including NaN
        # updates, so a mixed round slipped through).
        n_scorable = len(results) - n_non_finite
        committee_failed = n_scorable > 0 and n_unscored == n_scorable

        # 5. elect next committee
        candidate_ids = [r.node_id for r in results]
        held_over_reputation: list = []
        if self.election == "reputation":
            scores = {r.node_id: self._by_id(r.node_id).reputation_state.reputation for r in results}
            # reputation persists whether or not a node served on committee last
            # round, so incumbents are legitimately still eligible on their
            # accumulated reputation (BtRaI's design intent) -- unless the
            # committee failed this round. A failed committee's reputations are
            # deliberately left untouched (round 20), so re-ranking would seat
            # the same members again indefinitely: with distinct reputations
            # the simulation livelocked (audit, round 24). The paper's remedy
            # is a collective penalty phi (BtRaI Section 4.2 step 3), not
            # implemented here (see rpbft.py); the parameter-free stand-in is
            # that a failed committee's members are ineligible for the very
            # next election only. Their reputations still decide later rounds.
            # reelect_incumbents=False (round 27) applies the same exclusion on
            # every round, not only after a failure: the election is then
            # restricted to this round's trainers, matching the score
            # baseline's forced rotation.
            if not committee_failed and self.reelect_incumbents:
                for cid in self.rpbft.committee:
                    scores.setdefault(cid, self._by_id(cid).reputation_state.reputation)
                    if cid not in candidate_ids:
                        candidate_ids.append(cid)
            elif len(candidate_ids) < self.c_num:
                # Fewer trainers than seats (n_nodes - c_num < c_num): excluding
                # the incumbents leaves too few candidates and the committee
                # silently shrank below c_num (fuzz test, audit round 25).
                # Fill the shortfall from the excluded incumbents, best
                # reputation first -- reputation election may use reputation --
                # and report it as seats_held_over. Non-incumbent candidates
                # keep absolute priority, so the round-24 livelock fix is intact
                # whenever trainers >= c_num.
                held = sorted((cid for cid in self.rpbft.committee if cid not in candidate_ids),
                              key=lambda cid: -self._by_id(cid).reputation_state.reputation)
                held = held[: self.c_num - len(candidate_ids)]
                for cid in held:
                    scores[cid] = self._by_id(cid).reputation_state.reputation
                candidate_ids += held
                held_over_reputation = list(held)
        elif self.election == "score":
            scores = {r.node_id: r.score for r in results}
            # BFLC's original rule has no memory across rounds: a node with no
            # fresh validation score this round (e.g. an incumbent committee
            # member who did not train) is NOT eligible for re-election just
            # because it has a high standing reputation -- backfilling with
            # reputation here would silently leak this package's own
            # integration into the baseline it is meant to be compared
            # against. Incumbents compete again only once they resubmit and
            # earn a fresh score as ordinary trainers.
        else:   # unreachable after the check at the top of run_round(); kept as a guard
            raise ValueError(f"election must be 'reputation' or 'score'; got {self.election!r}")

        self.rpbft.reputations = {n.node_id: n.reputation_state.reputation for n in self.nodes}
        seats_filled_randomly = 0
        seats_held_over = 0
        if self.election == "score":
            # Eligibility under BFLC's rule requires a finite score; -inf is
            # not "last place", it is "not a candidate". Until round 22 the
            # by_score sort merely ranked -inf last, so submitters of NaN
            # updates were seated whenever finite-scored candidates were
            # fewer than c_num, and a mixed failure round (some NaN updates,
            # the rest unscored by the committee) seated the first c_num
            # trainers in list order. Three tiers now apply:
            #   1. finite-scored candidates, best score first (the paper's rule);
            #   2. shortfall filled at random (seeded) from candidates the
            #      committee failed to score -- no fault of theirs;
            #   3. any remaining seats are held over by incumbents, chosen at
            #      random (seeded) -- NOT in reputation order: rpbft.committee
            #      is reputation-sorted, and iterating it here let the
            #      incumbents' reputations decide who stays inside the score
            #      baseline, the same contamination class fixed in v0.1.1
            #      (audit, round 23). Flagged in the round summary. Submitters
            #      of non-finite updates are never seated.
            finite = [r.node_id for r in results if np.isfinite(r.score)]
            new_committee = elect_committee(finite, scores, min(self.c_num, len(finite)), strategy="by_score") if finite else []
            if len(new_committee) < self.c_num:
                pool = [r.node_id for r in results if r.reason in COMMITTEE_SIDE_REASONS]
                k = min(self.c_num - len(new_committee), len(pool))
                if k:
                    new_committee += elect_committee(pool, None, k, strategy="random", rng=self._rng)
                    seats_filled_randomly = k
            if len(new_committee) < self.c_num:
                # Draw over a reputation-blind ordering (node construction
                # order): a seeded draw of *positions* in the reputation-sorted
                # rpbft.committee list would still let reputation pick the
                # identities (caught by the round-23 regression test).
                position = {n.node_id: i for i, n in enumerate(self.nodes)}
                incumbents = sorted((cid for cid in self.rpbft.committee if cid not in new_committee), key=position.get)
                seats_held_over = self.c_num - len(new_committee)
                new_committee += elect_committee(incumbents, None, seats_held_over, strategy="random", rng=self._rng)
        else:
            # reputation election needs no scores; a committee failure leaves
            # reputations untouched, so the ranking is still meaningful.
            if held_over_reputation:   # only set when incumbents were excluded and trainers < c_num
                # trainers take every seat they can; only the shortfall goes to
                # the held-over incumbents (they may out-rank the trainers on
                # reputation, so a plain by_score over the union would re-seat them)
                trainers_only = [c for c in candidate_ids if c not in held_over_reputation]
                new_committee = elect_committee(trainers_only, scores, min(self.c_num, len(trainers_only)),
                                                strategy="by_score") if trainers_only else []
                new_committee += held_over_reputation[: self.c_num - len(new_committee)]
                seats_held_over = len(new_committee) - len(trainers_only)
            else:
                new_committee = elect_committee(candidate_ids, scores, self.c_num, strategy="by_score")
        self.rpbft.committee = sorted(new_committee, key=lambda nid: -self.rpbft.reputations[nid])
        self.rpbft.validators = [n.node_id for n in self.nodes if n.node_id not in set(self.rpbft.committee)]

        round_summary = {
            "n_accepted": len(accepted),
            "n_submitted": len(trainers),
            "n_unscored": n_unscored,                       # updates the committee could not (validly) score
            "n_non_finite": n_non_finite,                   # NaN/Inf updates, rejected before scoring
            "committee_failed": committee_failed,
            "seats_filled_randomly": seats_filled_randomly, # score election: tier-2 seats (see run_round)
            "seats_held_over": seats_held_over,             # score election: tier-3 seats kept by incumbents
            "committee": list(self.rpbft.committee),
            "global_weights": self.global_weights.copy(),
        }
        self.history.append(round_summary)
        self._round += 1
        return round_summary

    def run(self, n_rounds: int) -> list[dict]:
        return [self.run_round() for _ in range(n_rounds)]

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> float:
        return _validation_accuracy(self.global_weights, (X_test, y_test))
