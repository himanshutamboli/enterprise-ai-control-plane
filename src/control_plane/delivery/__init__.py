"""AI Delivery Manager: TPM-native delivery tracking with an explainable risk signal.

Projects hold work items and a RAID log (Risks / Assumptions / Issues / Dependencies). The module
computes project health and a **delivery-risk score** from a transparent, deterministic heuristic
(no black box — every point of risk has a stated reason), and generates an AI status report
through the gateway (metered + traced).
"""
