"""Illustrate the qualitative reputation dynamics described by Liu et al. (2024).

Six healthcare centers converge to distinct steady-state reputations under
steady service quality; the asymmetric learning rate (Section 4.1.1) then
makes a quality drop cost more reputation than a quality rise gains. The six
input levels below are the steady-state reputations the paper itself reports
for Fig. 4 (Section 6.1: "maintained steadily around 0.96, 0.84, 0.74, 0.82,
0.88, and 0.88"), verified against the published text during audit (round 19).

What this shows -- and does not show (audit, round 31): feeding those six
values as sustained service-quality *inputs* makes each reputation converge
to within 0.04 of its input while preserving the six centres' order. That is
a contraction property of Eq. 1-6 (with the default alpha and a saturated
chain-behaviour term the fixed point is about 0.78*input + 0.20, so 0.74
settles at 0.78 and 0.96 at 0.95), not an independent reproduction of the
paper's figure: the paper's outputs are being used as inputs. Earlier
versions of this docstring and the manuscript said the script "drives" the
centres "to" those values; the test suite's docstring for the corresponding
test had already flagged the circularity in round 2.

On the loss/gain ratio printed below: the 0.98 vs 0.10 inputs are *not*
symmetric around the 0.8 baseline (the input that leaves 0.8 unchanged is
about 0.759, so they sit +0.22 / -0.66 from neutral). The ~4.5x ratio is
therefore mostly an input-asymmetry effect; the update rule's own asymmetry
is exactly gamma_up/gamma_down = 1.5x, which the symmetric-input block
prints for comparison (audit, round 19).

Run: python examples/demo_reputation_dynamics.py
"""
import numpy as np

from medchain.consensus.reputation import HCReputationState, update_hc_reputation, behavior_score

CHAIN_OK = dict(ac_num=10, f_bar=3, ac_val=10, wr_num=0, wr_val=0)


def run_at_level(level, rounds=80, seed=0):
    rng = np.random.default_rng(seed)
    state = HCReputationState(reputation=0.5, alpha=(0.4, 0.2, 0.2, 0.2),
                               gamma_up=0.6, gamma_down=0.4)
    trace = []
    for _ in range(rounds):
        pnf = rng.normal(level, 0.02, 50).clip(0, 1)
        peer = rng.normal(level, 0.02, 5).clip(0, 1)
        r = update_hc_reputation(state, pnf_ratings=pnf, peer_hc_ratings=peer,
                                  csp_rating=level, csp_reputation=0.95,
                                  chain_behavior=CHAIN_OK)
        trace.append(r)
    return trace


if __name__ == "__main__":
    levels = {"HC1": 0.96, "HC2": 0.84, "HC3": 0.74, "HC4": 0.82, "HC5": 0.88, "HC6": 0.88}
    print("Steady-state convergence under six sustained service-quality inputs")
    print("(the inputs are the six steady-state reputations the paper reports for its Fig. 4, Section 6.1;")
    print(" the fixed point is ~0.78*input + 0.20, so this is a contraction check, not a figure reproduction):")
    for name, level in levels.items():
        trace = run_at_level(level)
        print(f"  {name}: input={level:.2f}  converged={trace[-1]:.3f}  ({trace[-1] - level:+.3f})")

    print()
    print("Asymmetric growth vs. decay from a fixed 0.8 baseline:")
    state = HCReputationState(reputation=0.8, gamma_up=0.6, gamma_down=0.4)
    r_up = update_hc_reputation(state, pnf_ratings=np.array([0.98]), peer_hc_ratings=np.array([0.98]),
                                 csp_rating=0.98, csp_reputation=0.95, chain_behavior=CHAIN_OK)
    state2 = HCReputationState(reputation=0.8, gamma_up=0.6, gamma_down=0.4)
    r_down = update_hc_reputation(state2, pnf_ratings=np.array([0.1]), peer_hc_ratings=np.array([0.1]),
                                   csp_rating=0.1, csp_reputation=0.95, chain_behavior=CHAIN_OK)
    print(f"  one excellent round (input=0.98): 0.800 -> {r_up:.3f}  (gain {r_up-0.8:+.3f})")
    print(f"  one terrible round  (input=0.10): 0.800 -> {r_down:.3f}  (loss {r_down-0.8:+.3f})")
    print(f"  ratio {abs((r_down-0.8)/(r_up-0.8)):.2f}x -- but these inputs are asymmetric about the baseline")

    print()
    # The input s0 that leaves a reputation of 0.8 unchanged (current == historical):
    # current = (a1 + a2 + a3*0.95) * s + a4 * BR, with the default alpha and CHAIN_OK.
    s0 = (0.8 - 0.2 * behavior_score(**CHAIN_OK)) / (0.4 + 0.2 + 0.2 * 0.95)
    print(f"Same comparison with inputs symmetric about the neutral input s0 = {s0:.4f}:")
    for d in (0.10, 0.15, 0.20):
        s_up = HCReputationState(reputation=0.8, gamma_up=0.6, gamma_down=0.4)
        s_dn = HCReputationState(reputation=0.8, gamma_up=0.6, gamma_down=0.4)
        g = update_hc_reputation(s_up, pnf_ratings=np.array([s0 + d]), peer_hc_ratings=np.array([s0 + d]),
                                 csp_rating=s0 + d, csp_reputation=0.95, chain_behavior=CHAIN_OK) - 0.8
        l = update_hc_reputation(s_dn, pnf_ratings=np.array([s0 - d]), peer_hc_ratings=np.array([s0 - d]),
                                 csp_rating=s0 - d, csp_reputation=0.95, chain_behavior=CHAIN_OK) - 0.8
        print(f"  +/-{d:.2f}: gain {g:+.4f}, loss {l:+.4f}, ratio {abs(l/g):.2f}x  (= gamma_up/gamma_down)")
    print("  Reputation falls faster than it rises, matching the paper's design goal")
    print("  that reputation is 'not easily accumulated but quickly degraded'.")
