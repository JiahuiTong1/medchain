# Changelog

## v0.1.34 (2026-09-12) -- freeze candidate
Round-34 audit: a closing consistency pass over the whole deliverable
(version strings in six places, test count in four, the
release-to-manuscript mapping of every changelog entry since v0.1.24, CI
YAML, compileall, placeholder inventory, final render). One C-level item,
introduced by v0.1.33's own edit. No code change.

- `tests/test_medchain.py` header: "about half of the suite; each such
  test names its round" -> "about three-quarters of the suite (46 of 62),
  grouped below under the round in which the defect was found" -- the
  count under the file's `round-N audit` section headers, which is what
  identifies each regression test's round.
- **Manuscript v16 -> v17** (`paper/medchain_manuscript_v17.docx`): C1/S1
  -> 0.1.34 only.
- **Verified this round (positive findings).** 0.1.33 consistent in
  pyproject, `__init__`, CITATION.cff, the manuscript's C1/S1 and the
  changelog; 62 consistent in Section 2.1, README, Fig. 1 and the file;
  every entry from v0.1.24 on maps to exactly one manuscript version and
  the current one matches `paper/`; ci.yml parses (3 OS x Python
  3.10-3.14); src/ byte-identical to v0.1.32 apart from the version string.
- **Handover.** Nothing further on the audit side. The authors' remaining
  steps, in order: fill the 11 manuscript placeholders and the author /
  repository fields in `pyproject.toml`, `LICENSE` and `CITATION.cff`;
  push, let CI run, and replace Section 2.1's "has not yet run" with the
  result; transfer the manuscript into the SoftwareX Word template;
  tag, mint the Zenodo DOI, fill C2/S2, and confirm that `pytest` passes
  from a fresh install of the tagged source.

## v0.1.33 (2026-09-12) -- freeze candidate
Round-33 audit: a three-way cross-check of the manuscript, the README and
every module docstring -- all 55 sentences containing a strong claim word
(unchanged / reproduce / closes / implements / verified / exact / never /
always ...) traced to code, tests or the source papers, and the 27 numbers
the three share compared. No new B-level finding; three wording items,
one of them introduced by round 32. No code change.

- Manuscript Section 4: "so they transfer directly" -> "so it transfers
  directly" (the subject became singular in v15).
- README: the convergence tolerance now distinguishes the shipped run
  ("within 0.04") from the test's assertion ("the test allows 0.06"); the
  two numbers previously read as a contradiction against the manuscript.
- `tests/test_medchain.py` header: states that about half of the suite are
  audit regression tests, as Section 2.1 and the README already do.
- **Manuscript v15 -> v16** (`paper/medchain_manuscript_v16.docx`): the
  Section 4 fix; C1/S1 -> 0.1.33. Fig. 1 unchanged.
- **Verified this round (positive findings).** The three-way check found
  every strong claim backed and every shared number consistent; src/
  byte-identical to v0.1.32 apart from the version string.
- **Audit series closed.** From round 26: A-level (an unregistered DOI,
  placeholders) -> B-level code (documentation contradicting behaviour,
  missing input validation, a check placed after side effects) -> B-level
  manuscript accuracy (Example 1, "unchanged") -> wording only. What
  remains is the authors': placeholders (manuscript, `pyproject.toml`,
  `LICENSE`, `CITATION.cff`); the CI workflow's first run and the
  corresponding update of Section 2.1; transfer of the manuscript into
  the SoftwareX Word template.

## v0.1.32 (2026-09-12) -- freeze candidate
Round-32 audit: the first read-through of the README and of every
module-level docstring (the manuscript had its own in round 31), plus an
online check of SoftwareX's current guide for authors. No code change;
one B-level accuracy item of the same kind as round 31's, five wording
items, and one correction to this changelog's own assumptions.

- **"Unchanged" removed from the README and `trustworthy_fl.py`.** Both
  still said medchain reuses BtRaI's model "unchanged", although the
  package documents three deliberate deviations (`rpbft.py`: hard
  carryover cap, no collective penalty phi; `reputation.py`: Eq. 9
  restricted to non-zero ratings, no formula for the PnF-from-CSP rating)
  and the manuscript dropped the word in v3 (round 20) for exactly that
  reason. Both now say "rather than designing a new reputation formula"
  and point to the docstrings that list the deviations.
- **Docstrings and README aligned with the code and manuscript.**
  `bflc.py`'s module docstring referred to `score_fn` and a non-existent
  `aggregate_fn`; it now names `committee_score_fn` and states that
  aggregation is the caller's job. The manuscript's F4, Section 2.1 and
  Section 4 use the real parameter name too, and Section 2.1/4 no longer
  say the *election* function takes a scoring callable (it takes a dict
  of scores). `trustworthy_fl.py`: "directly closes the gap" -> "directly
  targets the gap", as in the manuscript; `reelect_incumbents`'s "same
  p-value" now says both arms sit at the exact test's floor. README: the
  BtRaI bullet states that the token-incentive mechanism is *not*
  implemented; the layout comment for `tests/` mentions the audit
  regression tests.
- **Word limit corrected: 4 000, not 3 000.** SoftwareX's current guide
  sets a maximum of 4 000 words (abstract, running text, captions and
  footnotes; excluding title, authors, affiliations, references and the
  metadata tables) and six figures. Entries from round 13 onward managed
  the manuscript to a 3 000-word limit; by the journal's definition v15
  is about 3 440 words. The clause dropped from F5 in round 27 to save
  words ("callers who want random or multi_factor election end-to-end
  should call elect_committee directly") is restored. The guide also
  states that submissions are accepted only in the journal's Word or
  LaTeX template; the manuscript is generated with docx-js and must be
  transferred into the official template at submission.
- **Manuscript v14 -> v15** (`paper/medchain_manuscript_v15.docx`): the
  items above; body 3 102 -> 3 118 words; C1/S1 -> 0.1.32. Fig. 1
  unchanged.
- **Verified this round (positive findings).** src/ byte-identical to
  v0.1.31 apart from the version string; Example 1's "within 0.04" holds
  (largest deviation 0.039); no `target` wording left in the reputation
  demo; docx free of comments, tracked changes and author metadata.
- **Still open (authors only):** placeholders (manuscript, `pyproject.toml`,
  `LICENSE`, `CITATION.cff`); the CI workflow's first run; transfer of
  the manuscript into the SoftwareX Word template.

## v0.1.31 (2026-09-12) -- freeze candidate
Round-31 audit: `twine check` on the built sdist and wheel (both pass),
and the first end-to-end read-through of the manuscript since v9 --
earlier rounds had reviewed only the paragraphs they changed. No code
change. One B-level manuscript-accuracy finding, present since v2, and
five wording items; all addressed.

- **Example 1 no longer implies a reproduction of BtRaI's Fig. 4.** The
  manuscript said `demo_reputation_dynamics.py` "drives six healthcare
  centres *to* the six steady-state reputations BtRaI reports" (0.96,
  0.84, 0.74, 0.82, 0.88, 0.88). The script uses those six *reported
  outputs* as its service-quality *inputs*; with the default alpha and a
  saturated chain-behaviour term the update rule's fixed point is about
  0.78*input + 0.20, so the centres settle at 0.951, 0.857, 0.779, 0.842,
  0.889 and 0.889 -- within 0.04 of each input, order preserved, but not
  at the stated values (0.74 -> 0.779 is visible in the script's own
  output). The round-2 audit had softened this claim and the test's
  docstring still records the circularity; round 19 re-tightened the
  manuscript wording after verifying the six numbers against the paper's
  text, conflating "the inputs are the paper's numbers" with "the output
  reproduces the paper's figure". Example 1 now says the script feeds
  those levels and shows convergence to within 0.04 of each input, "a
  contraction property of the update rule rather than an independent
  reproduction of the figure"; the script's docstring, header and labels
  say `input` instead of `target` and print the deviation; `run_to_target`
  is renamed `run_at_level`; the README's test summary says the same.
  Test suite unchanged (62; the convergence test already asserted only
  "within 0.06, order preserved").
- **Manuscript v13 -> v14** (`paper/medchain_manuscript_v14.docx`), the
  wording items from the read-through: the Abstract expands PBFT (it
  should be self-contained; Section 1's expansion from round 16 did not
  cover it); Section 2.1's description of the test layer adds "or to a
  defect found during audit", matching Fig. 1; F5's "(both rank by
  score; ...)" -> "(the same ranking, applied to this round's scores or
  to accumulated reputations respectively; ...)"; F3/F6 name the real
  parameters `n_total` / `n_participating` instead of `n`; Section 4's
  closing sentence no longer credits the two parameter-check functions
  with the infiltration result (that is `TrustworthyFLSimulator`'s);
  Example 2's "spreads" sentence and two clauses in F2/F7 shortened to
  pay for the additions. Body 3 088 -> 3 102 words; Abstract 198 -> 203;
  C1/S1 -> 0.1.31. Fig. 1 unchanged.
- **Verified this round (positive findings).** `twine check` passes for
  sdist and wheel; sdist carries CITATION.cff, CHANGELOG.md and
  examples/ and nothing from paper/; src/ byte-identical to v0.1.30 apart
  from the version string; docx free of comments, tracked changes and
  author metadata; Abstract/Section 1/Section 5 numbers mutually
  consistent.
- **Method note.** Rounds 27-29 reviewed only the paragraphs changed in
  the preceding round, which is how the Example 1 wording survived three
  audits; once changes converge, a full read-through (manuscript, README
  and module docstrings) should be the closing step before submission.
- **Still open (authors only):** placeholders (manuscript, `pyproject.toml`,
  `LICENSE`, `CITATION.cff`); the CI workflow's first run.

## v0.1.30 (2026-09-11) -- freeze candidate
Round-30 audit: a review of round 29's changes with three new dimensions
(full suite and both examples under `-W error`; test order shuffled three
ways with pytest-randomly; a fresh-reviewer read-through of F7 and
Examples 2-3). No code change; no A/B-level findings for the second
consecutive round. Three C-level items, all packaging or wording.

- **sdist now ships `CITATION.cff`, `CHANGELOG.md` and `examples/`.** The
  README points to the citation file, the manuscript refers readers to
  the changelog (Section 4) and is built on the two example scripts
  (Section 3), yet `python -m build --sdist` included none of them
  (setuptools' defaults: README, LICENSE, pyproject, `src/`, `tests/`).
  A four-line `MANIFEST.in` adds them; the wheel is unchanged.
- **Manuscript v12 -> v13** (`paper/medchain_manuscript_v13.docx`): F7's
  "neither train nor update while serving" -> "nor have their reputation
  updated" (the object was missing); the ordinary-round eligibility
  sentence now opens with "In ordinary rounds," so it no longer reads as
  contradicting the failed-round exclusion two sentences earlier; F7's
  signature adds `seed`, which Example 2's snippet uses (v9-v12 omitted
  it); C1/S1 -> 0.1.30. Body 3 081 -> 3 088 words. Fig. 1 unchanged.
- **Verified this round (positive findings).** 62/62 under `-W error` in
  both dependency sets (NumPy 2.4.4/SciPy 1.17.1; NumPy 1.26.4/SciPy 1.13.1
  from a clean non-editable install); 62/62 under three random test
  orders; both examples warning-free; `reputation.py`, `rpbft.py` and
  `bflc.py` byte-identical to v0.1.28; the v0.1.29 regression test fails
  against v0.1.28 as claimed.
- **Still open (authors only):** placeholders (manuscript, `pyproject.toml`,
  `LICENSE`, `CITATION.cff`); the CI workflow's first run. Code-level
  audit findings have converged; the next release should be the authors'
  placeholder/first-push release.

## v0.1.29 (2026-09-11) -- freeze candidate
Round-29 audit: a review of round 28's own changes, including a clean
non-editable install of the tarball (NumPy 1.26.4/SciPy 1.13.1,
DeprecationWarning as error) and a check of the per-seed margins behind
the suite's strict assertions (score minus reputation >= 3 seats on
every seed, score minus forced-rotation >= 8). One B-level item -- the
v0.1.28 regression fix was incomplete and its test comment wrong -- and
three wording items. No new tests (62 total); headline numbers unaffected.

- **`run_round()` validates `election` before any side effect.** v0.1.28
  restored the run-time check, but in step 5 (election), after local
  training, aggregation and the reputation update had already run: a
  call with an overwritten `election` raised as intended yet left
  `global_weights` and every reputation advanced by one round while
  `history` and the round counter were not, and the v0.1.28 regression
  test's comment ("the bad round left no trace") was false -- it asserted
  only `len(history)`. The check now runs first; the step-5 `else` is kept
  as an unreachable guard. The test asserts that weights, reputations,
  committee, round counter and the RNG state are all untouched by the
  failed call and that a subsequent valid call runs as an ordinary next
  round; it fails against v0.1.28 at the `global_weights` assertion.
- **Demo output.** The robustness arm's p-value line now carries the same
  "= 2^-20, the floor" annotation as the headline line (both arms sit at
  the floor); its comment on scipy's approximate method now says "about
  45x (more than an order of magnitude)" -- the measured ratio is
  4.25e-5 / 9.54e-7 = 45.
- **Manuscript v11 -> v12** (`paper/medchain_manuscript_v12.docx`):
  Example 2 "understating significance by an order of magnitude" ->
  "by more than an order of magnitude" (45x); the closing "contrasting
  spreads" sentence shortened to keep the body under 3 100 words
  (3 090 -> 3 081); C1/S1 -> 0.1.29. Fig. 1 unchanged (62 tests).
- **Verified this round (positive findings).** Tarball installs cleanly
  from source (non-editable) and passes 62/62 under both dependency
  sets; both `<wp:extent>` and `<a:ext>` match the figure's aspect ratio;
  Highlights <= 79 characters; citations [1]-[6] all resolve to entries;
  no comments/tracked changes/author metadata in the docx.
- **Still open (authors only):** placeholders (manuscript, `pyproject.toml`,
  `LICENSE`, `CITATION.cff`); the CI workflow's first run.

## v0.1.28 (2026-09-11) -- freeze candidate
Round-28 audit: a review of round 27's own changes, re-run in two
environments (NumPy 2.4.4/SciPy 1.17.1 and, for the first time on this
line, NumPy 1.26.4/SciPy 1.13.1 with DeprecationWarning as error), plus
a 600-round fuzz of `reelect_incumbents=False` (0 violations). All
headline numbers identical in both environments. One B-level regression
introduced by v0.1.27, one B-level statistical-wording issue it made
prominent, and five maintenance items; all addressed.

- **`run_round()` again rejects an invalid `election` (regression fix).**
  v0.1.27 moved the check to the constructor and replaced the
  `else: raise` in `run_round()` with a bare `else` for score election,
  so an `election` value overwritten after construction (it is a public
  dataclass field) was silently run as score election. Both checks now
  exist; one regression test (62 total).
- **The reported p-value is the exact test's floor.** With all 20 paired
  differences of one sign, the one-sided exact Wilcoxon test returns
  2^-20 = 9.54e-7 -- exactly the value reported since round 19. The
  round-27 robustness arm therefore reports "the same p-value" not
  because the arms are alike but because both dominate on every seed and
  the test is saturated. The manuscript's Example 2, the README, the demo
  output and the headline test's docstring now say so; the test asserts
  `p == 2**-20` for both arms and relies on seat counts and per-seed
  dominance for the substantive claim.
- **`max_fault_tolerance` raises `ValueError` for non-integer counts**, as
  every other validator in the package does (v0.1.27 used `TypeError`
  there and `ValueError` in `malicious_attack_success_probability` for the
  same fault). The validation is now also documented in the docstring.
- **Counts corrected.** The number of tests that instantiate the
  simulator is 22 of 61 (20 of 58 in v0.1.26); the v0.1.27 entry and the
  round-27 audit report said 28, which counted call sites. Corrected in
  place above.
- `examples/demo_sleeper_attack.py`'s module docstring describes the third
  arm and the carry-over statistic it prints.
- **Manuscript v10 -> v11** (`paper/medchain_manuscript_v11.docx`):
  Example 2 states that p = 2^-20 is the floor for 20 same-signed
  differences and describes the robustness arm as "again strictly better
  on all 20 seeds" rather than "at the same p-value"; the scipy-default
  parenthetical shortened to pay for it; F7's signature lists
  `reelect_incumbents`, matching Fig. 1; Fig. 1's display extent
  corrected to the image's aspect ratio (v10 stretched it 1.5%
  horizontally; v9 0.8%); test count -> 62; C1/S1 -> 0.1.28.
- **Verified this round (positive findings).** 61/61 (now 62/62) tests
  and identical demo output under NumPy 1.26.4/SciPy 1.13.1 and
  2.4.4/1.17.1; `reelect_incumbents=False` fuzz (120 configurations x 5
  rounds, NaN submissions, whole/partial committee failures): committee
  size, uniqueness, exact hold-over accounting, trainer priority and
  finite weights all hold; CITATION.cff valid; docx free of comments,
  tracked changes and author metadata.
- **Still open (authors only):** placeholders (manuscript, `pyproject.toml`,
  `LICENSE`, `CITATION.cff`); the CI workflow's first run.

## v0.1.27 (2026-09-11) -- freeze candidate
Round-27 audit: an independent end-to-end re-audit of v0.1.26 and
manuscript v9 (full reproduction of every reported number, reference
verification with DOI resolution, docx and packaging checks, and a
behavioural probe of committee turnover). All reported numbers reproduced
exactly; 58/58 tests, pyflakes and `python -m build` clean. Two A-level
and three B-level findings, all addressed below except the author
placeholders.

- **Reference [2] removed.** "Blockchain-based federated learning for
  privacy-preserving medical data sharing", *IEEE JBHI* 25(10):3640-3651,
  had been flagged since round 19 as unlocatable. This round its DOI
  (10.1109/JBHI.2021.3098841) was resolved through doi.org and returned
  **404** -- unregistered -- and title/author/volume searches of IEEE
  Xplore and dblp found nothing; the only occurrence anywhere is one
  third-party reference list that also contains obviously spurious
  entries. The manuscript's Section 1 clause ("...was extended to
  medical data sharing specifically by Li, Jiang, Chen, Luo and Wen
  [2]"), reference-list entry [2], the README bullet and the
  `CITATION.cff` entry (with its audit note) are removed; [3]-[7] are
  renumbered [2]-[6]; `bflc.py`'s docstring records the removal. If the
  authors do hold the paper, restore all four and re-verify the DOI.
- **`TrustworthyFLSimulator` docstring corrected; committee stickiness
  disclosed; `reelect_incumbents` added.** The Limitations paragraph
  claimed that "no committee member can serve two consecutive rounds
  under either election rule". True for `election="score"` (0 of 2 340
  seat transitions carried over in the 20-seed benchmark) but false for
  `election="reputation"`, whose incumbents are deliberately kept
  eligible: 1 806 of 2 340 seats (77.2%) carried over and one node sat
  for 34 consecutive rounds. Members neither train nor update their
  reputation while serving, so a node that reaches the top c_num stays
  -- the reputation-monopolisation risk BtRaI's carryover cap and Yang &
  Li both target -- and the two arms of the headline comparison differed
  in rotation as well as in ranking quantity. Counterfactual: with
  election restricted to the round's trainers (the score baseline's
  forced rotation), reputation election gives **0.90 (SD 2.15)** sleeper
  seats, a 94.8% reduction, 14/20 zero-infiltration seeds, exact
  Wilcoxon p = 9.5e-7 -- the headline result does not depend on the
  committee failing to rotate. That variant is now a constructor flag,
  `reelect_incumbents` (default `True`, unchanged behaviour; `False`
  restricts reputation election to this round's trainers and holds the
  shortfall over from the best-reputation incumbents, reported as
  `seats_held_over`; rejected under `election="score"`, where it would
  change nothing). `election` is also validated at construction. The
  demo prints all three arms and the carry-over fractions; the headline
  test gains the third arm and now asserts `<` (the manuscript has said
  "strictly better" since v4; the test still said `<=`). Headline
  numbers unaffected.
- **Rating-channel instantiation disclosed.** Within the simulator all
  three BtRaI rating channels receive the same scalar (the committee's
  median validation score) and `csp_reputation` and the chain-behaviour
  term are constants, so the comprehensive reputation reduces to
  `0.79*score + 0.196` with the default alpha; the multidimensional
  structure is exercised only when `reputation.py` is driven directly
  (Example 1). Stated in a code comment and in manuscript F7.
- **`max_fault_tolerance` and `malicious_attack_success_probability` now
  validate their inputs.** They were the only public functions without
  validation -- and the two the manuscript recommends as pre-deployment
  parameter checks. `max_fault_tolerance(4, 10)` returned
  `validator_fault_tolerance=-3` and `improvement=-1`; a fraction above 1
  made `malicious_attack_success_probability` return `nan`; both
  silently. Now: integer counts with `1 <= c_num < n_total`; positive
  integer `n_participating` and finite fractions in [0, 1] (boundaries
  0 and 1 remain legal).
- **Docstrings.** `rpbft._ranked_ids` documents its lexicographic tie-break
  ("H10" < "H2"), which fixes the first committee to the c_num smallest
  ids when all reputations are equal (the demo's initial committee is
  therefore H0/H1/H10, two of them sleepers, in both arms alike).
- **Tests.** Three new (61 total): the `reelect_incumbents` flag and its
  hold-over invariant, input validation of the two deployment-check
  functions, and first coverage of `TrustworthyFLSimulator.evaluate`.
- **Manuscript v9 -> v10** (`paper/medchain_manuscript_v10.docx`): [2]
  removed and references renumbered; F7 discloses the rating-channel
  instantiation and the incumbent carry-over; Example 2 reports the
  forced-rotation robustness check (0.90 seats, same p); Example 3 notes
  the new input validation; F3 "forces eviction" -> "would force";
  Section 2.1 "Table 2 (S5/C6)" -> "Tables 1-2 (C6/S5)"; Fig. 1 redrawn
  with 61 tests and a test-coverage line to recipes/ (22 of the tests
  instantiate the simulator -- *corrected in round 28: this entry and the
  round-27 audit report originally said 28, which was the number of
  call sites, not tests*; the earlier figure showed none); the
  audit-narration sentences in F2, F7 and Example 2 that carried no
  information for readers were removed to pay for the additions; C1/S1
  -> 0.1.27.
- **Verified this round (positive findings).** References [1], [3] (now
  [2]), [6] (now [5]) and [7] (now [6]) resolve to the cited works;
  `actions/checkout@v6` and `actions/setup-python@v6` exist; the docx
  carries no comments, tracked changes or author/tool metadata;
  Highlights are all <= 85 characters; the README quick start runs.
- **Still open (authors only):** all author/affiliation/funding/CRediT/
  generative-AI placeholders in the manuscript, `pyproject.toml`
  (`authors`), `LICENSE` and `CITATION.cff` (`authors`,
  `repository-code`); the CI workflow's first run.

## v0.1.26 (2026-09-03) -- freeze candidate
Round-26 audit extended randomized fuzzing to the direct APIs of the
three modules. Reputation updates (3 000 trials), committee validation
and election (1 000), and the attack-probability formula (200) showed no
invariant violation. RPBFT rotation did.

- **Anti-collusion replacements now exclude previous committee members.**
  `rotate_committee` drew replacements from "validators not on the new
  committee"; a previous member that had just dropped out of the top
  c_num is often the best-ranked validator, and swapping it back in left
  the carryover count above the cap. Present since v0.1.0. Under
  drifting reputations 46.7% of rotations breached the cap (worst excess
  5 seats); the round-8 test never saw it because it rotated with fixed
  reputations, so the ranking never changed and the replacement path was
  never taken. The construction-time enforceability check is unchanged
  (with K carryovers the eligible pool has n - 2*c_num + K members and
  K - cap are needed, so the condition n >= 2*c_num - cap does not
  depend on K). After the fix the round-26 drift benchmark (3 310
  rotations) and sequence fuzz (4 404 steps) show 0 breaches. Not used
  by the simulator; headline numbers unaffected. Manuscript F3's
  statement of the rule is now true for the direct API.
- `test_anti_collusion_caps_carryover` now drifts a quarter of the
  reputations before every rotation; new fixed-seed property test
  `test_rpbft_rotation_invariants_under_random_drift` (120 random
  configurations x 10 blocks, six invariants). 58 tests total.
- README states the `n_nodes >= 2 * c_num - collusion_cap` constraint
  next to the module (with the default cap the round-20 check rejects
  roughly c_num > 2/3 of the network).
- **Manuscript v8 -> v9** (`paper/medchain_manuscript_v9.docx`): C1/S1 ->
  0.1.26; test count -> 58 (no wording change: F3's claim stands as
  written once the fix is in).
- **Still open:** reference [2].

## v0.1.25 (2026-09-03) -- freeze candidate
Round-25 audit introduced randomized fuzzing (300 simulations, random
network/committee sizes, both election modes, injected NaN submissions
and whole/partial committee failures) against seven structural
invariants that had never been asserted. One invariant failed, 62 times,
all in one place.

- **Reputation election no longer shrinks the committee.** The round-24
  exclusion of a failed committee's members left too few candidates
  whenever there were fewer trainers than seats (n_nodes - c_num <
  c_num), and the next committee silently had fewer than c_num members
  (with `min_scored` shrinking accordingly) until the following round.
  Trainers now take every seat they can; the shortfall is filled by the
  excluded incumbents, best reputation first (reputation election may use
  reputation), and reported as `seats_held_over`. Non-incumbents keep
  absolute priority, so the round-24 livelock fix is unchanged whenever
  trainers >= c_num. Score election was already covered by its tier-3
  hold-over and had zero fuzz hits.
- **Fuzz test kept as a property test.** `test_simulator_invariants_under
  _random_failures` runs 60 fixed-seed simulations x 5 rounds (300 rounds,
  ~10 s) asserting: committee size == c_num, no duplicate seats, seats
  are known ids, finite global weights, reputations finite in [0, 1], the
  round accounting identity, and tier-flag bounds. The full 300 x 8 run
  from the audit passes with 0 violations after the fix.
- One regression test for the shrink (57 tests total). Headline numbers
  unaffected.
- **Manuscript v7 -> v8** (`paper/medchain_manuscript_v8.docx`): F7
  notes that seats which cannot otherwise be filled are held over; C1/S1
  -> 0.1.25; test count -> 57.
- **Still open:** reference [2].

## v0.1.24 (2026-09-02) -- freeze candidate
Round-24 audit: run-to-run determinism (including 20 consecutive
shortfall rounds), deep-copy isolation after the v0.1.20 write-back, and
the long-run behaviour of a *persistently* failing committee. The first
two passed; the third exposed a livelock.

- **A failed committee can no longer re-elect itself under
  `election="reputation"`.** Round 20 made a committee-side failure leave
  every reputation untouched; round 22 gave the score mode a way out
  (incumbents have no score, so tier 2 draws fresh members). The
  reputation mode had none: the failed members kept the top reputations
  and were re-seated every round -- with distinct reputations the
  simulation froze (same committee, no reputation change, no weight
  update, `committee_failed` raised every round). This is the situation
  BtRaI's collective penalty phi (Section 4.2 step 3) exists for; phi
  remains unimplemented (v0.2). The parameter-free stand-in: a failed
  committee's members are ineligible for the immediately following
  election only, so with persistent failure the committee alternates
  instead of freezing, and their reputations still rank them afterwards.
  The round-21 test that encoded the old re-seating as expected was
  updated; one new regression test (55 total). Headline numbers
  unaffected (no committee failure occurs in the reported runs).
- **Manuscript v6 -> v7** (`paper/medchain_manuscript_v7.docx`): F7
  discloses the one-election exclusion; F7 split into two paragraphs at
  the degenerate-round material for readability; a 22-word clause
  duplicating F1's "independent reuse" point removed to pay for the
  addition (2 980 words); C1/S1 -> 0.1.24; test count -> 55.
- **Still open:** reference [2].

## v0.1.23 (2026-09-02) -- freeze candidate
Round-23 audit: behavioural probe of v0.1.22's three-tier score
election, plus first-time submission-format and docx-metadata checks
(all passed: Highlights <= 85 chars, C1-C9/S1-S8 present, document
properties carry no author/tool name, no comments or tracked changes).

- **Score-election hold-over is now reputation-blind.** Tier 3 iterated
  `rpbft.committee`, which is reputation-sorted, so under
  `election="score"` the incumbents' reputations decided who kept a
  seat -- the contamination class fixed in v0.1.1, in a narrow corner
  (only when finite-scored and committee-side-unscored candidates
  together fall short of `c_num`; no reported number is affected).
  Held-over seats are now drawn with the simulator's seeded generator
  over the incumbents in node-construction order. The first attempt
  drew positions in the reputation-sorted list, which the new regression
  test exposed as still reputation-dependent; the ordering fix is what
  shipped.
- `seed` docstring corrected: the generator also drives the tier-2/3
  draws, so a shortfall round shifts the later malicious-noise stream;
  ordinary rounds make no other random draws.
- One new regression test (54 total): permuting incumbents' reputations
  cannot change which seats are held over under score election.
- **Manuscript v5 -> v6** (`paper/medchain_manuscript_v6.docx`): F5 no
  longer claims the two election modes share one algorithm apart from
  the scores dict; F7 discloses the held-over-incumbent fallback (a
  flagged deviation from BFLC's no-re-election rule); C1/S1 -> 0.1.23;
  test count -> 54.
- **Still open:** reference [2].

## v0.1.22 (2026-09-02) -- freeze candidate
Round-22 audit: combination-scenario probing of the round-21 committee-
failure fallback. One B-level finding, the most substantive since round
19: under `election="score"` eligibility never required a finite score.

- **Score election now requires a finite score.** `by_score` merely ranked
  `-inf` last, so (a) whenever fewer than `c_num` candidates had a finite
  score, submitters of NaN updates were seated on the next committee --
  reachable without any committee failure, simply by more garbage
  submissions than honest ones in a round; and (b) a *mixed* failure round
  (some NaN updates, the rest unscored by the committee) did not meet the
  round-21 `committee_failed` definition, so its random fallback did not
  fire and the first `c_num` trainers in list order were seated, NaN
  submitter included. `run_round()` now applies three tiers under score
  election: finite-scored candidates best-first (the paper's rule); a
  shortfall filled at random (seeded) from candidates the committee failed
  to score; any remaining seats held over by incumbents in reputation
  order. Submitters of non-finite updates are never seated. The round
  summary gains `n_non_finite`, `seats_filled_randomly` and
  `seats_held_over`; `committee_failed` is redefined as "every scorable
  submission went unscored for a committee-side reason" (a round of only
  NaN submissions is the submitters' failure, not the committee's).
  Reputation election is unchanged. Headline numbers unaffected (no
  non-finite submissions occur in the reported runs). Found and fixed in
  the same round: the tier-3 loop initially iterated a `set` of incumbent
  ids, i.e. in hash order rather than reputation order.
- **`min_scored` validated** to `[1, committee size]` (0 was a silent
  no-op; a value above the committee size made every round a committee
  failure).
- **Random election preserves id types**: `elect_committee(strategy=
  "random")` indexed the candidate list through `rng.choice`, which
  returned `np.str_`/`np.int64` that then leaked into `rpbft.committee`
  and `history`.
- **Docstrings**: `CommitteeValidationResult` now lists all four `reason`
  values; `run_round` documents every summary key.
- Three new regression tests (53 total).
- **Manuscript v4 -> v5** (`paper/medchain_manuscript_v5.docx`): F7
  states the eligibility rule in one sentence; Example 1's parenthetical
  about an earlier, never-submitted draft's 4.5x figure removed (no
  information for readers; same rationale as the Tables 3-4 sentence
  removed in v4) to stay under the word limit; C1/S1 -> 0.1.22; test
  count -> 53 in Section 2.1 and Fig. 1.
- **Still open:** reference [2].

## v0.1.21 (2026-09-02) -- pre-submission freeze candidate
Round-21 audit: a review of round 20's changes. No A-level or
formula/number-level findings; one B-level behaviour left undefined by
the round-20 committee-failure handling, plus direct-API validation
gaps and three manuscript wording items. Reference [2] remains with
the authors. Rounds 19-21 have shown steadily diminishing returns; the
remaining design-level items (gamma rename, epoch rotation, phi
penalty) are deferred to v0.2 rather than risked in further point
releases.

- **Committee-failed rounds under `election="score"` are re-elected at
  random, not by list order.** With every candidate at `-inf`, the
  by_score sort silently seated the first `c_num` trainers in input
  order. `run_round()` now falls back to BFLC's own random-election
  strategy (`elect_committee(strategy="random")`, driven by the
  simulator's seeded generator) for that case only; under
  `election="reputation"` the untouched reputations still rank the
  candidates and nothing changes. Documented in F7. The headline
  numbers are unaffected (no committee failure occurs in the reported
  runs).
- **`validate_updates(min_scored=...)`.** A verdict resting on a single
  finite member score (the other members having failed) was recorded as
  `n_scored=1` but still accepted, forfeiting the median's robustness to
  one dishonest member. `min_scored` (default `None`, previous
  behaviour) rejects such updates with `reason="too_few_member_scores"`;
  the simulator passes a committee majority (`c_num // 2 + 1`) and
  treats the case as a committee-side failure. `COMMITTEE_SIDE_REASONS`
  is exported for callers that update reputations themselves.
- **Direct-API validation.** `RPBFTState` now rejects duplicated
  `node_ids` (a duplicate landed on both the committee and the validator
  side; the simulator has checked this since round 7) and reputations
  missing an entry for any node; `elect_committee` (by_score and
  multi_factor) reports which candidates have no score instead of
  raising a bare `KeyError`.
- Three new regression tests (50 total).
- **Manuscript v3 -> v4** (`paper/medchain_manuscript_v4.docx`): F3
  mentions the construction-time enforceability condition; F4 mentions
  the majority requirement; F7 describes the committee-failure
  fallback; Example 2 "no worse on every one of the 20 seeds" ->
  "strictly better on all 20 seeds" (which is what the data show);
  Fig. 1 caption "dashed arrows" -> "dashed lines"; C1/S1 -> 0.1.21;
  test count -> 50. *(Addendum, round 22: two edits were omitted from
  this list -- Example 3's sentence about an earlier draft having
  mis-cited the paper's Tables 3-4 was removed as carrying no
  information for readers, and F7's new sentence was shortened; both to
  stay under the 3 000-word limit.)*
- **Still open:** reference [2] (JBHI 25(10):3640-3651) in the
  manuscript, README and CITATION.cff.

## v0.1.20 (2026-09-02)
Round-20 audit: a review of round 19's own changes. No new A-level
defects; four B-level findings (three introduced by v0.1.19 / manuscript
v2) and twelve maintenance items, all addressed below except reference
[2], which remains with the authors.

- **Committee-side failure no longer penalises trainers.** v0.1.19 mapped
  every non-finite score to 0 reputation credit. When *no* committee
  member produced a finite score (every member's score_fn returned
  NaN/Inf), every update was rejected with `-inf` and every trainer's
  reputation fell 0.5 -> 0.318 -- v0.1.18's undeserved reward had become
  an undeserved penalty for a failure on the committee's side.
  `CommitteeValidationResult` now carries `n_scored` (finite member
  scores used) and `reason` (`None`, `"non_finite_update"` or
  `"no_finite_member_score"`); `run_round()` skips the reputation update
  for unscorable submissions and reports `n_unscored` and
  `committee_failed` in the round summary. A NaN *update* is still the
  submitter's fault and still receives 0 credit. Two regression tests
  replace the round-19 NaN-score test, whose scenario is now split into
  these two cases.
- **Anti-collusion enforceability checked at construction.** Whether
  `rotate_committee` can always honour `collusion_cap` depends only on
  (n_nodes, c_num, collusion_cap): the worst-case excess is
  `c_num - collusion_cap`, so `n_nodes - c_num >= c_num - collusion_cap`
  is required. v0.1.19 raised only when a rotation actually hit the
  shortfall -- i.e. in the middle of a rejected-block recovery.
  `RPBFTState.__post_init__` now rejects such configurations with the
  minimal fix spelled out; the in-rotation check is kept as a guard.
  `TrustworthyFLSimulator` passes `collusion_cap=c_num-1` explicitly (a
  no-op cap; it never rotates) so small simulations such as four nodes
  with `c_num=3` are unaffected.
- **Validated shards are written back as arrays.** A list-of-lists shard
  passed the round-19 shape checks (done on `np.asarray` copies) and then
  failed on `.shape` inside `_local_fit`. The coerced float arrays now
  replace the originals on the simulator's private deep copy.
- **gamma naming clarified.** `gamma_up` is the paper's gamma_1 -- the
  *larger* rate, applied when reputation *falls*; `gamma_down` is gamma_2,
  applied when it rises. The suffixes describe the rate's size, not the
  direction of the change. Documented on the dataclass fields and in
  `adaptive_learning_rate`; names kept for backward compatibility, a
  rename (`gamma_fall`/`gamma_rise`) is a candidate for v0.2.
- **Packaging and CI currency.** `license = "MIT"` / `license-files`
  per PEP 639 (build backend floor raised to setuptools>=77; the
  `License ::` classifier removed); `actions/checkout@v6` and
  `actions/setup-python@v6`. Verified with an isolated build in a clean
  virtual environment.
- **Tests** now assert what the manuscript states: reputation election is
  no worse than score election on all 20 seeds; the count of
  zero-infiltration seeds (15) is asserted loosely (>= 12) to tolerate
  floating-point differences across the CI platforms. 47 tests total
  (46 - 1 + 2).
- **Manuscript v2 -> v3** (`paper/medchain_manuscript_v3.docx`): Section 1
  "reuses BtRaI's published model unchanged" -> "rather than designing a
  new reputation formula" (the package documents three deliberate
  deviations); Section 4 "the only public BFLC code" -> "a public BFLC
  demonstration"; F2 states the gamma_up = gamma_1 / gamma_down = gamma_2
  mapping; F4/F7 mention `n_scored` and the committee-failure flag; the
  Abstract's "of 102 possible" given its context; C6 -> "NumPy >= 1.22
  (tested 1.26 and 2.4)"; reference [7] no longer carries an unverified
  year; C1/S1 -> 0.1.20; test count -> 47; Fig. 1 test count updated.
- **Still open:** reference [2] (JBHI 25(10):3640-3651) remains in the
  manuscript (Section 1 and reference list), README and CITATION.cff and
  must be verified or removed by the authors.

## v0.1.19 (2026-09-02)
Round-19 audit: three new audit dimensions -- reference verification,
equation-by-equation comparison against the two source papers' full
texts (obtained for the first time this round), and adversarial-input
probing -- plus an environment-currency sweep. Code fixes below; the
manuscript has been revised accordingly (`paper/medchain_manuscript_v2.docx`
replaces v1; the list of manuscript edits is at the end of this entry).

- **NaN score gave full reputation credit (direction-reversal, severe).**
  `run_round()` clamped each submitter's score with
  `max(0.0, min(1.0, score))`; Python's `min(1.0, nan)` is `1.0`, so a
  rejected update whose median score was NaN earned the reputation of a
  perfect one. Reproduced with a committee member holding an empty shard
  (`_validation_accuracy` -> `mean([])` -> NaN, `np.median` -> NaN):
  `n_accepted` was 0 yet every trainer's reputation rose 0.5 -> 0.695.
  Round 18 guarded NaN *updates*, not NaN *scores*. Fixed in three places:
  non-finite scores now map to 0 credit; `validate_updates` drops
  non-finite member scores before taking the median (one faulty member
  can neither veto nor distort, the same robustness argument the median
  is there for) and returns `-inf` only if no member score is finite;
  and `TrustworthyFLSimulator` validates every shard at construction
  (2-D X, 1-D y, matching row counts, non-empty, one shared feature
  count), turning the previous mid-run numpy broadcasting errors into
  clear `ValueError`s. NaN-valued *entries* remain allowed (round-18
  behaviour unchanged).
- **NaN passed every parameter validator.** All range checks added in
  rounds 2-10 were written as comparisons (`x < 0`, `x <= 0`,
  `0 <= x <= 1`, `|sum-1| > eps`), each of which is False for NaN, so
  `omega=nan`, `alpha=(nan,0,0,0)`, NaN ratings and NaN `csp_rating`
  were accepted silently and produced NaN reputations. `np.isfinite`
  checks added to `_check_convex_weights`, `_check_positive_omega`,
  `_check_reputation_range`, `_check_gamma_order`, `_check_unit_interval`,
  `credibility_weighted_score` and `behavior_score`. Error-message
  prefixes are unchanged so existing `match=` assertions still hold.
- **Eq. (8) fidelity fix (`update_pnf_reputation`).** The paper computes
  the credibility `Hcr` from the *raw* ratings and applies the waste
  penalty `eta` only inside the weighted sum. The previous
  implementation penalised first and then computed credibility on the
  penalised vector, so a per-HC penalty also made that rating an
  outlier and down-weighted it a second time. Identical for uniform
  `eta` (the only case the earlier test exercised); for
  `hr=[0.9,0.85,0.9,0.88], eta=[1,1,3,1]` the HR term moves from 0.6050
  to the paper's 0.7198. `waste_penalty` may now also be a scalar.
- **`behavior_score` count validation.** The five chain-behaviour
  quantities had no sign check (missed by the round-10 sweep):
  `wr_num=-1` raised `ZeroDivisionError`, `ac_num=-5` produced 0.0067,
  below the documented [0.5, 1) range. All five must now be finite and
  non-negative (the paper's `f_bar` is a 1-5 scale; only non-negativity
  is enforced).
- **`rotate_committee` no longer partially enforces the cap.** With fewer
  spare validators than excess carryover seats (`zip` truncation), it
  silently replaced only as many as it could -- e.g. n=5, c=4, cap=0
  left 3 carryovers. Now raises `ValueError` naming the configuration.
- **`max_fault_tolerance` returns the exact component sum as well.** All
  four formulas were verified verbatim against Liu et al. Section 5(3),
  but the paper's closed form floor((3N-c-1)/6) is not equal to
  floor((c-1)/3)+floor((N-c)/2): they differ by 1 for 6 632 of the
  19 897 (N, c) pairs with 4 <= N <= 200 (e.g. N=100, c=5: 49 vs 48).
  The closed form is kept under its existing key for continuity;
  `rpbft_total_exact_fault_tolerance` and `improvement_exact` are new.
- **RPBFT rule deviation documented.** The paper's step (4) replaces a
  *fixed* ceil((c-1)/2) carryover nodes when the threshold is exceeded;
  this package replaces `carryover - cap`, i.e. enforces a hard cap
  (stricter for excess > 1). The module docstring now says so, and no
  longer claims the step-(3) collective reputation penalty `phi`, which
  was never implemented.
- **Attribution.** The "susceptible to mixing malicious nodes into the
  committee" sentence quoted in `trustworthy_fl.py`, the README and the
  manuscript comes from Yang & Li, *Connection Science* 36(1):2316018
  (2024), doi:10.1080/09540091.2024.2316018 -- a primary paper that goes
  on to propose its own reputation-based committee consensus, not a
  survey. Now cited and differentiated in the docstring and README. The
  public FISCO-BCOS implementation `iammcy/BFLC-demo` is acknowledged.
- **Reference to verify.** "Blockchain-based federated learning for
  privacy-preserving medical data sharing", *IEEE JBHI* 25(10):3640-3651
  (doi:10.1109/JBHI.2021.3098841) could not be located on IEEE Xplore,
  dblp or via its DOI during audit. Flagged in `CITATION.cff` and no
  longer relied on in `bflc.py`'s docstring; must be confirmed or
  removed before submission.
- **Verified this round (positive findings).** Eq. (1)-(6), Eq. (5), the
  gamma rule, Table 2 defaults, the BFLC median rule, the three election
  strategies, the hypergeometric attack formula and the "committee will
  not be re-elected" rule all match the papers. The six Fig. 4 targets
  used by `demo_reputation_dynamics.py` and the convergence test are
  exactly the levels the paper reports in Section 6.1 ("0.96, 0.84,
  0.74, 0.82, 0.88, and 0.88"); the v0.1.2 "not independently
  re-verified" caveat is withdrawn in the example's docstring.
- **Two manuscript-facing numbers re-derived and re-based.** (a) The
  statistic reported as "post-defection committee seats" (12.95 -> 1.10)
  actually counted *post-defection rounds in which at least one sleeper
  held a seat* (of 34). The headline metric is now the raw number of
  sleeper seats in those rounds (of 102): 17.30 (SD 2.60) -> 1.10 (SD
  3.18), a 93.6% reduction, reputation no worse than score on all 20
  seeds (15 with zero infiltration), one-sided exact Wilcoxon p =
  9.5e-7 (approximate method: 4.2e-5). SDs are now sample (ddof=1)
  values; the test asserts on the seat metric and the demo prints the
  rounds view as a secondary statistic. (b) The "roughly 4.5x
  loss-vs-gain" of v0.1.6 was an input-asymmetry effect (0.98 and 0.10
  sit +0.22 / -0.66 from the neutral input 0.7595 at baseline 0.8); the
  update rule's own asymmetry is exactly gamma_up/gamma_down = 1.5, which
  is what Example 1 now reports (inputs +/-0.15 about neutral: gain
  +0.047, loss -0.071). The demo prints both setups.
- **Environment currency.** Python 3.9 reached end-of-life on
  2025-10-31 and 3.10 does so on 2026-10-31; `requires-python` is now
  `>=3.10`, the CI matrix is 3.10-3.14, classifiers list each version,
  and `scipy>=1.9` (the `wilcoxon(mode=...)` keyword used since round
  17 has been an undocumented alias of `method=` since 1.9; switched).
  The full suite passes on NumPy 2.4.4 / SciPy 1.17.1 with no
  deprecation warnings. Seven unused imports removed (pyflakes clean);
  `seed` and `csp_rating` docstrings corrected; the tests file header no
  longer says "v0.1.0" or attributes rpbft.py to Li et al.
- Seven new regression tests (46 total, up from 39).

**Manuscript edits applied in `paper/medchain_manuscript_v2.docx`:**
headline metric re-based to sleeper seats (17.30 -> 1.10, p = 9.5e-7,
no worse on all 20 seeds) in the Abstract, Sections 1, 3 and 5 and the
Example 2 code comment; the stale "roughly three-quarters" in Section 1
replaced (~94%); Example 1 rewritten around symmetric inputs with the
1.5x = gamma_1/gamma_2 result and a one-sentence note on why the earlier
4.5x was an input artefact, and its Fig. 4 hedge replaced by the verified
Section 6.1 levels; F2's "4.5x" parenthetical updated; new references
[6] Yang & Li (2024) and [7] BFLC-demo, cited in Sections 1, 4 and 5,
with the contribution repositioned against [6]; Fig. 1 redrawn to the
real import graph (only trustworthy_fl -> bflc / reputation / rpbft) with
46 tests; F3 "BFLC/BtRaI" -> "BtRaI" plus the cap-variant and
closed-form-vs-exact notes; F4 and F7 updated for the non-finite member
score and shard validation; Highlights "proven" -> "documented"; SD
convention stated; C1/S1 -> 0.1.19, C6 -> Python 3.10-3.14 (NumPy
1.22-2.x), S6 -> scipy>=1.9, test count -> 46; audit-narration wording
trimmed in F1/F2/F3/F5/F7/Example 2/Section 2.1 to keep the body at 2 898
words (2 978 including code snippets) under the 3 000 limit. **Still
open:** reference [2] (JBHI 25(10):3640-3651) is unchanged in the
manuscript and must be verified or removed by the authors before
submission.

## v0.1.18 (2026-08-24)
Round-18 audit: the most severe finding since v0.1.1's original
statistical-contamination bug and v0.1.8's alpha/beta/delta
direction-reversal defect. A NaN-contaminated update could permanently
corrupt the global model while the simulation reported normal operation
throughout, with no error or warning at any point.

- **`validate_updates` now rejects non-finite (NaN/Inf) updates before
  scoring**, rather than relying on the resulting score to reflect the
  corruption. Root cause: this package's own `_validation_accuracy`
  computes `pred = (p >= 0.5)`, and under IEEE 754 rules a NaN
  comparison always evaluates to `False` -- so an all-NaN weight vector
  silently becomes "predict the negative class on every sample," which
  is not NaN and can score as an ordinary, plausible number depending on
  the validation set's class balance. Demonstrated during audit: a
  single node with entirely NaN training data (a realistic outcome of a
  malformed data pipeline, not only a deliberate attack) got its update
  accepted by the committee and corrupted `global_weights` to all-NaN
  within 2 rounds of a 15-round simulation; every subsequent round
  reported a normal-looking `n_accepted` count with no indication
  anything had gone wrong. This is a genuine gap in the
  "Byzantine-robust median-based validation" this package advertises:
  the median-of-committee-scores mechanism itself was never at fault
  (verified since round 1) -- the scoring function it depends on was
  simply not defending against non-finite input at all.
  `validate_updates` now checks each array-like update with
  `np.isfinite` before calling the caller-supplied `committee_score_fn`;
  non-finite updates are marked `accepted=False` with `score=-inf`,
  independent of what any scoring function would have returned.
  Updates that are not array-like (anything `np.asarray` cannot coerce)
  are left to `committee_score_fn`, since "finite" is not a meaningful
  concept for an arbitrary object.
- Two new regression tests: one confirming NaN/Inf updates are rejected
  at the `validate_updates` level while legitimate updates are
  unaffected, one confirming a full 15-round simulation with a
  NaN-corrupted node's data completes with `global_weights` remaining
  finite throughout (39 tests total, up from 37; also fixed a missing
  `_validation_accuracy` import needed for the first of these tests).

## v0.1.17 (2026-08-24)
*(Superseded in v0.1.19: the headline statistic was re-based from
"rounds with >= 1 sleeper" to sleeper seats, so the p-value reported here
(1.9e-06) became 9.5e-07; the exact-method point stands.)*

Round-17 audit: a statistical-methodology transparency fix. The
qualitative conclusion is unchanged (both the approximate and exact
Wilcoxon calculations strongly reject the null), but the specific
p-value reported was silently dependent on an unstated scipy default.

- **`stats.wilcoxon` calls now explicitly pass `mode="exact"`** in both
  `examples/demo_sleeper_attack.py` and the corresponding test. The 20
  paired differences (score-mode vs. reputation-mode post-defection
  committee seats) contain many tied absolute values (13 five times, 14
  four times, 12 three times, ...); scipy's default `mode="auto"`
  silently falls back to a normal approximation whenever ties are
  present, which is what the code had been relying on without saying so.
  That approximation gives p = 4.91e-05; the exact calculation, fully
  supported at this sample size (n=20), gives p = 1.91e-06 -- both
  comfortably below 0.0001 and both leading to the same conclusion, but
  differing by roughly an order of magnitude as raw numbers, and only
  one of them is what "the Wilcoxon test" means without the qualifier.
  Cross-checked `zero_method` (wilcox/pratt/zsplit) separately: it has no
  effect on this dataset, since none of the 20 paired differences are
  exactly zero.
- **Manuscript Example 2 updated** to name the exact method explicitly
  and report the precise resulting p-value (1.9e-06) rather than only
  the previously-used inequality "p < 0.0001" (which remains true under
  either method and is left unchanged in the Abstract and Conclusions
  for brevity). No test assertions changed (they check `p < 1e-3`, which
  holds either way).

## v0.1.16 (2026-08-24)
Round-16 audit: a methodology change (fresh-reviewer read-through
instead of another citation/format sweep, per the plan stated at the end
of round 15 to rotate through different structural dimensions each
round). No code/test change; one readability fix to the manuscript.

- **Expanded the "PBFT" acronym at its first prose occurrence.** PBFT
  appears repeatedly throughout the manuscript (Abstract, Section 1, F3)
  but was never spelled out; a reader unfamiliar with distributed
  consensus algorithms had no way to learn what it stood for short of
  inferring it from reference [5]'s title. Contrasted against "BFLC,"
  which is expanded at its own first occurrence in the same paragraph
  style -- PBFT simply had not received the same treatment. Fixed by
  rewording the sentence introducing RPBFT to spell out "Practical
  Byzantine Fault Tolerance (PBFT)" there; all later uses of PBFT/RPBFT
  rely on that one expansion, per standard practice. Net addition: 9
  words (2821 -> 2830 / 3000-word limit).
- Also reviewed this round and confirmed acceptable as-is: "BtRaI" is
  not expanded letter-by-letter (its construction is not a clean
  initialism of the paper's title, so guessing at an expansion risked
  being wrong; the prose already makes clear it is Liu et al. (2024)'s
  name for their own scheme, which is sufficient); the five-section
  narrative flow (Motivation -> Software description -> Illustrative
  examples -> Impact -> Conclusions) was read end-to-end and found
  coherent, with the Abstract's headline numbers echoed consistently in
  the Conclusions; undefined variables in illustrative code snippets
  (e.g. `CHAIN_OK`, `hospitals`) were judged acceptable, standard
  practice for illustrative rather than fully executable snippets, with
  complete definitions available in the corresponding `examples/` scripts.

## v0.1.15 (2026-08-24)
Round-15 audit: a methodology change (whole-manuscript coherence sweep
instead of hunting one more isolated parameter bug, per the explicit
assessment at the end of round 14 that the latter had converged). No
code/test change; manuscript citation formatting fixed.

- **Fixed a citation-format mismatch**, found by reading the entire
  rendered manuscript end-to-end for the first time since early drafts
  (every prior round edited specific passages without re-reading the
  whole document). The reference list is numbered [1]-[5], but the
  prose exclusively used narrative "Author (Year)" citations and never
  actually referenced any of those five numbers -- a reader could not
  jump from an in-text mention to its reference-list entry. Cross-checking
  further found reference [4] (McMahan et al. 2017, FedAvg) was not
  mentioned anywhere in the prose at all, an uncited reference in the
  stricter sense, not just an unlabelled one.
- Five bracket citations inserted at the first natural prose mention of
  each work: [1] and [2] where BFLC and its medical extension are first
  introduced (Section 1); [3] where BtRaI is introduced (Section 1); [4]
  appended to the sentence defining the standard FL paradigm that FedAvg
  established (Section 1's opening); [5] where "plain PBFT" is first
  named as a specific protocol (F3, Section 2.2). Net addition: 5 words
  (2816 -> 2821 / 3000-word limit).

## v0.1.14 (2026-08-24)
Round-14 audit: a single inline-comment wording correction. No behavior,
test, or manuscript change -- the corrected comment was never reflected
in any user-facing documentation.

- **Corrected an inaccurate inline comment** in `TrustworthyFLSimulator.__post_init__`,
  introduced in v0.1.13's deep-copy fix. That comment said the X/y arrays
  "are not deep-copied," which is the opposite of what `copy.deepcopy(self.nodes)`
  actually does (it recurses into everything, including the arrays). The
  code was always correct; only the comment's wording was wrong. Also
  investigated and confirmed safe this round: `_local_fit` never mutates
  its X/y/weights arguments in place (it copies the weight vector before
  modifying it, and only ever reads X/y), and the deep-copy's overhead is
  negligible at a realistic data scale (100 nodes x 1000 samples x 50
  features, ~41.6MB total, copied in ~0.2s).

## v0.1.13 (2026-08-24)
Round-13 audit: a real hidden-state-sharing defect fixed, plus a
manuscript word-budget management step (the budget was at 96% of the
SoftwareX 3000-word limit going into this round).

- **`TrustworthyFLSimulator` no longer shares reputation state across
  instances built from the same `Node` list.** `update_hc_reputation`
  mutates `HCReputationState.reputation` in place, and `Node.reputation_state`
  held a reference to that mutable object; constructing two
  `TrustworthyFLSimulator`s from the same `Node` objects (or reusing a
  list after a prior run) meant the second, freshly-built simulator
  silently started from reputations already altered by the first run --
  demonstrated during audit: a second simulator's nodes showed
  post-first-run reputations (e.g. 0.586) rather than their original 0.5,
  before `run_round()` had ever been called on the second instance.
  `__post_init__` now deep-copies the supplied `nodes`, so no simulator
  instance shares mutable state with the caller's original objects or
  with any other simulator instance. Verified that the package's own
  core reported numbers (the 12.95 vs. 1.10 sleeper-attack comparison)
  were never affected by this defect: both `examples/demo_sleeper_attack.py`
  and the corresponding test construct a fresh `Node` list inside every
  seed iteration and never reuse objects across simulator instances.
  One new regression test; an existing round-12 test that asserted
  object identity between the caller's nodes and the simulator's internal
  index was updated, since that identity is no longer expected to hold
  by design after this fix (37 tests total, up from 36).
- **Manuscript trimmed before adding this round's note**, rather than
  risking the 3000-word limit: F2's description of the reputation-update
  functions was rewritten to state the same validation facts (the
  alpha/beta/delta, omega, waste_penalty, reputation-range and
  gamma-ordering checks from earlier rounds) without the accompanying
  audit-process narration (e.g. "the most severe finding... after the
  original contamination bug"), saving roughly 60-70 words net even
  after this round's own addition to F7. Word count after this release:
  2816 / 3000 (was 2879 before the trim).

## v0.1.12 (2026-08-24)
Round-12 audit: a performance fix, not a correctness fix. All 35
pre-existing tests' asserted numeric values are unchanged (verified by
running the full suite before and after) -- this release only changes
how fast the same results are computed.

- **`TrustworthyFLSimulator._by_id` is now an O(1) dict lookup** instead
  of an O(n) linear scan (`next(n for n in self.nodes if n.node_id ==
  node_id)`). Found during a performance-focused audit sweep (round 12):
  `run_round()` called it roughly `2*c_num + 2*(n_nodes-c_num) + c_num`
  times per round, making a full round's committee-data/reputation
  bookkeeping O(n^2) overall -- not a problem at the small node counts
  used in the examples and test suite, but a real bottleneck at the
  larger scales the package's stated design goal (Section 2.1,
  independent reuse) invites. An `{node_id: Node}` index is now built
  once in `__post_init__`.
- **Fixed a redundant double lookup** in the committee-data preparation
  step: the same committee member was looked up twice (once for `.X`,
  once for `.y`) even before the O(1) fix, a wasted call regardless of
  the underlying lookup's complexity. Now looked up once via a walrus
  assignment and both attributes read from the single result.
- The duplicate-`node_id` error message (added in v0.1.7) was updated to
  match the new O(1) index's actual failure mode: the earlier message
  described the old linear-scan version's "keeps returning only the
  first match" behaviour, which no longer describes what would happen
  post-fix (a dict comprehension keeps the *last* match, not the first);
  the check itself was unaffected (it still runs, and still correctly
  rejects duplicates, before the index is ever built) but the message
  text was stale and has been corrected for accuracy.
- One new regression test confirming the index is built correctly and
  that a 200-node simulation still produces finite, sensible results
  after the optimization (36 tests total, up from 35). Smoke-tested
  separately (not part of the portable test suite, which avoids
  wall-clock assertions): 200 nodes x 20 rounds completed in ~2.6s.

## v0.1.11 (2026-08-24)
Round-11 audit: pure manuscript wording clarification. No code, test, or
package behavior changed in this release -- recorded as a version bump
only to keep the manuscript's C1/S1 metadata in step with the release
history, not because any code changed.

- **Manuscript scope clarification (F5):** the description of
  `elect_committee`'s three interchangeable strategies could be read as
  implying `TrustworthyFLSimulator` also exposes all three end-to-end.
  It does not: `TrustworthyFLSimulator` always calls `elect_committee`
  with `strategy="by_score"` regardless of its own `election` setting
  ("score" vs "reputation" differ only in how the `scores` dict fed to
  that call is built, not in the election algorithm itself). This is a
  deliberate scope choice -- contrasting exactly those two modes is the
  package's central narrative -- not a limitation worth changing, so F5
  now says so explicitly rather than leaving the boundary implicit.
  `random` and `multi_factor` remain fully available to callers of
  `elect_committee` directly.
- Audit also swept four previously-unexamined dimensions this round and
  confirmed no defects: no bare mutable default arguments anywhere in the
  codebase (the classic Python gotcha); `Node`'s non-hashability is
  standard dataclass behaviour for a class holding numpy arrays and is
  never relied upon internally; `CITATION.cff` parses as valid YAML with
  all required fields; and the `random` election strategy is genuinely
  reproducible given a seeded generator.

## v0.1.10 (2026-08-24)
Round-10 audit: methodology change to a systematic sweep of every
parameter across the codebase with an implicit sign/range constraint,
rather than probing one parameter at a time. Three gaps closed (1 B-level,
2 C-level); one parameter (`threshold`) reviewed and confirmed to need no
constraint. No direction-reversal defects found this round.

- **`reputation` field now validated to [0, 1]** on all three
  reputation-state classes. Previously unconstrained; an out-of-range
  starting value (e.g. 5.0) is not a direction-reversal defect -- the
  convex-combination update rule pulls it back toward [0, 1] over several
  rounds (observed: 5.0 -> 2.49 -> 1.49 -> 1.09 -> 0.93 -> 0.87) -- but
  every round before convergence reports a reputation with no physical
  meaning under the model's own [0, 1] definition, and this was
  inconsistent with the [0, 1] validation already applied to other scalar
  rating inputs (`csp_rating`, `credibility_weighted_score`) in earlier
  rounds.
- **`gamma_up`/`gamma_down` ordering now validated eagerly at
  construction**, not only lazily inside `adaptive_learning_rate` on
  first use. A state object with the gammas swapped (e.g.
  `gamma_up=0.1, gamma_down=0.9`) previously constructed without error
  and only failed later, when an update function was actually called --
  inconsistent with alpha/omega's immediate construction-time failure.
  `adaptive_learning_rate`'s own check is retained as a second line of
  defence for direct callers.
- **`RPBFTState.epoch_num` now validated to be a positive integer.** A
  non-positive value was previously accepted and forces committee
  rotation on every single accepted block rather than the intended
  periodic rotation -- a degenerate configuration, not a
  direction-reversal defect.
- **Reviewed and left unchanged:** `validate_updates`'s and
  `TrustworthyFLSimulator`'s `threshold` argument. Unlike the parameters
  above, it has no implicit sign/range constraint -- negative values
  ("accept nearly everything") and values above 1 ("reject nearly
  everything") are both legitimate configurations, not errors.
- Three new regression tests (35 total, up from 32), one per fix.

## v0.1.9 (2026-08-24)
Round-9 audit: the same direction-reversal failure mode fixed in v0.1.8
(alpha/beta/delta) found again in a different parameter (omega), one
round later. No behavior change for legal (positive) omega values.

- **`omega` now validated to be strictly positive**, at both entry
  points: `behavior_score()` itself, and construction of
  `HCReputationState` / `PnFReputationState` / `CSPReputationState` (so
  a misconfigured object fails fast at construction rather than only on
  first use). `behavior_score`'s sigmoid depends on `omega > 0` for its
  monotonicity; demonstrated during audit that `omega=-1.0` inverts it
  completely -- "good" chain behaviour (many correctly generated blocks,
  zero errors) scored 0.000 while "bad" behaviour (almost no blocks,
  many errors) scored 0.477, the opposite of the intended ranking, with
  no error raised. `omega=0` degenerates the score to a constant 0.5
  regardless of behaviour, silently discarding all information. Extreme
  magnitudes (e.g. omega on the order of 1e10) were also observed to
  trigger `RuntimeWarning: overflow encountered in exp`, though the
  resulting value still fell in [0, 1] by floating-point convention.
  **This is the same class of defect fixed for alpha/beta/delta in
  v0.1.8** -- "a parameter that must be positive for the direction of a
  core computation to be correct, left unvalidated" -- found again in a
  different parameter the very next audit round, which is why this
  fix reuses the round-8 lesson directly: the check is written once, in
  a new shared `_check_positive_omega` function, and called from all
  three classes plus `behavior_score` itself, rather than being
  duplicated inline at each of the four call sites (an earlier draft of
  this fix did exactly that copy-paste, caught and corrected during the
  same development session that introduced it -- see the module's
  history). Two new regression tests (32 total, up from 30).

## v0.1.8 (2026-08-24)
Round-8 audit: the most severe finding since the original v0.1.1
statistical-contamination bug. No behavior change for legal (non-negative,
sum-to-1) weight tuples.

- **Reputation-direction reversal fix (severe):** `HCReputationState`,
  `PnFReputationState` and `CSPReputationState` each validated only that
  their weight tuple (`alpha`/`beta`/`delta`) summed to 1, never that
  every component was non-negative. A tuple such as
  `alpha=(1.5, -0.3, -0.1, -0.1)` sums to 1 and was accepted silently,
  but inverts the sign of the corresponding sub-score's contribution to
  the comprehensive reputation. Demonstrated during audit: with this
  alpha, a healthcare centre with a *worse* peer/CSP rating (0.05 instead
  of 0.95) received a *higher* updated reputation (0.792 vs 0.650) --
  the exact opposite of the reputation model's core design goal, with no
  error raised and the output remaining in the ordinary [0, 1] range
  throughout. This is more severe than the round-2 `waste_penalty`
  direction bug (which affected one minor penalty factor) because
  alpha/beta/delta control the sign of the *entire* comprehensive
  reputation computation. All three classes shared the identical gap
  (the missing non-negativity check had been copy-pasted three times),
  so the fix centralises the check in one shared function
  (`_check_convex_weights`) rather than patching each class separately, to
  remove the root cause rather than the third symptom of it.
  Two new regression tests (30 total, up from 28): one confirming all
  three classes reject negative components, one confirming end-to-end
  that a better peer/CSP rating now reliably produces a higher
  reputation than a worse one.

## v0.1.7 (2026-08-24)
Round-7 audit: one data-integrity gap closed. No behavior change for
normal (unique-id) usage.

- **`TrustworthyFLSimulator` now validates that every `Node.node_id` is
  unique.** Previously, a duplicate id silently collapsed the internal
  reputation dictionary (`{node_id: reputation}`, which cannot hold two
  entries for the same key) while `_by_id()` continued to return only
  the *first* matching `Node` object -- so committee-election ranking
  (keyed on the collapsed dict, reflecting whichever duplicate was
  constructed last) and the data actually used for that node's training
  and validation (from whichever duplicate `_by_id()` finds first) could
  silently come from two different `Node` objects that merely share an
  id, with no error raised. Found during audit by constructing two nodes
  both named `"H0"` with different reputations; one round ran without
  crashing purely because the duplicate id was not selected onto the
  committee that round -- the mismatch is real but was not guaranteed to
  surface as a visible failure. Now raises `ValueError` naming the
  duplicate id(s) at construction time. One new regression test (28
  total, up from 27).
- Also investigated during this round and left unchanged: `lr` and
  `local_steps` accept out-of-range values (e.g. a negative learning
  rate) with no validation. Consistent with common practice in
  scikit-learn and PyTorch, which likewise leave training
  hyperparameter sanity to the caller; not treated as a defect.

## v0.1.6 (2026-08-24)
Round-6 audit: two range-validation gaps closed, one manuscript number
re-verified. No behavior change for in-range parameter values.

- **`elect_committee`'s `factor_weight` (multi_factor strategy) now
  validated to [0, 1].** Outside this range the "weighted blend" the
  docstring promises silently reverses: e.g. `factor_weight=2.0` gives
  the raw score a *negative* effective weight, so higher-scoring
  candidates become less likely to be elected -- the opposite of the
  documented behavior, with no error raised. Now raises `ValueError`
  outside [0, 1]; boundary values 0.0 and 1.0 (pure by-score / pure
  by-secondary-factor) remain valid and tested.
- **`RPBFTState`'s custom `collusion_cap` now validated to
  `[0, c_num - 1]`.** A negative cap (e.g. -1) makes the anti-collusion
  rule treat *any* non-negative carryover count, including zero, as
  "exceeding the cap," forcing full committee eviction on every single
  rotation regardless of the actual reputation ranking. Demonstrated
  during audit: with a negative cap and unchanging reputations, the
  committee enters a permanent two-group oscillation rather than
  converging to a stable top-c_num set. Now raises `ValueError` outside
  the valid range; the default (unset) `collusion_cap` computation is
  unaffected.
- Two new regression tests (27 total, up from 25).
- **Manuscript number re-verified:** the "roughly 4.5x" reputation
  loss-vs-gain ratio (Abstract, F2, Example 1) was recomputed
  independently during audit rather than only recomputed once at
  original writing: gain = 0.0697, loss = 0.3126, ratio = 4.489. No
  change needed. *(Superseded in v0.1.19: the arithmetic was right but
  the inputs 0.98/0.10 are not symmetric about the neutral point; the
  update rule's own asymmetry is gamma_up/gamma_down = 1.5x, which the
  manuscript now reports.)*

## v0.1.5 (2026-08-24)
Round-5 audit: one low-severity configuration cleanup. No code, test, or
manuscript-content changes.

- **Removed unused dev dependency:** `pyproject.toml`'s `dev` extra
  declared `scikit-learn>=1.1`, left over from the pyproject.toml
  template this package started from (a different project's test suite
  used scikit-learn's KMeans; medchain's never has). Confirmed by
  cross-checking every `import` statement in `tests/` and `examples/`
  against declared dependencies: only numpy, scipy, and pytest are
  actually used. Removing it means each of the 12 CI matrix jobs
  installs one fewer unnecessary heavy dependency, and resolves an
  internal inconsistency with the manuscript's own metadata table (C6),
  which never listed scikit-learn as a tool used.
- Verified in a clean virtual environment that `pip install -e ".[dev]"`
  still installs successfully and all 25 tests still pass after the
  removal.

## v0.1.4 (2026-08-24)
Round-4 audit: one real runtime-crash regression fixed (introduced by the
round-2 input-validation fix itself), one manuscript internal
inconsistency corrected, one unverified platform claim addressed with a
real CI workflow.

- **Regression fix (significant):** `_check_unit_interval` (added in
  v0.1.2 to validate scalar `csp_rating` / `csp_reputation` inputs) used
  the open interval `(0, 1]`, rejecting the legitimate value `0.0` (e.g.
  a committee validation accuracy of exactly zero -- a normal, expected
  outcome, not an error condition). This was inconsistent with
  `credibility_weighted_score`'s own array-input validation, which
  accepts 0. The mismatch could crash `TrustworthyFLSimulator.run_round()`
  mid-simulation the first time a submitted update scored exactly 0
  against the committee -- a real regression introduced while fixing a
  different, genuine gap in v0.1.2. Fixed: the check is now the closed
  interval `[0, 1]`. Two new regression tests added: one confirming 0.0
  is accepted (and negative / >1 values are still correctly rejected,
  i.e. the fix did not loosen validation in the wrong direction), and one
  exercising the exact `TrustworthyFLSimulator` code path that could have
  crashed. 25 tests total (up from 23).
- **Manuscript correction:** Highlights bullet 3 ("Reputation formulas
  validated against the source paper's own reported figures") was left
  unchanged when Examples 1 and 3 were softened in v0.1.2/v0.1.3 to stop
  asserting unverified correspondence to specific paper figures/tables --
  producing an internal contradiction between the manuscript's own
  Highlights and its body text. Reworded to "Reputation and consensus
  formulas tested against the source papers' equations," a claim that
  remains fully supported (the formulas *are* tested against the papers'
  equations; only the specific-figure/table correspondence was ever in
  question).
- **CI workflow added:** the metadata table (S5: Linux/macOS/Windows;
  C6: Python 3.9-3.12) previously had no CI matrix or any other
  multi-environment run backing it -- `.github/` did not exist in the
  repository. Added `.github/workflows/ci.yml` (3.9-3.12 x three
  platforms). As of this release the workflow has not yet executed (it
  requires the repository's first push); the manuscript now says so
  explicitly rather than leaving the platform/version claim to be read as
  already-verified.

## v0.1.3 (2026-08-24)
Round-3 audit: coverage/API-declaration gaps closed, one suspected defect
investigated and ruled out. No logic changes to any function's behavior.

- **API declaration fix:** `rpbft.py`'s `__all__` was missing `leader` and
  `record_block`, both real public functions defined in the module.
  `record_block` -- the sole implementation of RPBFT's
  "rotate immediately on a rejected block, otherwise rotate every
  epoch_num blocks" rule -- additionally had zero test coverage anywhere
  in the repository (source, tests, examples, or the manuscript) despite
  being a complete, correct implementation (verified by two new
  scenario probes during audit). Both gaps closed: `__all__` updated,
  and `test_record_block_rotates_on_schedule_and_on_rejection` /
  `test_select_committee_contract` added (23 tests total, up from 21).
- **Investigated and ruled out:** audit initially suspected a Python 3.9
  compatibility break, since all four core modules use PEP 604 union-type
  syntax (`X | None`), which requires `from __future__ import annotations`
  protection to be safe on Python <3.10. A first check (grepping only the
  first 20 lines of each file) reported this import missing from two
  modules; re-checking full file contents confirmed all four modules
  correctly include it (pushed past line 20 by longer module
  docstrings). No code defect exists; the initial concern was an artifact
  of an insufficiently thorough audit check, corrected and documented here
  for transparency. A true Python 3.9 runtime reproduction was not
  possible in this environment (Ubuntu 24.04's apt repositories do not
  package python3.9, and no network path to a source that does was
  available), so this remains a static-analysis conclusion; the CI matrix
  (Python 3.9-3.12) shipped with the repository will provide the first
  real runtime confirmation once run.
- Manuscript and architecture figure updated to reflect 23 tests.

## v0.1.2 (2026-08-24)
Round-2 audit fixes: input validation, test-coverage gaps, and two
manuscript overclaims corrected. No changes to the statistical behaviour
of any function on in-domain input.

- **Input validation added (significant):** `credibility_weighted_score`
  (and therefore every function built on it) previously accepted any
  numeric rating, including values outside the paper's (0, 1] domain,
  and could silently produce negative credibility weights with no error.
  Now raises `ValueError` on out-of-range input. Similarly,
  `update_pnf_reputation`'s `waste_penalty` argument previously had no
  range check; a value below 1 divided the rating *up* rather than down,
  silently inverting a penalty into a reward. Now requires
  `waste_penalty >= 1`. The scalar `csp_rating` / `csp_reputation`
  arguments (which bypass `credibility_weighted_score` entirely) now
  receive the same (0, 1] validation directly.
- **New tests:** four regression tests for the above, plus first-ever
  coverage of `update_pnf_reputation` and `update_csp_reputation` (zero
  tests existed for either before this round). 21 tests total (up from
  16).
- **Manuscript correction (important):** an earlier draft claimed
  `max_fault_tolerance`'s output "reproduces the paper's Table 3-4
  pattern." This was incorrect and has been removed: Tables 3-4 in Liu
  et al. (2024) report transaction-latency and network-traffic
  comparisons, not fault-tolerance counts, and were never actually
  cross-checked against this package's output. The general
  fault-tolerance improvement claim (49 vs. 33 for a 100-node/committee-4
  example) is retained, attributed only to the paper's general Section 5
  discussion.
- **Manuscript softened:** the claim that `examples/demo_reputation_dynamics.py`
  "reproduces the qualitative pattern of BtRaI's own Fig. 4" is retained
  as a qualitative statement, but the specific six numeric targets used
  are now flagged as not independently re-verified against the original
  figure during audit, rather than asserted as a confirmed match. The
  corresponding test was renamed from
  `test_hc_reputation_converges_near_paper_targets` to
  `test_hc_reputation_converges_to_steady_service_quality` to stop
  implying a verified correspondence the test's (circular) design cannot
  establish.
- Architecture figure (Fig. 1) regenerated with the updated test count.

## v0.1.1 (2026-08-24)
*(Superseded in v0.1.19: the "post-defection committee seats" numbers
below (4.30 -> 12.95 vs 1.10) counted rounds containing at least one
sleeper; the seat-count metric now reported is 17.30 vs 1.10.)*

Audit fixes to the round-3 (recipes) integration layer. No changes to
consensus/reputation.py, consensus/rpbft.py or aggregation/bflc.py.

- **Contamination fix (significant):** under `election="score"` in
  `TrustworthyFLSimulator`, incumbent committee members with no fresh
  validation score this round were being backfilled with their
  *reputation* to determine re-election eligibility -- the same quantity
  that is supposed to be exclusive to `election="reputation"`. This
  silently leaked the package's own integration into the baseline it is
  meant to be compared against, understating the true effect size.
  Fixed: under `election="score"`, incumbents without a fresh round score
  are no longer eligible for immediate re-election, matching BFLC's
  memoryless single-round rule. Effect on the headline sleeper-attack
  comparison (20 seeds, unchanged methodology): mean post-defection
  committee seats regained under `election="score"` moved from 4.30 (SD
  8.80) to 12.95 (SD 1.36); `election="reputation"` is unchanged at 1.10
  (SD 3.10); significance improved from p=0.008 to p<0.0001. The
  corrected comparison is a *stronger* result for the package's central
  claim, not a weaker one -- the bug had been making the two election
  rules look more similar than they actually are.
- **New regression test**
  (`test_score_election_incumbents_not_backfilled_by_reputation`)
  reproduces the exact scenario that surfaced the bug: an incumbent with
  an artificially high reputation and no training history must lose its
  committee seat under `election="score"`.
- Removed an unused `rotate_committee` import from `trustworthy_fl.py`
  and documented, rather than silently left implicit, that the simulator
  re-elects every round instead of using epoch-based rotation; the
  anti-collusion carryover cap in `consensus/rpbft.py` is therefore
  validated in isolation but not yet exercised end-to-end. Epoch-based
  rotation is deferred to v0.2 rather than retrofitted under audit time
  pressure.
- Four edge cases probed with no defects found: `elect_committee`
  multi_factor with degenerate (zero-range) inputs,
  `malicious_attack_success_probability` with a malicious pool that
  rounds to zero, and an all-updates-rejected round (global weights
  correctly hold at their previous value rather than corrupting).

## v0.1.0 (2026-08-24)
Initial release: reputation assessment (Liu et al. 2024), RPBFT
consensus (Section 4.2), BFLC committee-consensus aggregation (Li et al.
2021), trustworthy_fl integration recipe, 15 tests, two example scripts.
