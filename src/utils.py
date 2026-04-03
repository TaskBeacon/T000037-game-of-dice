from __future__ import annotations

from typing import Any
import random

from psyflow.sim.rng import stable_int_hash


def normalize_condition_label(condition: Any) -> str:
    """Return a stable lower-case condition label."""
    label = str(condition or "").strip().lower()
    return label or "gdt_standard"


def normalize_choice_key(choice_key: Any) -> str:
    """Return a stable string key for an option choice."""
    key = str(choice_key or "").strip()
    return key


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(round(float(value)))
    except Exception:
        return int(default)


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def option_specs_from_settings(settings) -> dict[str, dict[str, Any]]:
    """Return normalized option metadata keyed by response key."""
    raw_specs = getattr(settings, "option_specs", {}) or {}
    if not isinstance(raw_specs, dict):
        raise TypeError("task.option_specs must be a mapping keyed by choice key")

    specs: dict[str, dict[str, Any]] = {}
    for raw_key, raw_spec in raw_specs.items():
        key = normalize_choice_key(raw_key)
        if not key:
            continue

        spec = dict(raw_spec or {})
        label = str(spec.get("label", f"{key} 个数字")).strip() or f"{key} 个数字"
        match_count = max(1, min(6, _as_int(spec.get("match_count", key), default=1)))
        win_amount = max(0, _as_int(spec.get("win_amount", 0), default=0))
        loss_amount = max(0, _as_int(spec.get("loss_amount", win_amount), default=win_amount))
        win_probability = _as_float(spec.get("win_probability", match_count / 6.0), default=match_count / 6.0)

        specs[key] = {
            "key": key,
            "label": label,
            "match_count": match_count,
            "win_amount": win_amount,
            "loss_amount": loss_amount,
            "win_probability": win_probability,
        }

    if not specs:
        raise ValueError("task.option_specs is empty; Game of Dice needs four explicit options.")

    return dict(
        sorted(
            specs.items(),
            key=lambda item: (0, int(item[0])) if item[0].isdigit() else (1, str(item[0])),
        )
    )


def option_keys_from_settings(settings) -> list[str]:
    """Return the sorted option keys exposed to participants."""
    specs = option_specs_from_settings(settings)
    numeric_keys = [key for key in specs.keys() if key.isdigit()]
    if numeric_keys:
        return sorted(numeric_keys, key=int)
    return list(specs.keys())


def option_spec_for_key(settings, choice_key: Any) -> dict[str, Any]:
    """Look up normalized metadata for a specific choice key."""
    key = normalize_choice_key(choice_key)
    specs = option_specs_from_settings(settings)
    if key not in specs:
        raise KeyError(f"Unknown Game of Dice choice key: {choice_key!r}")
    return dict(specs[key])


def choice_label_for_key(settings, choice_key: Any) -> str:
    """Return the participant-facing label for a choice key."""
    return str(option_spec_for_key(settings, choice_key)["label"])


def choice_expected_value(settings, choice_key: Any) -> float:
    """Return the expected value of a choice."""
    spec = option_spec_for_key(settings, choice_key)
    win_probability = float(spec["win_probability"])
    win_amount = float(spec["win_amount"])
    loss_amount = float(spec["loss_amount"])
    return (win_probability * win_amount) - ((1.0 - win_probability) * loss_amount)


def trial_seed(settings, *, trial_id: int, block_idx: int = 0, choice_key: Any = "") -> int:
    """Create a deterministic per-trial seed."""
    seed_base = int(getattr(settings, "overall_seed", 0))
    block_seed = getattr(settings, "block_seed", None)
    if isinstance(block_seed, (list, tuple)) and 0 <= int(block_idx) < len(block_seed):
        candidate = block_seed[int(block_idx)]
        if candidate is not None:
            try:
                seed_base = int(candidate)
            except Exception:
                seed_base = int(getattr(settings, "overall_seed", 0))

    return stable_int_hash(seed_base, int(block_idx), int(trial_id), "gdt_roll")


def deterministic_roll(settings, *, trial_id: int, block_idx: int, choice_key: Any) -> int:
    """Return a deterministic six-sided die roll in the range 1-6."""
    rng = random.Random(trial_seed(settings, trial_id=trial_id, block_idx=block_idx, choice_key=choice_key))
    return int(rng.randint(1, 6))


def compute_choice_outcome(
    settings,
    *,
    choice_key: Any,
    capital_before: int,
    trial_id: int,
    block_idx: int = 0,
) -> dict[str, Any]:
    """Compute the die roll, win/loss flag, and capital update for one choice."""
    spec = option_spec_for_key(settings, choice_key)
    key = normalize_choice_key(choice_key)
    roll = deterministic_roll(settings, trial_id=trial_id, block_idx=block_idx, choice_key=key)
    reward_win = roll <= int(spec["match_count"])
    reward_delta = int(spec["win_amount"]) if reward_win else -int(spec["loss_amount"])
    capital_after = int(capital_before) + int(reward_delta)
    expected_value = choice_expected_value(settings, key)

    return {
        "choice_key": key,
        "choice_label": str(spec["label"]),
        "choice_match_count": int(spec["match_count"]),
        "choice_win_amount": int(spec["win_amount"]),
        "choice_loss_amount": int(spec["loss_amount"]),
        "choice_win_probability": float(spec["win_probability"]),
        "choice_expected_value": float(expected_value),
        "choice_risk_tier": int(spec["match_count"]),
        "reward_win": bool(reward_win),
        "reward_delta": int(reward_delta),
        "capital_after": int(capital_after),
        "total_score": int(capital_after),
        "roll": int(roll),
        "outcome_label": "win" if reward_win else "loss",
        "advantageous_choice": bool(int(spec["match_count"]) >= 3),
        "risky_choice": bool(int(spec["match_count"]) <= 2),
    }


def summarize_gdt_trials(
    trials: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    *,
    initial_capital: int,
) -> dict[str, float | int]:
    """Summarize a list of Game of Dice trial rows."""
    trial_list = list(trials or [])
    responded = [row for row in trial_list if not bool(row.get("timeout", False))]

    win_count = sum(1 for row in responded if bool(row.get("reward_win", False)))
    loss_count = sum(1 for row in responded if not bool(row.get("reward_win", False)))
    timeout_count = sum(1 for row in trial_list if bool(row.get("timeout", False)))
    risky_choice_count = sum(1 for row in responded if bool(row.get("risky_choice", False)))
    advantageous_choice_count = sum(1 for row in responded if bool(row.get("advantageous_choice", False)))

    choice_rts: list[float] = []
    total_delta = 0
    capital_end = int(initial_capital)
    for row in trial_list:
        reward_delta = row.get("reward_delta")
        if isinstance(reward_delta, (int, float)):
            total_delta += int(round(float(reward_delta)))

        capital_after = row.get("capital_after", row.get("total_score"))
        if isinstance(capital_after, (int, float)):
            capital_end = int(round(float(capital_after)))

        choice_rt = row.get("choice_rt", row.get("response_rt"))
        if isinstance(choice_rt, (int, float)):
            choice_rts.append(float(choice_rt))

    response_count = len(responded)
    mean_choice_rt = sum(choice_rts) / len(choice_rts) if choice_rts else 0.0
    win_rate = (win_count / response_count) if response_count else 0.0
    risky_choice_rate = (risky_choice_count / response_count) if response_count else 0.0
    advantageous_choice_rate = (advantageous_choice_count / response_count) if response_count else 0.0

    return {
        "n_trials": int(len(trial_list)),
        "n_responded": int(response_count),
        "n_timeouts": int(timeout_count),
        "win_count": int(win_count),
        "loss_count": int(loss_count),
        "win_rate": float(win_rate),
        "mean_choice_rt": float(mean_choice_rt),
        "risky_choice_count": int(risky_choice_count),
        "risky_choice_rate": float(risky_choice_rate),
        "advantageous_choice_count": int(advantageous_choice_count),
        "advantageous_choice_rate": float(advantageous_choice_rate),
        "capital_start": int(initial_capital),
        "capital_end": int(capital_end),
        "capital_change": int(capital_end - int(initial_capital)),
        "total_reward_delta": int(total_delta),
    }
