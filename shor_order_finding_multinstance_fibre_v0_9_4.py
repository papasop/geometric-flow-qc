#!/usr/bin/env python3
"""Frozen multi-instance Shor task-fibre audit v0.9.4.

Extends the v0.9.3 N=15,a=2 preflight to a prospectively frozen family of
six (N,a) order-finding instances.  The optimization rule, hyperparameters,
response map, tangent projector, noise construction, training/shifted-heldout
split, and equal objective budget are shared across instances.

Primary comparison: intrinsic exact-fibre ascent versus (i) the unchanged
reference, (ii) basis-invariant random search on the same fibre, and (iii)
SPSA on an orthonormal fibre basis.  Every objective or declared-response
evaluation is charged.  Results are reported per instance and in a
hierarchical paired bootstrap that resamples instances and meta-repetitions.

Scientific boundary: exact phase-estimation distributions with a synthetic
implementation/noise ansatz.  This is not a native gate decomposition,
hardware experiment, fault-tolerance result, cryptographic-scale factoring,
or asymptotic speedup claim.

Only NumPy is required.  Notebook-injected arguments such as ``-f`` are
ignored.  Nonzero exit status means a preregistered primary gate failed.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from fractions import Fraction
import json
import math
import sys
from typing import Iterable

import numpy as np


VERSION = "0.9.4"
N_PARAM = 9
FROZEN_INSTANCES = ((15, 2), (15, 7), (21, 2), (21, 5), (33, 2), (35, 2))

# Five independent declared-response coordinates plus one dependent audit row.
RESPONSE_MATRIX = np.array(
    [
        [1, 0, 0, -1, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 1, 1, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 0],
        [1, 1, 1, -1, 0, 1, 1, 1, 1],
    ],
    dtype=float,
)
J_DAG = np.linalg.pinv(RESPONSE_MATRIX, rcond=1e-12)
P_T = np.eye(N_PARAM) - J_DAG @ RESPONSE_MATRIX
P_T = 0.5 * (P_T + P_T.T)
P_N = np.eye(N_PARAM) - P_T


def tangent_basis() -> np.ndarray:
    w, v = np.linalg.eigh(P_T)
    return v[:, w > 0.5]


T_BASIS = tangent_basis()
TANGENT_DIM = T_BASIS.shape[1]


@dataclass(frozen=True)
class Instance:
    N: int
    a: int
    order: int
    control_qubits: int
    M: int
    success_bins: tuple[int, ...]
    ideal_success: float
    common_c: np.ndarray

    @property
    def key(self) -> str:
        return f"N{self.N}_a{self.a}_r{self.order}"


@dataclass
class Ledger:
    task_calls: int = 0
    response_calls: int = 0
    proposals: int = 0
    steps: int = 0

    @property
    def total(self) -> int:
        return self.task_calls + self.response_calls


def multiplicative_order(a: int, n: int) -> int:
    if n < 2 or math.gcd(a, n) != 1:
        raise ValueError(f"a={a} must be coprime to N={n}")
    x = 1
    for r in range(1, n + 1):
        x = (x * a) % n
        if x == 1:
            return r
    raise RuntimeError(f"no multiplicative order found for ({n},{a})")


def stable_seed(n: int, a: int, salt: int) -> int:
    # Integer-only mixing; independent of Python hash randomization.
    return int((20260816 + 1000003 * n + 9176 * a + 7919 * salt) % (2**32))


def ideal_distribution(order: int, m: int) -> np.ndarray:
    x = np.arange(m, dtype=float)
    p = np.zeros(m, dtype=float)
    for s in range(order):
        state = np.exp(2j * np.pi * s * x / order) / math.sqrt(m)
        p += np.abs(np.fft.fft(state) / math.sqrt(m)) ** 2 / order
    return p / p.sum()


def continued_fraction_success_bins(n: int, order: int, m: int) -> tuple[int, ...]:
    bins = []
    for y in range(m):
        f = Fraction(y, m).limit_denominator(n)
        if f.denominator == order:
            bins.append(y)
    return tuple(bins)


def build_instance(n: int, a: int) -> Instance:
    order = multiplicative_order(a, n)
    # Use the smallest control register, up to the conventional 2*ceil(log2 N)
    # ceiling, for which the frozen continued-fraction rule has at least one
    # exact-order bin.  This keeps the cross-instance audit computationally
    # light while never weakening the denominator bound from N to the known r.
    q0 = int(math.ceil(math.log2(n)))
    bins: tuple[int, ...] = ()
    control_qubits = q0
    for q in range(q0, 2 * q0 + 1):
        trial = continued_fraction_success_bins(n, order, 2**q)
        if trial:
            control_qubits, bins = q, trial
            break
    if not bins:
        raise ValueError(f"empty exact-order success set for N={n}, a={a}")
    m = 2**control_qubits
    p0 = ideal_distribution(order, m)
    rng = np.random.default_rng(stable_seed(n, a, 17))
    c = rng.normal(size=(control_qubits, N_PARAM))
    c /= np.linalg.norm(c, axis=1, keepdims=True)
    return Instance(n, a, order, control_qubits, m, bins,
                    float(np.sum(p0[list(bins)])), c)


def response(theta: np.ndarray, ledger: Ledger | None = None) -> np.ndarray:
    if ledger is not None:
        ledger.response_calls += 1
    return RESPONSE_MATRIX @ np.asarray(theta, dtype=float)


def multiplier_permutation(inst: Instance) -> np.ndarray:
    dim = 2 ** int(math.ceil(math.log2(inst.N)))
    u = np.zeros((dim, dim), dtype=complex)
    for x in range(dim):
        y = (inst.a * x) % inst.N if x < inst.N else x
        u[y, x] = 1.0
    return u


def ideal_multiplier(inst: Instance, theta: np.ndarray) -> np.ndarray:
    """Implementation phases vanish exactly when RESPONSE_MATRIX @ theta=0."""
    u = multiplier_permutation(inst)
    q = RESPONSE_MATRIX[:5] @ np.asarray(theta, dtype=float)
    dim = len(u)
    signs = np.array(
        [[1.0 if ((x >> j) & 1) == 0 else -1.0 for x in range(dim)]
         for j in range(min(4, inst.control_qubits))]
    )
    while len(signs) < 4:
        signs = np.vstack((signs, np.ones(dim)))
    generators = np.vstack((signs[:4], signs[0] * signs[1]))
    return u @ np.diag(np.exp(-0.5j * (q @ generators)))


def noise_instance(inst: Instance, seed: int, shifted: bool) -> tuple[np.ndarray, np.ndarray, float]:
    rng = np.random.default_rng(seed)
    d = rng.normal(size=(inst.control_qubits, N_PARAM))
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    c = inst.common_c + (0.10 if not shifted else 0.17) * d
    c /= np.linalg.norm(c, axis=1, keepdims=True)
    j = np.arange(inst.control_qubits, dtype=float)
    common = 0.105 * ((-0.78) ** j)
    eps = common + rng.normal(0.0, 0.010 if not shifted else 0.016,
                              inst.control_qubits)
    dephase = float(np.clip((0.025 if not shifted else 0.040) +
                            rng.normal(0.0, 0.004), 0.0, 0.15))
    return c, eps, dephase


def iqft_probabilities(inst: Instance, theta: np.ndarray, seed: int,
                       shifted: bool) -> np.ndarray:
    c, base, dephase = noise_instance(inst, seed, shifted)
    eps = base + 0.72 * (c @ np.asarray(theta, dtype=float))
    x = np.arange(inst.M)
    bits = np.array([[(xx >> k) & 1 for k in range(inst.control_qubits)]
                     for xx in x], dtype=float)
    implementation_phase = bits @ eps
    p = np.zeros(inst.M, dtype=float)
    for s in range(inst.order):
        state = np.exp(2j * np.pi * s * x / inst.order +
                       1j * implementation_phase) / math.sqrt(inst.M)
        p += np.abs(np.fft.fft(state) / math.sqrt(inst.M)) ** 2 / inst.order
    p = (1.0 - dephase) * p + dephase / inst.M
    return p / p.sum()


def seed_success(inst: Instance, theta: np.ndarray, seed: int,
                 shifted: bool) -> float:
    p = iqft_probabilities(inst, theta, seed, shifted)
    return float(np.sum(p[list(inst.success_bins)]))


def mean_success(inst: Instance, theta: np.ndarray, seeds: Iterable[int],
                 shifted: bool = False, ledger: Ledger | None = None) -> float:
    seeds = tuple(seeds)
    if ledger is not None:
        ledger.task_calls += len(seeds)
    return float(np.mean([seed_success(inst, theta, s, shifted) for s in seeds]))


def intrinsic_gradient(inst: Instance, z: np.ndarray, seeds: tuple[int, ...],
                       ledger: Ledger, h: float = 2e-5) -> np.ndarray:
    g = np.zeros_like(z)
    for j in range(len(z)):
        e = np.zeros_like(z)
        e[j] = h
        fp = mean_success(inst, T_BASIS @ (z + e), seeds, ledger=ledger)
        fm = mean_success(inst, T_BASIS @ (z - e), seeds, ledger=ledger)
        g[j] = (fp - fm) / (2.0 * h)
    return g


def intrinsic_flow(inst: Instance, seeds: tuple[int, ...], budget: int,
                   trust: float = 0.10) -> tuple[np.ndarray, Ledger]:
    z = np.zeros(TANGENT_DIM)
    led = Ledger()
    per_iteration = (2 * TANGENT_DIM + 3) * len(seeds)
    while led.total + per_iteration <= budget:
        g = intrinsic_gradient(inst, z, seeds, led)
        ng = np.linalg.norm(g)
        if ng < 1e-14:
            break
        direction = g * min(1.0, trust / ng)
        base = mean_success(inst, T_BASIS @ z, seeds, ledger=led)
        best_z, best = z, base
        for alpha in (1.0, 0.5):
            cand = z + alpha * direction
            val = mean_success(inst, T_BASIS @ cand, seeds, ledger=led)
            if val > best:
                best_z, best = cand, val
                break
        z = best_z
        led.steps += 1
    theta = T_BASIS @ z
    while led.total < budget:
        response(theta, led)
    return theta, led


def basis_invariant_random(inst: Instance, seeds: tuple[int, ...], budget: int,
                           meta: int, rmax: float = 1.6) -> tuple[np.ndarray, Ledger]:
    rng = np.random.default_rng(meta ^ stable_seed(inst.N, inst.a, 31))
    led = Ledger()
    best = np.zeros(N_PARAM)
    best_value = mean_success(inst, best, seeds, ledger=led)
    while led.total + len(seeds) <= budget:
        v = P_T @ rng.normal(size=N_PARAM)
        nv = np.linalg.norm(v)
        if nv < 1e-14:
            continue
        radius = rmax * rng.random() ** (1.0 / TANGENT_DIM)
        cand = radius * v / nv
        value = mean_success(inst, cand, seeds, ledger=led)
        led.proposals += 1
        if value > best_value:
            best, best_value = cand, value
    while led.total < budget:
        response(best, led)
    return best, led


def spsa(inst: Instance, seeds: tuple[int, ...], budget: int, meta: int,
         lr: float = 0.18, c: float = 0.03) -> tuple[np.ndarray, Ledger]:
    rng = np.random.default_rng(meta ^ stable_seed(inst.N, inst.a, 53))
    z = np.zeros(TANGENT_DIM)
    led = Ledger()
    k = 0
    while led.total + 2 * len(seeds) <= budget:
        delta = rng.choice((-1.0, 1.0), size=TANGENT_DIM)
        fp = 1.0 - mean_success(inst, T_BASIS @ (z + c * delta), seeds,
                                ledger=led)
        fm = 1.0 - mean_success(inst, T_BASIS @ (z - c * delta), seeds,
                                ledger=led)
        grad = ((fp - fm) / (2.0 * c)) * delta
        z -= (lr / (1.0 + 0.02 * k)) * grad
        k += 1
        led.proposals += 1
    theta = T_BASIS @ z
    while led.total < budget:
        response(theta, led)
    return theta, led


def bootstrap_ci(values: Iterable[float], seed: int, draws: int) -> list[float]:
    x = np.asarray(tuple(values), dtype=float)
    rng = np.random.default_rng(seed)
    means = np.mean(rng.choice(x, size=(draws, len(x)), replace=True), axis=1)
    return [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]


def hierarchical_bootstrap(records: list[dict], field: str, seed: int,
                           draws: int) -> list[float]:
    groups: dict[str, list[float]] = {}
    for row in records:
        groups.setdefault(row["instance"], []).append(float(row[field]))
    keys = tuple(groups)
    rng = np.random.default_rng(seed)
    out = np.empty(draws)
    for b in range(draws):
        sampled_keys = rng.choice(keys, size=len(keys), replace=True)
        instance_means = []
        for key in sampled_keys:
            vals = np.asarray(groups[str(key)], dtype=float)
            instance_means.append(float(np.mean(rng.choice(vals, len(vals), replace=True))))
        out[b] = np.mean(instance_means)
    return [float(np.quantile(out, 0.025)), float(np.quantile(out, 0.975))]


def sign_test(values: Iterable[float]) -> float:
    vals = tuple(values)
    pos = sum(v > 0 for v in vals)
    neg = sum(v < 0 for v in vals)
    n = pos + neg
    if n == 0:
        return 1.0
    k = min(pos, neg)
    return float(min(1.0, 2.0 * sum(math.comb(n, i) for i in range(k + 1)) / 2**n))


def parse_instances(text: str) -> tuple[tuple[int, int], ...]:
    if text.strip().lower() == "frozen":
        return FROZEN_INSTANCES
    out = []
    for item in text.split(","):
        n, a = item.split(":")
        out.append((int(n), int(a)))
    return tuple(out)


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    p = argparse.ArgumentParser()
    p.add_argument("--instances", default="frozen",
                   help="'frozen' or comma list such as 15:2,21:2")
    p.add_argument("--meta-seeds", type=int, default=12)
    p.add_argument("--train-per-meta", type=int, default=5)
    p.add_argument("--heldout-per-meta", type=int, default=8)
    p.add_argument("--budget", type=int, default=5520)
    p.add_argument("--bootstrap", type=int, default=10000)
    p.add_argument("--json-out", default="shor_multinstance_fibre_v0_9_4_result.json")
    return p.parse_known_args()


def main() -> int:
    args, unknown = parse_args()
    if unknown:
        print(f"[notice] ignored notebook/kernel arguments: {unknown}")
    pairs = parse_instances(args.instances)
    instances = [build_instance(n, a) for n, a in pairs]
    records: list[dict] = []
    instance_reports = []

    for ii, inst in enumerate(instances):
        local_rows = []
        u0 = multiplier_permutation(inst)
        for m in range(args.meta_seeds):
            meta = stable_seed(inst.N, inst.a, 101 + 1009 * m)
            rng = np.random.default_rng(meta)
            train = tuple(int(x) for x in rng.integers(1, 2**31 - 1,
                                                       args.train_per_meta))
            held = tuple(int(x) for x in rng.integers(1, 2**31 - 1,
                                                      args.heldout_per_meta))
            ti, li = intrinsic_flow(inst, train, args.budget)
            tr, lr = basis_invariant_random(inst, train, args.budget, meta)
            ts, ls = spsa(inst, train, args.budget, meta)
            zero = np.zeros(N_PARAM)
            before = mean_success(inst, zero, held, shifted=True)
            intrinsic = mean_success(inst, ti, held, shifted=True)
            random_value = mean_success(inst, tr, held, shifted=True)
            spsa_value = mean_success(inst, ts, held, shifted=True)
            row = {
                "instance": inst.key,
                "N": inst.N,
                "a": inst.a,
                "exact_order": inst.order,
                "meta_seed": meta,
                "success_before": before,
                "success_intrinsic": intrinsic,
                "success_basis_invariant_random": random_value,
                "success_spsa": spsa_value,
                "intrinsic_minus_before": intrinsic - before,
                "intrinsic_minus_random": intrinsic - random_value,
                "intrinsic_minus_spsa": intrinsic - spsa_value,
                "intrinsic_budget": li.total,
                "random_budget": lr.total,
                "spsa_budget": ls.total,
                "intrinsic_response_residual": float(np.linalg.norm(response(ti))),
                "random_normal_component": float(np.linalg.norm(P_N @ tr)),
                "intrinsic_ideal_multiplier_change": float(
                    np.linalg.norm(ideal_multiplier(inst, ti) - u0)
                ),
            }
            records.append(row)
            local_rows.append(row)
            print(
                f"[{ii+1:02d}/{len(instances):02d} {inst.key} "
                f"{m+1:02d}/{args.meta_seeds:02d}] "
                f"pre={before:.8f} intrinsic={intrinsic:.8f} "
                f"random={random_value:.8f} spsa={spsa_value:.8f} "
                f"budget={li.total}"
            )

        report = {
            "instance": inst.key,
            "N": inst.N,
            "a": inst.a,
            "exact_order": inst.order,
            "control_qubits": inst.control_qubits,
            "success_bins": list(inst.success_bins),
            "ideal_exact_order_probability": inst.ideal_success,
        }
        for field, label, salt in (
            ("intrinsic_minus_before", "intrinsic_vs_reference", 201),
            ("intrinsic_minus_random", "intrinsic_vs_random", 202),
            ("intrinsic_minus_spsa", "intrinsic_vs_spsa", 203),
        ):
            vals = [r[field] for r in local_rows]
            report[label] = {
                "mean": float(np.mean(vals)),
                "bootstrap_95ci": bootstrap_ci(vals, stable_seed(inst.N, inst.a, salt),
                                                 args.bootstrap),
                "win_fraction": float(np.mean(np.asarray(vals) > 0)),
                "sign_p_two_sided": sign_test(vals),
            }
        instance_reports.append(report)

    aggregate = {}
    for field, label, salt in (
        ("intrinsic_minus_before", "intrinsic_vs_reference", 301),
        ("intrinsic_minus_random", "intrinsic_vs_random", 302),
        ("intrinsic_minus_spsa", "intrinsic_vs_spsa", 303),
    ):
        vals = [r[field] for r in records]
        per_instance_means = [
            np.mean([r[field] for r in records if r["instance"] == inst.key])
            for inst in instances
        ]
        aggregate[label] = {
            "equal_instance_weight_mean": float(np.mean(per_instance_means)),
            "hierarchical_bootstrap_95ci": hierarchical_bootstrap(
                records, field, stable_seed(97, 89, salt), args.bootstrap
            ),
            "meta_record_win_fraction": float(np.mean(np.asarray(vals) > 0)),
            "instance_positive_mean_fraction": float(
                np.mean(np.asarray(per_instance_means) > 0)
            ),
            "naive_record_sign_p_two_sided_diagnostic": sign_test(vals),
        }

    budget_gap = max(
        max(r["intrinsic_budget"], r["random_budget"], r["spsa_budget"])
        - min(r["intrinsic_budget"], r["random_budget"], r["spsa_budget"])
        for r in records
    )
    all_exact = all(pow(i.a, i.order, i.N) == 1 and
                    all(pow(i.a, k, i.N) != 1 for k in range(1, i.order))
                    for i in instances)
    max_multiplier_change = max(r["intrinsic_ideal_multiplier_change"] for r in records)
    max_response_residual = max(r["intrinsic_response_residual"] for r in records)
    max_random_normal = max(r["random_normal_component"] for r in records)

    primary_checks = {
        "frozen_instance_family_used": pairs == FROZEN_INSTANCES,
        "all_multiplicative_orders_exact": all_exact,
        "all_success_bin_sets_nonempty": all(len(i.success_bins) > 0 for i in instances),
        "response_rank_five_tangent_dimension_four":
            np.linalg.matrix_rank(RESPONSE_MATRIX) == 5 and TANGENT_DIM == 4,
        "three_way_budget_exact": budget_gap == 0,
        "intrinsic_preserves_declared_response": max_response_residual < 1e-10,
        "intrinsic_preserves_ideal_multiplier": max_multiplier_change < 1e-10,
        "random_comparator_is_tangent": max_random_normal < 1e-10,
        "aggregate_intrinsic_vs_reference_ci_positive":
            aggregate["intrinsic_vs_reference"]["hierarchical_bootstrap_95ci"][0] > 0,
        "aggregate_intrinsic_vs_random_ci_positive":
            aggregate["intrinsic_vs_random"]["hierarchical_bootstrap_95ci"][0] > 0,
        "aggregate_intrinsic_vs_spsa_ci_positive":
            aggregate["intrinsic_vs_spsa"]["hierarchical_bootstrap_95ci"][0] > 0,
        "intrinsic_beats_random_on_majority_of_instances":
            aggregate["intrinsic_vs_random"]["instance_positive_mean_fraction"] >= 2 / 3,
        "intrinsic_beats_spsa_on_majority_of_instances":
            aggregate["intrinsic_vs_spsa"]["instance_positive_mean_fraction"] >= 2 / 3,
    }

    result = {
        "scientific_status": (
            "MULTI_INSTANCE_SHOR_TASK_FIBRE_PREFLIGHT_SUPPORTED"
            if all(primary_checks.values())
            else "MULTI_INSTANCE_SHOR_TASK_FIBRE_PREFLIGHT_NOT_SUPPORTED"
        ),
        "version": VERSION,
        "boundary": (
            "Six small exact state-vector order-finding distributions with a shared "
            "synthetic implementation/noise ansatz; not native gate hardware, fault "
            "tolerance, cryptographic scale, universal Shor optimization, or "
            "asymptotic speedup."
        ),
        "protocol": {
            "instances": [{"N": i.N, "a": i.a, "order": i.order,
                           "control_qubits": i.control_qubits}
                          for i in instances],
            "frozen_default_instances": [list(x) for x in FROZEN_INSTANCES],
            "meta_seeds_per_instance": args.meta_seeds,
            "train_seeds_per_meta": args.train_per_meta,
            "shifted_heldout_seeds_per_meta": args.heldout_per_meta,
            "equal_budget_per_method_per_meta": args.budget,
            "bootstrap_draws": args.bootstrap,
            "random_sampling":
                "v~N(0,I9); theta=r P_Tv/||P_Tv||; r=1.6u^(1/4)",
            "aggregate_inference":
                "paired hierarchical bootstrap; equal instance weight; resample "
                "instances then meta-repetitions",
            "primary_methods": ["intrinsic", "basis_invariant_random", "SPSA"],
        },
        "aggregate": aggregate,
        "instances": instance_reports,
        "audit": {
            "maximum_three_way_budget_gap": int(budget_gap),
            "maximum_intrinsic_response_residual": max_response_residual,
            "maximum_intrinsic_ideal_multiplier_change": max_multiplier_change,
            "maximum_random_normal_component": max_random_normal,
        },
        "records": records,
        "primary_checks": {k: bool(v) for k, v in primary_checks.items()},
        "all_primary_checks_pass": bool(all(primary_checks.values())),
        "interpretation": (
            "A pass supports only cross-instance generalization inside the frozen "
            "synthetic model family. Per-instance failures remain visible and are "
            "not overridden by the aggregate statistic."
        ),
    }
    with open(args.json_out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print(json.dumps(result, indent=2))
    return 0 if result["all_primary_checks_pass"] else 2


if __name__ == "__main__":
    code = main()
    if "ipykernel" not in sys.modules and "google.colab" not in sys.modules:
        raise SystemExit(code)
