# Configuration validation

`configs/experiment.yaml` intentionally keeps `labels.tick_size` null until the
source/venue rule is verified. Loading it therefore fails fast while
`threshold_mode` is `half_tick_over_mid`. Set a verified positive value in a
run-specific copy; do not silently infer it from observed test performance.

