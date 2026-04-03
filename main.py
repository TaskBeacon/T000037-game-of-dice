from contextlib import nullcontext
from functools import partial
from pathlib import Path

import pandas as pd
from psychopy import core

from psyflow import (
    BlockUnit,
    StimBank,
    StimUnit,
    SubInfo,
    TaskRunOptions,
    TaskSettings,
    context_from_config,
    count_down,
    initialize_exp,
    initialize_triggers,
    load_config,
    parse_task_run_options,
    runtime_context,
)

from src import run_trial, summarize_gdt_trials


MODES = ("human", "qa", "sim")
DEFAULT_CONFIG_BY_MODE = {
    "human": "config/config.yaml",
    "qa": "config/config_qa.yaml",
    "sim": "config/config_scripted_sim.yaml",
}


def _collect_subject_data(options: TaskRunOptions, cfg: dict, runtime_ctx) -> dict[str, str]:
    if options.mode == "qa":
        return {"subject_id": "qa"}
    if options.mode == "sim":
        participant_id = "sim"
        if runtime_ctx is not None and runtime_ctx.session is not None:
            participant_id = str(runtime_ctx.session.participant_id or "sim")
        return {"subject_id": participant_id}

    subform = SubInfo(cfg["subform_config"])
    return subform.collect()


def _show_block_break(
    *,
    settings: TaskSettings,
    stim_bank: StimBank,
    win,
    kb,
    trigger_runtime,
    summary: dict[str, float | int],
    block_num: int,
) -> None:
    if not stim_bank.has("block_break"):
        return

    StimUnit("block", win, kb, runtime=trigger_runtime).add_stim(
        stim_bank.get_and_format(
            "block_break",
            block_num=block_num,
            total_blocks=int(settings.total_blocks),
            mean_rating=summary.get("mean_choice_rt", 0.0),
            mean_rt=summary.get("mean_choice_rt", 0.0),
            current_total=summary.get("capital_end", 0),
            total_score=summary.get("capital_end", 0),
            block_net=summary.get("capital_change", 0),
            adv_rate=summary.get("advantageous_choice_rate", 0.0),
            deck_a_count=summary.get("risky_choice_count", 0),
            deck_b_count=0,
            deck_c_count=0,
            deck_d_count=0,
            timeout_count=summary.get("n_timeouts", 0),
        )
    ).wait_and_continue()


def run(options: TaskRunOptions):
    """Run the Game of Dice task in human/qa/sim mode."""
    task_root = Path(__file__).resolve().parent
    cfg = load_config(str(options.config_path))

    output_dir: Path | None = None
    runtime_scope = nullcontext()
    runtime_ctx = None
    if options.mode in ("qa", "sim"):
        runtime_ctx = context_from_config(task_dir=task_root, config=cfg, mode=options.mode)
        output_dir = runtime_ctx.output_dir
        runtime_scope = runtime_context(runtime_ctx)

    with runtime_scope:
        subject_data = _collect_subject_data(options, cfg, runtime_ctx)

        settings = TaskSettings.from_dict(cfg["task_config"])
        if options.mode in ("qa", "sim") and output_dir is not None:
            settings.save_path = str(output_dir)
        settings.add_subinfo(subject_data)
        settings.current_capital = int(getattr(settings, "initial_capital", 1000))
        settings.total_score = int(settings.current_capital)

        if options.mode == "qa" and output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            settings.res_file = str(output_dir / "qa_trace.csv")
            settings.log_file = str(output_dir / "qa_psychopy.log")
            settings.json_file = str(output_dir / "qa_settings.json")

        settings.triggers = cfg["trigger_config"]
        trigger_runtime = initialize_triggers(mock=True) if options.mode in ("qa", "sim") else initialize_triggers(cfg)

        win, kb = initialize_exp(settings)

        stim_bank = StimBank(win, cfg["stim_config"])
        if options.mode == "human" and bool(getattr(settings, "voice_enabled", False)):
            stim_bank = stim_bank.convert_to_voice(
                "instruction_text",
                voice=str(getattr(settings, "voice_name", "zh-CN-YunyangNeural")),
            )
        stim_bank = stim_bank.preload_all()

        settings.controller = cfg.get("controller_config", {})
        settings.save_to_json()

        trigger_runtime.send(settings.triggers.get("exp_onset"))

        instruction = StimUnit("instruction_text", win, kb, runtime=trigger_runtime).add_stim(
            stim_bank.get("instruction_text")
        )
        if options.mode == "human" and stim_bank.has("instruction_text_voice"):
            instruction.add_stim(stim_bank.get("instruction_text_voice"))
        instruction.wait_and_continue()

        all_data: list[dict] = []
        condition_weights = settings.resolve_condition_weights()
        for block_i in range(int(settings.total_blocks)):
            if options.mode == "human":
                count_down(win, 3, color="black")

            block = (
                BlockUnit(
                    block_id=f"block_{block_i}",
                    block_idx=block_i,
                    settings=settings,
                    window=win,
                    keyboard=kb,
                )
                .generate_conditions(
                    n_trials=int(settings.trials_per_block),
                    condition_labels=list(getattr(settings, "conditions", [])),
                    weights=condition_weights,
                    order="random",
                )
                .on_start(lambda b: trigger_runtime.send(settings.triggers.get("block_onset")))
                .on_end(lambda b: trigger_runtime.send(settings.triggers.get("block_end")))
                .run_trial(
                    partial(
                        run_trial,
                        stim_bank=stim_bank,
                        trigger_runtime=trigger_runtime,
                        block_id=f"block_{block_i}",
                        block_idx=block_i,
                    )
                )
                .to_dict(all_data)
            )

            if int(settings.total_blocks) > 1 and block_i < int(settings.total_blocks) - 1:
                block_summary = summarize_gdt_trials(block.get_all_data(), initial_capital=int(settings.initial_capital))
                _show_block_break(
                    settings=settings,
                    stim_bank=stim_bank,
                    win=win,
                    kb=kb,
                    trigger_runtime=trigger_runtime,
                    summary=block_summary,
                    block_num=block_i + 1,
                )

        final_summary = summarize_gdt_trials(all_data, initial_capital=int(getattr(settings, "initial_capital", 1000)))
        StimUnit("goodbye", win, kb, runtime=trigger_runtime).add_stim(
            stim_bank.get_and_format(
                "end_summary",
                capital=final_summary["capital_end"],
            )
        ).wait_and_continue(terminate=True)

        trigger_runtime.send(settings.triggers.get("exp_end"))

        pd.DataFrame(all_data).to_csv(settings.res_file, index=False)

        trigger_runtime.close()
        core.quit()


def main() -> None:
    task_root = Path(__file__).resolve().parent
    options = parse_task_run_options(
        task_root=task_root,
        description="Run Game of Dice in human/qa/sim mode.",
        default_config_by_mode=DEFAULT_CONFIG_BY_MODE,
        modes=MODES,
    )
    run(options)


if __name__ == "__main__":
    main()
