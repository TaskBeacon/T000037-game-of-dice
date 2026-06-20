# Task Plot Review

## Evidence Match

- Pass: title and construct match the Game of Dice Task.
- Pass: rows match the four configured dice gamble options.
- Pass: phase order matches README and `src/run_trial.py`: Fixation -> Choice screen -> Outcome reveal -> Feedback -> ITI.
- Pass: timing labels match config: 500 ms fixation, 10000 ms choice, 900 ms outcome, 1000 ms feedback, 800 ms ITI.
- Pass: response mapping shows keys 1-4 and option-specific win probabilities/amounts.
- Pass: feedback shows win/loss and updated capital.
- Pass: timeout behavior is documented in the brief without adding an extra phase to the standard valid-response timeline.

## Visual Quality

- Pass: labels and timings are readable.
- Pass: generated timeline content stays below the header band.
- Pass: fixed title and Construct subtitle are centered.
- Pass: top-right TaskBeacon logo lockup is borderless and non-overlapping.
- Pass: no generated title, logo, watermark, people, devices, or decorative scene is present.

## README Embed

- Pass: `README.md` contains `## 2. Task Flow`.
- Pass: the section embeds `![Task Flow](task_flow.png)`.
- Pass: final image is saved as `task_flow.png`; raw timeline is saved as `references/task_plot_timeline_raw.png`.
