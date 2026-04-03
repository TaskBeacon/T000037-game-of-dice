# Task Plot Audit

- generated_at: 2026-04-03T20:51:17
- mode: existing
- task_path: E:\Taskbeacon\T000037-game-of-dice

## 1. Inputs and provenance

- E:\Taskbeacon\T000037-game-of-dice\README.md
- E:\Taskbeacon\T000037-game-of-dice\config\config.yaml
- E:\Taskbeacon\T000037-game-of-dice\src\run_trial.py

## 2. Evidence extracted from README

- | Step | Description |
- |---|---|
- | Fixation | A central fixation cross is shown briefly. |
- | Choice screen | The current total, prompt, and four risk cards are shown; the participant presses `1`-`4`. |
- | Outcome reveal | If a valid response was made, the sampled die roll and selected option are shown. |
- | Feedback | If a valid response was made, the win/loss message and updated capital are shown. |
- | Timeout branch | If the response window expires, the trial logs `timeout=true`, skips outcome/feedback, and keeps capital unchanged. |
- | ITI | A short fixation interval separates trials. |

## 3. Evidence extracted from config/source

- gdt_standard: phase=fixation, deadline_expr=fixation_duration, response_expr=n/a, stim_expr='fixation'
- gdt_standard: phase=choice screen, deadline_expr=choice_duration, response_expr=choice_duration, stim_expr=_choice_stim_id(choice_keys)
- gdt_standard: phase=iti, deadline_expr=iti_duration, response_expr=n/a, stim_expr='fixation'

## 4. Mapping to task_plot_spec

- timeline collection: one representative timeline per unique trial logic
- phase flow inferred from run_trial set_trial_context order and branch predicates
- participant-visible show() phases without set_trial_context are inferred where possible and warned
- duration/response inferred from deadline/capture expressions
- stimulus examples inferred from stim_id + config stimuli
- conditions with equivalent phase/timing logic collapsed and annotated as variants
- root_key: task_plot_spec
- spec_version: 0.2

## 5. Style decision and rationale

- Single timeline-collection view selected by policy: one representative condition per unique timeline logic.

## 6. Rendering parameters and constraints

- output_file: task_flow.png
- dpi: 300
- max_conditions: 4
- screens_per_timeline: 6
- screen_overlap_ratio: 0.1
- screen_slope: 0.08
- screen_slope_deg: 25.0
- screen_aspect_ratio: 1.4545454545454546
- qa_mode: local
- auto_layout_feedback:
  - layout pass 1: crop-only; left=0.038, right=0.038, blank=0.148
- auto_layout_feedback_records:
  - pass: 1
    metrics: {'left_ratio': 0.0383, 'right_ratio': 0.0383, 'blank_ratio': 0.1482}

## 7. Output files and checksums

- E:\Taskbeacon\T000037-game-of-dice\references\task_plot_spec.yaml: sha256=792d0ab37256ebaa8dab46f92dc0960df9ad46aff4008398f26f5c962837f6f7
- E:\Taskbeacon\T000037-game-of-dice\references\task_plot_spec.json: sha256=f2387c7e7d8483542d2fa535330127a0946a723ad7c358a432879b8e52bea367
- E:\Taskbeacon\T000037-game-of-dice\references\task_plot_source_excerpt.md: sha256=3b991891470440442ee5ae974a3544b2a8c0d0dc4bbb031670812d7b87306d96
- E:\Taskbeacon\T000037-game-of-dice\task_flow.png: sha256=b726a4376eb795ff459bed828c5497de3a224eced7435cfa449944322aa4fae5

## 8. Inferred/uncertain items

- gdt_standard:fixation:heuristic numeric parse from 'float(getattr(settings, 'fixation_duration', 0.5))'
- gdt_standard:choice screen:heuristic numeric parse from 'float(getattr(settings, 'choice_duration', getattr(settings, 'choice_timeout_s', 10.0)))'
- gdt_standard:iti:heuristic numeric parse from 'float(getattr(settings, 'iti_duration', 0.8))'
- unparsed if-tests defaulted to condition-agnostic applicability: not valid_keys; timeout
