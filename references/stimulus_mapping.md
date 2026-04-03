# Stimulus Mapping

## Mapping Table

| Condition | Stage/Phase | Stimulus IDs | Participant-Facing Content | Source Paper ID | Evidence (quote/figure/table) | Implementation Mode | Asset References | Notes |
|---|---|---|---|---|---|---|---|---|
| `gdt_standard` | `instruction` | `instruction_text` | Chinese instructions explaining the 18-round dice gambling task, the four risk levels, and the goal of maximizing total points | `W2161561914` | Standard explicit-risk GDT description; PST task page notes the four payoff levels and dice-roll reveal | `psychopy_builtin` | `n/a` | Written entirely in config for auditability |
| `gdt_standard` | `choice_screen` | `capital_banner`, `choice_prompt`, `option_1`, `option_2`, `option_3`, `option_4` | Current total points plus four gamble cards: 1/6, 2/6, 3/6, 4/6 payoff ladders with 1000/500/200/100 point magnitudes | `W2128601759` | Explicit-risk gamble ladder used in standard Game of Dice implementations; payoffs and probabilities follow the published task manual | `psychopy_builtin` | `n/a` | Four-card horizontal row with stable left-to-right risk order; timeout branches directly to ITI |
| `gdt_standard` | `outcome_reveal` | `outcome_text` | Revealed die result as a numeric roll (1-6) | `W2901004383` | Dice-roll outcome is the central feedback event in the explicit-risk task; numeric reveal is an implementation choice | `psychopy_builtin` | `n/a` | Mirrors the dice-roll movie with a lightweight numeric reveal |
| `gdt_standard` | `feedback` | `feedback_win`, `feedback_loss`, `capital_banner` | Win/loss message plus updated total points | `W1999635028` | Risk/decision tasks in Parkinsonian samples report trial-wise outcome feedback and cumulative score updates | `psychopy_builtin` | `n/a` | The feedback text is formatted from runtime outcome values; shown only after a valid choice |
| `gdt_standard` | `end` | `end_summary` | Final total points after all 18 rounds | `W2161561914` | End-of-task cumulative decision outcome summary; consistent with the task’s score-based design | `psychopy_builtin` | `n/a` | Final summary screen only, no extra stimuli |

Accepted implementation modes:

- `psychopy_builtin`
- `generated_reference_asset`
- `licensed_external_asset`

Decision rule:

- Participant-facing text should be defined in `config/*.yaml` stimuli and referenced by stimulus IDs.
