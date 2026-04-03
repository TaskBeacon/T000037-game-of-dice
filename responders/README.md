# Responders

`TaskSamplerResponder` is the QA/sim sampler for this task.

Behavior:
- non-rating screens continue with `space` when available
- rating screens choose a numeric key based on `task_factors.condition`
- default condition-to-rating mapping is low=2, medium=4, high=6
- response latency is sampled from the configured RT distribution

