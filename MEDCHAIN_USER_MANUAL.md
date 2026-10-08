# MedChain User Manual

**Software:** `medchain`  
**Package version:** 0.1.34  
**Manual edition:** October 8, 2026  
**Audience:** Researchers, developers, and students experimenting with reputation-driven committee-consensus federated learning.

## 1. Overview

MedChain is a Python research library and simulator for studying committee-based federated learning and reputation-aware participant selection in healthcare-blockchain scenarios. It combines concepts from committee-consensus federated learning (BFLC) and multidimensional reputation assessment (BtRaI).

The software supports simulated hospital nodes, local model training, validation of submitted updates, committee elections, reputation updates, and experiments involving malicious or intermittently malicious participants.

> **Research software only.** MedChain is not a deployed blockchain, a clinical decision-support product, or a certified medical system. The included examples use synthetic data; do not treat their results as clinical validation.

## 2. System Requirements

- Python **3.10 or later**.
- NumPy **1.22 or later**.
- SciPy **1.9 or later**.
- `pip` and a terminal (PowerShell, Command Prompt, macOS Terminal, or a Linux shell).
- Optional for development and testing: `pytest` **7 or later**.

The project's package metadata declares support for Python 3.10–3.14. The repaired package was checked with Python 3.13; other platforms and Python versions have not been independently verified as part of that check.

## 3. Installation

### 3.1 Extract the package

Extract `medchain-fixed-2026-10-08.zip` to a directory of your choice. Open a terminal in the extracted **`medchain-main`** directory (the one containing `pyproject.toml`).

### 3.2 Create a virtual environment (recommended)

**Windows (PowerShell):**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

If PowerShell blocks script activation, use Command Prompt activation (`.venv\Scripts\activate.bat`) or invoke `.venv\Scripts\python.exe` directly.

### 3.3 Install MedChain

For development and to run the included tests:

```bash
python -m pip install -e ".[dev]"
```

For normal use without the testing extra:

```bash
python -m pip install -e .
```

Check the installation:

```bash
python -c "import medchain; print('MedChain import successful')"
```

## 4. Quick Start: Run a Simulation

Create a file named `quickstart.py` in the project root:

```python
import numpy as np
from medchain.consensus.reputation import HCReputationState
from medchain.recipes.trustworthy_fl import Node, TrustworthyFLSimulator

rng = np.random.default_rng(0)
nodes = [
    Node(
        node_id=f"H{i}",
        X=np.hstack([
            rng.normal(0, 1, (150, 6)),
            np.ones((150, 1)),  # bias / intercept column
        ]),
        y=rng.integers(0, 2, 150).astype(float),
        reputation_state=HCReputationState(reputation=0.5),
    )
    for i in range(10)
]

sim = TrustworthyFLSimulator(
    nodes=nodes,
    c_num=3,
    election="reputation",
    seed=0,
)
history = sim.run(n_rounds=20)
print(f"Completed rounds: {len(history)}")
print(f"Recorded rounds: {len(sim.history)}")
```

Run it:

```bash
python quickstart.py
```

This example creates ten simulated hospital nodes, elects a three-member committee, and executes 20 rounds of simulated federated learning. It uses randomly generated data for illustration, not a medical dataset.

## 5. Main Configuration Options

The `TrustworthyFLSimulator` class is the principal high-level entry point.

| Argument | Purpose | Default |
|---|---|---|
| `nodes` | List of participating `Node` objects | Required |
| `c_num` | Number of committee members | Required |
| `threshold` | Minimum median validation accuracy for accepting an update | `0.5` |
| `election` | `"reputation"` or `"score"` | `"reputation"` |
| `seed` | Random seed for reproducible simulation behavior | `None` |
| `lr` | Local gradient-descent learning rate | `0.1` |
| `local_steps` | Number of local optimization steps | `50` |
| `reelect_incumbents` | Allow sitting committee members to remain eligible under reputation election | `True` |

**Election modes:**

- `election="reputation"` selects participants based on accumulated reputation.
- `election="score"` uses the current-round validation score as a comparison baseline.
- `reelect_incumbents=False` can be used **only** with `election="reputation"`. It restricts re-election to current-round trainers, subject to the simulator's documented seat-shortfall handling.

**Important:** With the default reputation election, incumbent members can remain on the committee for many consecutive rounds. Use the no-re-election setting when studying committee turnover or when comparing against the score baseline.

## 6. Preparing Input Data

Each `Node` represents a participant with a local data shard:

```python
Node(
    node_id="Hospital_A",
    X=feature_matrix,
    y=label_vector,
    reputation_state=HCReputationState(reputation=0.5),
)
```

Input requirements:

1. `node_id` must be unique across participants.
2. `X` must be a two-dimensional array of shape `(samples, features)`.
3. `y` must be a one-dimensional array with one target per sample.
4. Each node must have at least one sample.
5. All nodes must use the same number and ordering of features.
6. Use compatible numerical feature values and binary labels for the simulator's logistic prediction example.

The simulator checks many structural input errors at initialization. It does not perform clinical data preprocessing, privacy protection, or medical-data compliance checks for you.

## 7. Running the Bundled Examples

From the project root, after installation:

### 7.1 Reputation dynamics

```bash
python examples/demo_reputation_dynamics.py
```

Demonstrates reputation evolution for six simulated healthcare centers and compares the response to favorable and unfavorable behavior. The example is a qualitative/contraction check; it is **not** an independent reproduction of the referenced paper's Figure 4.

### 7.2 Sleeper-attack comparison

```bash
python examples/demo_sleeper_attack.py
```

Runs a synthetic multi-seed experiment comparing score-based election, reputation-based election, and reputation-based election without incumbent re-election. It reports measures of malicious committee participation and committee-seat carryover. This experiment may take longer than the quick-start example.

## 8. Accessing Simulation Results

Use `sim.run(n_rounds=...)` to execute several rounds and obtain a list of round records. The simulator also stores records in `sim.history` and the current global model parameters in `sim.global_weights`.

```python
history = sim.run(n_rounds=5)
print(history[-1])
print(sim.global_weights)
```

For evaluation on a separate, compatible test dataset:

```python
accuracy = sim.evaluate(X_test, y_test)
print(f"Test accuracy: {accuracy:.3f}")
```

Use the same feature layout for `X_test` as the training shards, including any intercept column. Inspect the returned dictionaries rather than assuming that all versions expose an identical set of history keys.

## 9. Running the Automated Tests

From the extracted project root:

```bash
python -m pytest tests/ -v
```

To run the complete test discovery:

```bash
python -m pytest -v
```

The repaired archive includes a `pytest.ini` that adds `src` to the test import path, making source-tree test runs possible even before editable installation. **Verification recorded for the repaired release:** 64 tests passed under Python 3.13 (62 original tests plus two regression tests). This is not a guarantee that every platform or future environment will behave identically.

## 10. Project Structure

```text
medchain-main/
├── README.md
├── CHANGELOG.md
├── FIXES_2026-10-08.md
├── pyproject.toml
├── pytest.ini
├── src/medchain/
│   ├── consensus/
│   │   ├── reputation.py       # Reputation models and updates
│   │   └── rpbft.py             # Reputation-ranked committee logic
│   ├── aggregation/
│   │   └── bflc.py              # Committee validation and election
│   └── recipes/
│       └── trustworthy_fl.py   # End-to-end FL simulator
├── examples/
│   ├── demo_reputation_dynamics.py
│   └── demo_sleeper_attack.py
├── tests/
│   └── test_medchain.py
└── paper/
```

## 11. Troubleshooting

### `ModuleNotFoundError: No module named 'medchain'`

Make sure the virtual environment is active, navigate to the directory containing `pyproject.toml`, and run:

```bash
python -m pip install -e ".[dev]"
python -m pytest tests/ -v
```

If you are running tests from the extracted source tree without installing, use the included `pytest.ini` from the project root.

### `python` is not recognized

Install a supported Python version and ensure it is available on your `PATH`. On Windows, try `py` instead of `python`.

### Dependency installation fails

Upgrade `pip`, verify your Python version, and retry in a clean virtual environment. Some NumPy/SciPy versions may require platform-specific wheels or build tools.

### Invalid committee size or missing reputation data

Check that committee size is a positive integer appropriate for the available participants, node IDs are unique, and all candidates have reputation entries. The repaired `select_committee` implementation explicitly rejects several invalid inputs.

### Shape mismatch or empty dataset

Ensure all `X` matrices are 2-D, all `y` arrays are 1-D, each shard contains samples, and every node has the same number of features.

### Results vary between runs

Set `seed` and use deterministic input generation. Remember that experiments involving stochastic attacks can produce different outcomes when random seeds or settings change.

## 12. Known Limitations

- The high-level simulator re-elects the committee every round; it does **not** integrate the separate `rotate_committee` anti-collusion carryover mechanism into the end-to-end simulation.
- Committee incumbents are not trained or reputation-updated while serving, which can make default reputation-based committees persistent.
- The simulator simplifies aspects of multidimensional reputation assessment; consult the source docstrings and manuscript before interpreting it as a complete reproduction of every mechanism in the cited papers.
- BtRaI's token-incentive mechanism is not implemented.
- No real blockchain deployment, clinical validation, production privacy/security certification, or cross-platform test matrix is included in the recorded verification.

## 13. Maintenance and Further Reading

- `README.md`: project overview and quick-start code.
- `CHANGELOG.md`: development history and audit notes.
- `FIXES_2026-10-08.md`: issues corrected in the repaired software archive.
- `CITATION.cff`: citation information.
- Source repository: https://github.com/JiahuiTong1/medchain

When publishing work based on MedChain, consult `CITATION.cff` and cite the underlying committee-consensus FL and reputation-assessment research as appropriate.

---

*End of MedChain User Manual.*
