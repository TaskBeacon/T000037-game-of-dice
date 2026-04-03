# CHANGELOG

All notable development changes for `Game of Dice Task` are documented here.

## [0.1.0-dev] - 2026-04-03

### Added
- Replaced the scaffolded risk-rating flow with a canonical Game of Dice choice task.
- Added four explicit-risk gamble options with known probabilities and win/loss magnitudes.
- Added deterministic dice outcome sampling and cumulative capital tracking.
- Added a task-specific sampler responder for QA/sim mode that exercises the choice keys.
- Added mode-specific human, QA, scripted-sim, and sampler-sim YAML configs.
- Added task evidence, stimulus mapping, and updated task audit artifacts for the dice paradigm.

### Changed
- Human instructions now describe the four dice betting options, the starting capital, and the trial sequence.
- The trial pipeline now uses fixation, choice, outcome reveal, feedback, and ITI phases.
- The goodbye screen now summarizes the final capital instead of risk-rating metrics.

### Fixed
- Removed the template risk-perception stimuli, scoring logic, and condition labels.
- Removed scaffold-era controller assumptions that did not match the explicit-risk decision task.
