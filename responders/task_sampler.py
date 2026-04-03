from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import random as _py_random

from psyflow.sim.contracts import Action, Feedback, Observation, SessionInfo


def _obs_get(obs: Observation | dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(obs, dict):
        return obs.get(key, default)
    return getattr(obs, key, default)


def _normalize_key(key: Any) -> str:
    return str(key or "").strip()


def _normalize_phase(obs: Observation | dict[str, Any]) -> str:
    phase = _normalize_key(_obs_get(obs, "phase", ""))
    if phase:
        return phase.lower()
    factors = dict(_obs_get(obs, "task_factors", {}) or {})
    return _normalize_key(factors.get("stage", "")).lower()


def _numeric_keys(valid_keys: list[str]) -> list[str]:
    return sorted({key for key in valid_keys if str(key).isdigit()}, key=int)


def _trial_index(obs: Observation | dict[str, Any]) -> int:
    trial_id = _obs_get(obs, "trial_id", None)
    try:
        return max(1, int(trial_id))
    except Exception:
        factors = dict(_obs_get(obs, "task_factors", {}) or {})
        try:
            return max(1, int(factors.get("trial_index", 1)))
        except Exception:
            return 1


@dataclass
class TaskSamplerResponder:
    """Task-specific sampler for the Game of Dice Task."""

    rt_mean_s: float = 0.48
    rt_sd_s: float = 0.08
    rt_min_s: float = 0.15
    choice_cycle_offset: int = 0

    def __post_init__(self) -> None:
        self._rng: Any = None
        self.rt_mean_s = float(self.rt_mean_s)
        self.rt_sd_s = max(1e-6, float(self.rt_sd_s))
        self.rt_min_s = max(0.0, float(self.rt_min_s))
        self.choice_cycle_offset = int(self.choice_cycle_offset)

    def start_session(self, session: SessionInfo, rng: Any) -> None:
        self._rng = rng

    def end_session(self) -> None:
        self._rng = None

    def on_feedback(self, fb: Feedback) -> None:
        return None

    def _sample_rt(self) -> float:
        rng = self._rng
        if hasattr(rng, "normal"):
            sample = float(rng.normal(self.rt_mean_s, self.rt_sd_s))
        elif hasattr(rng, "gauss"):
            sample = float(rng.gauss(self.rt_mean_s, self.rt_sd_s))
        else:
            sample = float(self.rt_mean_s)
        return max(self.rt_min_s, sample)

    def _sample_random(self) -> float:
        rng = self._rng
        if hasattr(rng, "random"):
            return float(rng.random())
        return float(_py_random.random())

    def _choose_choice_key(self, obs: Observation | dict[str, Any], valid_keys: list[str]) -> str | None:
        numeric_valid = _numeric_keys(valid_keys)
        if numeric_valid:
            idx = (_trial_index(obs) - 1 + self.choice_cycle_offset) % len(numeric_valid)
            return numeric_valid[idx]
        if "space" in valid_keys:
            return "space"
        return valid_keys[0] if valid_keys else None

    def _choose_continue_key(self, valid_keys: list[str]) -> str | None:
        if "space" in valid_keys:
            return "space"
        return valid_keys[0] if valid_keys else None

    def act(self, obs: Observation | dict[str, Any]) -> Action:
        valid_keys = [_normalize_key(key) for key in list(_obs_get(obs, "valid_keys", []) or []) if _normalize_key(key)]
        if not valid_keys:
            return Action(key=None, rt_s=None, meta={"source": "task_sampler", "reason": "no_valid_keys"})

        if self._rng is None:
            return Action(key=None, rt_s=None, meta={"source": "task_sampler", "reason": "rng_missing"})

        rt = self._sample_rt()
        phase = _normalize_phase(obs)
        numeric_valid = _numeric_keys(valid_keys)
        is_choice_phase = any(token in phase for token in ("choice", "decision", "response"))

        if numeric_valid and is_choice_phase:
            key = self._choose_choice_key(obs, valid_keys)
            if key is None:
                return Action(key=None, rt_s=None, meta={"source": "task_sampler", "reason": "no_choice_key"})
            return Action(
                key=key,
                rt_s=rt,
                meta={
                    "source": "task_sampler",
                    "phase": phase,
                    "mode": "choice_cycle",
                    "trial_index": _trial_index(obs),
                    "chosen_key": key,
                },
            )

        key = self._choose_continue_key(valid_keys)
        if key is None:
            return Action(key=None, rt_s=None, meta={"source": "task_sampler", "reason": "no_continue_key"})

        return Action(
            key=key,
            rt_s=rt,
            meta={
                "source": "task_sampler",
                "phase": phase,
                "mode": "continue",
                "chosen_key": key,
                "random_probe": self._sample_random(),
            },
        )
