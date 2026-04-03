from __future__ import annotations

from functools import partial
from typing import Any

from psyflow import StimUnit, next_trial_id, set_trial_context

from .utils import (
    choice_label_for_key,
    choice_expected_value,
    compute_choice_outcome,
    normalize_condition_label,
    option_keys_from_settings,
    option_spec_for_key,
    summarize_gdt_trials,
)


def _valid_choice_keys(settings) -> list[str]:
    configured = [str(key).strip() for key in list(getattr(settings, "key_list", [])) if str(key).strip()]
    option_keys = option_keys_from_settings(settings)
    if configured:
        valid = [key for key in configured if key in option_keys]
        if valid:
            return valid
    return option_keys


def _capital_from_settings(settings) -> int:
    capital = getattr(settings, "current_capital", None)
    if capital is None:
        capital = getattr(settings, "initial_capital", 1000)
    try:
        return int(capital)
    except Exception:
        return 1000


def _update_capital(settings, value: int) -> int:
    capital = int(value)
    setattr(settings, "current_capital", capital)
    setattr(settings, "total_score", capital)
    return capital


def _choice_trigger_map(settings, valid_keys: list[str]) -> dict[str, int | None]:
    trigger = settings.triggers.get("choice_response_key")
    return {key: trigger for key in valid_keys}


def _choice_stim_id(choice_keys: list[str]) -> str:
    return "capital_banner+choice_prompt+" + "+".join(f"option_{key}" for key in choice_keys)


def run_trial(
    win,
    kb,
    settings,
    condition,
    stim_bank,
    trigger_runtime,
    block_id=None,
    block_idx=None,
):
    """Run one explicit-risk Game of Dice trial."""
    condition_label = normalize_condition_label(condition)
    trial_id = int(next_trial_id())
    block_id_str = str(block_id) if block_id is not None else "block_0"
    block_index = int(block_idx) if block_idx is not None else 0

    fixation_duration = float(getattr(settings, "fixation_duration", 0.5))
    choice_duration = float(getattr(settings, "choice_duration", getattr(settings, "choice_timeout_s", 10.0)))
    outcome_duration = float(getattr(settings, "outcome_duration", 0.9))
    feedback_duration = float(getattr(settings, "feedback_duration", 1.0))
    iti_duration = float(getattr(settings, "iti_duration", 0.8))

    choice_keys = option_keys_from_settings(settings)
    valid_keys = _valid_choice_keys(settings)
    if not valid_keys:
        valid_keys = list(choice_keys)

    capital_before = _capital_from_settings(settings)
    _update_capital(settings, capital_before)

    trial_data: dict[str, Any] = {
        "trial_id": trial_id,
        "block_id": block_id_str,
        "block_idx": block_index,
        "condition": condition_label,
        "condition_id": condition_label,
        "capital_before": capital_before,
        "capital_after": capital_before,
        "total_score": capital_before,
        "timeout": False,
        "responded": False,
    }

    make_unit = partial(StimUnit, win=win, kb=kb, runtime=trigger_runtime)

    fixation = make_unit(unit_label="fixation").add_stim(stim_bank.get("fixation"))
    set_trial_context(
        fixation,
        trial_id=trial_id,
        phase="fixation",
        deadline_s=fixation_duration,
        valid_keys=[],
        block_id=block_id_str,
        condition_id=condition_label,
        task_factors={
            "stage": "fixation",
            "condition": condition_label,
            "capital_before": capital_before,
            "block_idx": block_index,
        },
        stim_id="fixation",
    )
    fixation.show(
        duration=fixation_duration,
        onset_trigger=settings.triggers.get("fixation_onset"),
    ).to_dict(trial_data)

    choice_screen = make_unit(unit_label="choice_screen")
    choice_screen.add_stim(stim_bank.get_and_format("capital_banner", capital=capital_before))
    choice_screen.add_stim(stim_bank.get("choice_prompt"))
    for key in choice_keys:
        choice_screen.add_stim(stim_bank.get(f"option_{key}"))

    choice_labels = {key: choice_label_for_key(settings, key) for key in choice_keys}
    set_trial_context(
        choice_screen,
        trial_id=trial_id,
        phase="choice_screen",
        deadline_s=choice_duration,
        valid_keys=valid_keys,
        block_id=block_id_str,
        condition_id=condition_label,
        task_factors={
            "stage": "choice_screen",
            "condition": condition_label,
            "capital_before": capital_before,
            "choice_keys": choice_keys,
            "choice_labels": choice_labels,
            "block_idx": block_index,
        },
        stim_id=_choice_stim_id(choice_keys),
        stim_features={
            "choice_keys": choice_keys,
            "choice_labels": choice_labels,
            "capital_before": capital_before,
            "choice_timeout_s": choice_duration,
        },
    )
    choice_screen.capture_response(
        keys=valid_keys,
        duration=choice_duration,
        correct_keys=valid_keys,
        onset_trigger=settings.triggers.get("choice_onset"),
        response_trigger=_choice_trigger_map(settings, valid_keys),
        timeout_trigger=settings.triggers.get("choice_timeout"),
    )
    choice_screen.to_dict(trial_data)

    response_key = str(choice_screen.get_state("response", "") or "").strip()
    choice_rt = choice_screen.get_state("rt", None)
    response_rt = float(choice_rt) if isinstance(choice_rt, (int, float)) else None
    choice_key = response_key if response_key in valid_keys else ""
    timeout = not bool(choice_key)

    trial_data.update(
        {
            "choice_key": choice_key,
            "choice_label": choice_labels.get(choice_key, "") if choice_key else "",
            "choice_rt": response_rt,
            "response_key": choice_key,
            "response_rt": response_rt,
            "timeout": bool(timeout),
            "responded": not bool(timeout),
        }
    )

    if timeout:
        trial_data.update(
            {
                "choice_match_count": None,
                "choice_win_amount": None,
                "choice_loss_amount": None,
                "choice_win_probability": None,
                "choice_expected_value": None,
                "choice_risk_tier": None,
                "reward_win": False,
                "reward_delta": 0,
                "capital_after": capital_before,
                "total_score": capital_before,
                "roll": None,
                "outcome_label": "timeout",
                "advantageous_choice": False,
                "risky_choice": False,
            }
        )
    else:
        outcome = compute_choice_outcome(
            settings,
            choice_key=choice_key,
            capital_before=capital_before,
            trial_id=trial_id,
            block_idx=block_index,
        )
        outcome_screen = make_unit(unit_label="outcome_reveal").add_stim(
            stim_bank.get_and_format(
                "outcome_text",
                roll=outcome["roll"],
                choice_label=outcome["choice_label"],
            )
        )
        set_trial_context(
            outcome_screen,
            trial_id=trial_id,
            phase="outcome_reveal",
            deadline_s=outcome_duration,
            valid_keys=[],
            block_id=block_id_str,
            condition_id=condition_label,
            task_factors={
                "stage": "outcome_reveal",
                "condition": condition_label,
                "choice_key": choice_key,
                "choice_label": outcome["choice_label"],
                "choice_match_count": outcome["choice_match_count"],
                "roll": outcome["roll"],
                "reward_win": outcome["reward_win"],
                "reward_delta": outcome["reward_delta"],
                "capital_before": capital_before,
                "capital_after": outcome["capital_after"],
                "block_idx": block_index,
            },
            stim_id="outcome_text",
            stim_features={
                "choice_key": choice_key,
                "choice_label": outcome["choice_label"],
                "roll": outcome["roll"],
                "reward_win": outcome["reward_win"],
            },
        )
        outcome_screen.show(
            duration=outcome_duration,
            onset_trigger=settings.triggers.get("outcome_onset"),
        ).to_dict(trial_data)

        feedback_stim_id = "feedback_win" if bool(outcome["reward_win"]) else "feedback_loss"
        feedback_screen = make_unit(unit_label="feedback").add_stim(
            stim_bank.get_and_format(
                feedback_stim_id,
                delta=abs(int(outcome["reward_delta"])),
                capital=outcome["capital_after"],
            )
        )
        set_trial_context(
            feedback_screen,
            trial_id=trial_id,
            phase="feedback",
            deadline_s=feedback_duration,
            valid_keys=[],
            block_id=block_id_str,
            condition_id=condition_label,
            task_factors={
                "stage": "feedback",
                "condition": condition_label,
                "choice_key": choice_key,
                "choice_label": outcome["choice_label"],
                "reward_win": outcome["reward_win"],
                "reward_delta": outcome["reward_delta"],
                "capital_before": capital_before,
                "capital_after": outcome["capital_after"],
                "block_idx": block_index,
            },
            stim_id=feedback_stim_id,
            stim_features={
                "choice_key": choice_key,
                "choice_label": outcome["choice_label"],
                "reward_delta": outcome["reward_delta"],
                "capital_after": outcome["capital_after"],
            },
        )
        feedback_screen.show(
            duration=feedback_duration,
            onset_trigger=settings.triggers.get("feedback_onset"),
        ).to_dict(trial_data)

        capital_before = int(outcome["capital_after"])
        _update_capital(settings, capital_before)
        trial_data.update(outcome)

    iti = make_unit(unit_label="iti").add_stim(stim_bank.get("fixation"))
    set_trial_context(
        iti,
        trial_id=trial_id,
        phase="iti",
        deadline_s=iti_duration,
        valid_keys=[],
        block_id=block_id_str,
        condition_id=condition_label,
        task_factors={
            "stage": "iti",
            "condition": condition_label,
            "capital_after": int(getattr(settings, "current_capital", capital_before)),
            "block_idx": block_index,
        },
        stim_id="fixation",
    )
    iti.show(
        duration=iti_duration,
        onset_trigger=settings.triggers.get("iti_onset"),
    ).to_dict(trial_data)

    trial_data.setdefault("reward_win", False)
    trial_data.setdefault("reward_delta", 0)
    trial_data.setdefault("capital_after", int(getattr(settings, "current_capital", capital_before)))
    trial_data.setdefault("total_score", int(getattr(settings, "total_score", capital_before)))
    trial_data.setdefault("roll", None)
    trial_data.setdefault("choice_match_count", None)
    trial_data.setdefault("choice_win_amount", None)
    trial_data.setdefault("choice_loss_amount", None)
    trial_data.setdefault("choice_win_probability", None)
    trial_data.setdefault("choice_expected_value", None)
    trial_data.setdefault("choice_risk_tier", None)
    trial_data.setdefault("advantageous_choice", False)
    trial_data.setdefault("risky_choice", False)

    return trial_data
