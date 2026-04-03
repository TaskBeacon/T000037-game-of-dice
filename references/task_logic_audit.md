# Task Logic Audit

Use this file as `references/task_logic_audit.md` before coding.

**WARNING:** DO NOT fill this template by reverse-engineering existing code (`src/run_trial.py`) or using automated scripts. You MUST extract the trial flow, timing, and conditions directly from the text, figures, and tables of the selected literature.
**WARNING:** If this task was initialized from MID (or any other task), treat that source as structure-only scaffolding. Rebuild the paradigm state machine from zero-base literature logic.

## 1. Paradigm Intent

- Task: Game of Dice Task
- Primary construct: explicit-risk decision making under known probabilities
- Manipulated factors:
  - Risk level of the chosen gamble option
  - Trial-by-trial outcome feedback
  - Deterministic outcome generation for reproducible QA/simulation
- Dependent measures:
  - Risky choice frequency
  - Advantageous vs disadvantageous choice rate
  - Choice response time
  - Cumulative capital / score
- Key citations:
  - `W2161561914` - decision-making impairments in Parkinsonian samples with explicit-risk gambling
  - `W2128601759` - gambling/decision-making in Parkinson's disease with and without pathological gambling
  - `W1999635028` - high-impact risk/impulse-control paper in *Brain*
  - `W2901004383` - open-access methodological paper on risk-taking measures

## 2. Block/Trial Workflow

### Block Structure

- Total blocks: 1
- Trials per block: 18
- Randomization/counterbalancing:
  - Single block with 18 decision trials
  - Trial outcomes are randomized with a deterministic seed
  - The four gamble options are presented in a stable left-to-right order for readability
- Condition generation method:
  - Built-in `BlockUnit.generate_conditions(...)`
  - A single repeated condition label is sufficient because the trial variability is generated at runtime from the die outcome
  - Generated condition data shape passed into `run_trial.py`: repeated string label, e.g. `gdt_standard`
- Runtime-generated trial values (if any):
  - Die roll outcome is sampled in `run_trial.py`
  - Total capital is updated trial by trial
  - Generation should be deterministic via `overall_seed` + block/trial index or an equivalent per-trial RNG seed

### Trial State Machine

List each state in order with entry/exit conditions:

1. State name: fixation
   - Onset trigger: `fixation_onset`
   - Stimuli shown: central fixation cross
   - Valid keys: none
   - Timeout behavior: automatic advance after fixed duration
   - Next state: choice_screen
2. State name: choice_screen
   - Onset trigger: `choice_onset`
   - Stimuli shown: current capital banner, choice prompt, and four gamble option cards
   - Valid keys: `1`, `2`, `3`, `4`
   - Timeout behavior: record `timeout=true`, skip outcome/feedback, and advance with no score update
   - Next state on valid response: outcome_reveal; next state on timeout: iti
3. State name: outcome_reveal
   - Onset trigger: `outcome_onset`
   - Stimuli shown: rolled die result or numeric die-face equivalent
   - Valid keys: none
   - Timeout behavior: automatic advance after fixed duration
   - Next state: feedback
4. State name: feedback
   - Onset trigger: `feedback_onset`
   - Stimuli shown: win/loss message and updated capital
   - Valid keys: none
   - Timeout behavior: automatic advance after fixed duration
   - Next state: iti
5. State name: iti
   - Onset trigger: `iti_onset`
   - Stimuli shown: fixation cross
   - Valid keys: none
   - Timeout behavior: automatic advance after fixed duration
   - Next state: next trial / end of block

## 3. Condition Semantics

For each condition token in `task.conditions`:

- Condition ID: `gdt_standard`
- Participant-facing meaning: choose one of four explicit-risk gambles with different payoff/probability tradeoffs
- Concrete stimulus realization (visual/audio):
  - Four horizontally arranged option cards
  - Option 1: `1 个数字`, `+1000 / -1000`, probability `1/6`
  - Option 2: `2 个数字`, `+500 / -500`, probability `2/6`
  - Option 3: `3 个数字`, `+200 / -200`, probability `3/6`
  - Option 4: `4 个数字`, `+100 / -100`, probability `4/6`
  - Die roll result shown after choice as a number or die-face equivalent
- Outcome rules:
  - Roll a fair six-sided die
  - If the roll matches one of the chosen numbers, the participant wins the stated amount
  - Otherwise the participant loses the same magnitude
  - Update the running capital immediately after outcome resolution

Also document where participant-facing condition text/stimuli are defined:

- Participant-facing text source (config stimuli / code formatting / generated assets): `config/config.yaml` stimuli plus formatted score/outcome text from `src/utils.py`
- Why this source is appropriate for auditability: all participant-visible wording lives in config, while the code only fills in numerically generated values such as the die outcome and capital update
- Localization strategy (how language variants are swapped via config without code edits): the trial runner references stimulus IDs only; changing the YAML text block localizes instructions/options without changing trial logic

## 4. Response and Scoring Rules

- Response mapping: `1`, `2`, `3`, `4` correspond to the four gamble cards from most risky/highest payoff to safest/lowest payoff
- Response key source (config field vs code constant): config-driven `task.key_list` and option definitions in `config/config.yaml`
- If code-defined, why config-driven mapping is not sufficient: not needed; config is sufficient
- Missing-response policy:
  - Treat timeout as a missed decision
  - Log `timeout=true`
  - Skip outcome and feedback screens on timeout
  - Advance to ITI without changing the score
  - In QA/sim, the responder is configured to avoid timeouts
- Correctness logic:
  - There is no binary correctness
  - Outcome is probability-based rather than right/wrong
- Reward/penalty updates:
  - Add the option-specific win amount on success
  - Subtract the same amount on failure
  - Maintain a cumulative capital variable starting at 1000
- Running metrics:
  - Current capital
  - Risky-choice count
  - Advantageous-choice count
  - Mean choice RT

## 5. Stimulus Layout Plan

For every screen with multiple simultaneous options/stimuli:

- Screen name: choice_screen
- Stimulus IDs shown together:
  - current capital banner
  - four gamble option cards
  - one brief instruction/prompt line
- Layout anchors (`pos`):
  - current capital banner: top center
  - prompt: upper middle
  - four option cards: horizontal row centered around screen midpoint
- Size/spacing (`height`, width, wrap):
  - Option cards should use consistent text height and wrapping to keep the payoff/probability text readable
  - Cards should be evenly spaced left-to-right with enough margin to avoid overlap on a 1280x720 window
- Readability/overlap checks:
  - Verify each card title, payoff line, and probability line are legible without collision
  - Ensure the current capital line does not overlap the option row
- Rationale:
  - A four-card horizontal row is the most direct way to expose the explicit-risk tradeoff while preserving keyboard or button selection clarity

## 6. Trigger Plan

Map each phase/state to trigger code and semantics.

- `exp_onset`: experiment start
- `fixation_onset`: fixation and capital banner display
- `choice_onset`: gamble option presentation
- `choice_key`: key-specific response trigger for 1-4 choice
- `choice_timeout`: response window timeout
- `outcome_onset`: die result reveal
- `feedback_onset`: win/loss and updated capital
- `iti_onset`: inter-trial fixation
- `exp_end`: experiment end

## 7. Architecture Decisions (Auditability)

- `main.py` runtime flow style (simple single flow / helper-heavy / why): simple single flow with one block and one trial runner
- `utils.py` used? (yes/no): yes
- If yes, exact purpose (adaptive controller / sequence generation / asset pool / other): task-specific gamble option metadata, outcome evaluation, and deterministic die-roll helpers
- Custom controller used? (yes/no): no
- If yes, why PsyFlow-native path is insufficient: not applicable
- Legacy/backward-compatibility fallback logic required? (yes/no): no
- If yes, scope and removal plan: not applicable

## 8. Inference Log

List any inferred decisions not directly specified by references:

- Decision: use 18 trials in a single block
- Why inference was required: the public task manual describes the canonical GDT structure, but the block packaging is not always spelled out in the selected papers
- Citation-supported rationale: the Game of Dice Task is implemented as a fixed explicit-risk gambling sequence in standard task manuals and GDT papers; a single 18-trial block is the common presentation format
- Decision: use keyboard keys `1`-`4` as the primary response mapping in the PsyFlow build
- Why inference was required: the original implementation is click/button based, but the framework needs a deterministic cross-platform response contract
- Citation-supported rationale: the task still presents four discrete gamble options with a single choice per trial, so numeric option keys preserve the selection semantics
- Decision: display the die result as a numeric/face-equivalent reveal rather than a movie-based animation
  - Why inference was required: the browser/PsyFlow implementation needs a lightweight, auditable rendering path
  - Citation-supported rationale: the manual specifies a dice-roll reveal; the exact animation style is an implementation detail
- Decision: skip outcome and feedback screens after a timeout instead of fabricating a roll
  - Why inference was required: the manual allows the participant to stop/omit response, but the browser implementation still needs a clean finite-state path
  - Citation-supported rationale: missed responses do not change the task score, so a neutral skip preserves the analysis contract
- Decision: classify 3- and 4-number options as advantageous/safe choices for summary reporting
  - Why inference was required: the literature emphasizes the lower-risk options, but the exact summary dichotomy is an implementation choice
  - Citation-supported rationale: the 3- and 4-number options have the least risky payoff structure and are commonly grouped as the safer choices in GDT analyses

## Contract Note

- Participant-facing labels/instructions/options should be config-defined whenever possible.
- `src/run_trial.py` should not hardcode participant-facing text that would require code edits for localization.
