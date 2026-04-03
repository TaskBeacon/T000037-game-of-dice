# Game of Dice Task

| Field | Value |
|---|---|
| Name | Game of Dice Task |
| Version | v0.1.0-dev |
| URL / Repository | https://github.com/TaskBeacon/T000037-game-of-dice |
| Short Description | Chinese explicit-risk dice gambling task with four known-probability options and cumulative capital feedback. |
| Created By | TaskBeacon build pipeline |
| Date Updated | 2026-04-03 |
| PsyFlow Version | local checkout |
| PsychoPy Version | 2025.1.1 |
| Modality | Behavior |
| Language | Chinese |
| Voice Name | zh-CN-YunyangNeural |

![Task Flow](./task_flow.png)

## 1. Task Overview

Participants complete an explicit-risk dice betting task with four visible gamble options on each trial. Each option corresponds to betting on 1, 2, 3, or 4 die faces with fixed win/loss magnitudes and known probabilities. The task tracks cumulative capital starting at 1000 points, shows the sampled die result after each valid choice, and then displays win/loss feedback with the updated total. Human mode uses 18 trials in a single block, while QA and simulation configs use shorter 8-trial preview runs for fast validation.

## 2. Task Flow

### Block-Level Flow

| Step | Description |
|---|---|
| Load config | `main.py` loads `config/config.yaml` or the mode-specific QA/sim variant and prepares the task settings. |
| Collect subject info | Human mode collects `subject_id`; QA uses a deterministic stand-in value and sim mode uses the runtime session participant id. |
| Initialize runtime | Triggers, window, keyboard, stimulus bank, and optional instruction voice are initialized. |
| Initialize capital | The running capital state starts at 1000 points and is stored on `settings`. |
| Show instructions | The Chinese instruction screen is shown before the trial block begins. |
| Generate conditions | `BlockUnit.generate_conditions(...)` repeats the single `gdt_standard` condition across the block. |
| Run trials | `run_trial(...)` executes fixation, choice, outcome, feedback, and ITI phases for each trial. |
| Save data | Trial rows are written to CSV and the settings snapshot is saved to JSON. |
| Finalize | The end trigger is emitted, the goodbye screen is closed, and PsychoPy exits. |

### Trial-Level Flow

| Step | Description |
|---|---|
| Fixation | A central fixation cross is shown briefly. |
| Choice screen | The current total, prompt, and four risk cards are shown; the participant presses `1`-`4`. |
| Outcome reveal | If a valid response was made, the sampled die roll and selected option are shown. |
| Feedback | If a valid response was made, the win/loss message and updated capital are shown. |
| Timeout branch | If the response window expires, the trial logs `timeout=true`, skips outcome/feedback, and keeps capital unchanged. |
| ITI | A short fixation interval separates trials. |

### Controller Logic

| Feature | Description |
|---|---|
| Condition scheduling | A single repeated `gdt_standard` label is scheduled by PsyFlow block generation. |
| Capital tracking | `settings.current_capital` and `settings.total_score` are updated after each valid outcome. |
| Response contract | Keys `1`-`4` select the four gamble options; the same keys are used in QA/sim. |
| Adaptive control | None. This is a static explicit-risk task, not a staircase or reversal task. |

### Other Logic

| Feature | Description |
|---|---|
| Deterministic roll | `trial_seed(...)` combines the block seed, block index, trial id, and choice key to produce a reproducible six-sided roll. |
| Outcome evaluation | `compute_choice_outcome(...)` maps the selected option to win/loss magnitude, reward sign, and capital update. |
| Advantageous choice flag | Options with 3 or 4 die faces are marked as advantageous/safe choices for summary reporting. |
| Trial summary | `summarize_gdt_trials(...)` computes win rate, advantageous-choice rate, timeout count, RT, and final capital. |

## 3. Configuration Summary

Settings are defined in `config/config.yaml` and mode-specific variants for QA and simulation.

### a. Subject Info

| Field | Meaning |
|---|---|
| `subject_id` | Numeric participant identifier collected in human mode and injected deterministically in QA/sim modes. |

### b. Window Settings

| Parameter | Value |
|---|---|
| `window.size` | `[1280, 720]` |
| `window.units` | `pix` |
| `window.screen` | `0` |
| `window.bg_color` | `black` |
| `window.fullscreen` | `false` |
| `window.monitor_width_cm` | `35.5` |
| `window.monitor_distance_cm` | `60` |

### c. Stimuli

| Name | Type | Description |
|---|---|---|
| `instruction_text` | text | Chinese instructions describing the four dice betting options and the 1000-point starting capital. |
| `fixation` | text | Central fixation cross shown before choice and during ITI. |
| `capital_banner` | text | Current total capital shown at the top of the choice screen. |
| `choice_prompt` | text | Prompt asking the participant to choose one of the four options. |
| `option_1` / `option_2` / `option_3` / `option_4` | text | Four explicit-risk gamble cards with 1/6, 2/6, 3/6, and 4/6 probabilities. |
| `outcome_text` | text | Die roll reveal and selected option label. |
| `feedback_win` | text | Win feedback with the point gain and updated capital. |
| `feedback_loss` | text | Loss feedback with the point loss and updated capital. |
| `end_summary` | text | Final total capital shown at task completion. |

### d. Timing

| Phase | Duration |
|---|---|
| `timing.fixation_duration` | `0.5 s` |
| `timing.choice_duration` | `10.0 s` in human mode, `8.0 s` in QA/sim configs |
| `timing.outcome_duration` | `0.9 s` |
| `timing.feedback_duration` | `1.0 s` |
| `timing.iti_duration` | `0.8 s` |

### e. Triggers

| Event | Code |
|---|---|
| `exp_onset` | `1` |
| `exp_end` | `2` |
| `block_onset` | `10` |
| `block_end` | `11` |
| `fixation_onset` | `20` |
| `choice_onset` | `30` |
| `choice_response_key` | `31` |
| `choice_timeout` | `32` |
| `outcome_onset` | `40` |
| `feedback_onset` | `50` |
| `iti_onset` | `60` |

### f. Adaptive Controller

| Parameter | Value |
|---|---|
| `task.conditions` | `gdt_standard` repeated across the block |
| `task.condition_weights` | `null` |
| `task.key_list` | `[1, 2, 3, 4]` |
| `task.seed_mode` | `same_across_sub` |
| `task.roll_seed_mode` | `same_across_sub` |
| `task.initial_capital` | `1000` |
| `Adaptive controller` | None; the task uses static condition scheduling and deterministic outcome helpers. |

## 4. Methods (for academic publication)

Participants completed a computerized explicit-risk gambling task implemented in PsychoPy/PsyFlow. On each trial, they chose one of four gambles with known success probabilities and fixed win/loss magnitudes. The participant-facing choice screen displayed the current capital, the four gamble cards, and a single response prompt, while the subsequent outcome screen revealed the sampled die roll and the selected option.

The task operationalizes risk preference through repeated choice behavior and capital accumulation. A valid choice triggers a deterministic die roll derived from a stable seed, followed by win/loss feedback and an updated capital display. If no response is made within the choice window, the trial is logged as a timeout and the capital remains unchanged, preserving the one-trial-one-row analysis contract without fabricating an outcome.

All participant-facing wording is defined in YAML stimulus templates so the same trial logic can be reused across human, QA, and simulation modes without code edits. The human configuration runs 18 trials in one block, whereas QA and simulation configurations shorten the run to 8 trials to support fast validation while preserving the same state sequence, response mapping, and scoring rules.
