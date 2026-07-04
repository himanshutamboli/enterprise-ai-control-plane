"""Evaluation Engine: score gateway outputs against a dataset.

Pluggable `Evaluator`s (deterministic CI-safe defaults; LLM-judge drop-ins later) run a dataset
through the gateway, score each output, and persist a run with per-item results and aggregate
mean-score / pass-rate. This is what turns "we called a model" into "we know if it's any good".
"""
