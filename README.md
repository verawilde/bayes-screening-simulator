# Rarity Roulette

Materials, data, and analysis code for An LLM Canary in the Online Data Coalmine: Bayesian Reasoning Problems as a Capability-Gap Test for LLM Contamination in Online Samples (Wilde), and for Rarity Roulette, an interactive tool for teaching Bayesian reasoning about low-prevalence screening (e.g., polygraphs, mammography).

Preregistrations and OSF project: https://osf.io/exaqj

## Data
- pilot2_scored_data.csv — Pilot 2 (Jan 2026), scored, one row per participant. Key columns: condition (control/treatment); in_quality_sample (preregistered 15-min filter); bayes_prop (Bayesian algorithm use, 0–1); accuracy (correct answers, 0–5).
- pilot1_complete_data.csv — Pilot 1 (Dec 2025), complete responses.

## Materials
- "Rarity Roulette pilot 2 survey instrument.pdf" — the instrument, including the five natural-frequency PPV problems.

## Analysis
- analysis/scoring_rubric.py — coding scheme for accuracy and Bayesian algorithm use.

## The tool
- index.html, legacy/, policy/, logo, favicon — the Rarity Roulette web app.

## Reproducing the analyses
Reported estimates use the preregistered quality-filtered subsample (in_quality_sample = TRUE) as primary, with the full sample reported for transparency. Accuracy = mean correct-answer rate across the five PPV problems; Bayesian algorithm use = coded from "show your work" responses.

## Citation
Wilde, V. (2026). An LLM Canary in the Online Data Coalmine: Bayesian Reasoning Problems as a Capability-Gap Test for LLM Contamination in Online Samples. Revised manuscript under review, Behavior Research Methods.

License: see LICENSE (MIT).
