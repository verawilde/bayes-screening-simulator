"""
Rarity Roulette Pilot Studies: Scoring Rubric & Code
=====================================================
Author: Vera Wilde
Repository: https://github.com/verawilde/rarity-roulette
OSF: https://osf.io/exaqj

This script scores both pilot studies' test problem responses and
reproduces the values reported in the manuscript.

Pilots 1 and 2 used the same 5 test problems but different SoSci Survey
data structures:
  - Pilot 1: Free-text responses in columns TP01s-TP05s (participants typed
    their answer AND showed their work in a single text field)
  - Pilot 2: Structured responses with separate numeric answer fields
    (TP01_01-TP05_01) and Bayesian algorithm coding (BN01-BN03 for 3 of 5
    problems; TP01s-TP05s for show-your-work free text)

Two outcome variables are scored:
  1. ACCURACY: Did the participant give the correct numerical answer?
  2. BAYESIAN ALGORITHM USE: Did the participant use a Bayesian algorithm
     (i.e., identify the correct denominator as true positives + false
     positives)?

Correct answers for each test problem:
  TP01 (Mammography):        5 out of 105    (PPV = 4.76%)
  TP02 (CSAM detection):     8 out of 1007   (PPV = 0.79%)
  TP03 (Prenatal screening): 9 out of 359    (PPV = 2.51%)
  TP04 (Plagiarism):        80 out of 1070   (PPV = 7.48%)
  TP05 (Hate speech):      160 out of 5150   (PPV = 3.11%)

CORRECTION NOTE (August 2026)
-----------------------------
An earlier version of code_bayesian_algorithm() contained an error in the
first entry of its indicator list, written as:

    'adding' and ('positive' in text or 'true' in text or 'false' in text)

Python evaluates a non-empty string as truthy, so this expression reduces to
its right-hand side and the word "adding" was never tested. The indicator
therefore fired on any response containing "positive", "true", or "false",
making the coder substantially more permissive than intended. The line is
corrected below. Accuracy scoring is unaffected: it requires an exact match
on both numerator and denominator.

Pilot 1 analysis sample
-----------------------
The Pilot 1 analysis sample (N = 76) is defined as FINISHED == 1 AND
STARTED >= 2025-12-01 13:40, the Prolific launch time. Responses before
that timestamp are pretests and are retained in the raw file but flagged
out via the in_analysis_sample column produced by score_pilot1().
"""

import re
import numpy as np
import pandas as pd


# ============================================================
# CORRECT ANSWERS
# ============================================================

CORRECT_ANSWERS = {
    'TP01': {'numerator': 5,   'denominator': 105,  'ppv_pct': 5/105*100},
    'TP02': {'numerator': 8,   'denominator': 1007, 'ppv_pct': 8/1007*100},
    'TP03': {'numerator': 9,   'denominator': 359,  'ppv_pct': 9/359*100},
    'TP04': {'numerator': 80,  'denominator': 1070, 'ppv_pct': 80/1070*100},
    'TP05': {'numerator': 160, 'denominator': 5150, 'ppv_pct': 160/5150*100},
}

# Prolific launch timestamp for Pilot 1; earlier responses are pretests.
PILOT1_LAUNCH = pd.Timestamp('2025-12-01 13:40:00')


# ============================================================
# ACCURACY SCORING
# ============================================================

def extract_fraction(text):
    """Extract 'X out of Y' or 'X/Y' from free-text response.

    Returns (numerator, denominator) or (None, None) if not found.
    """
    if pd.isna(text) or len(str(text).strip()) < 2:
        return None, None
    text = str(text).replace(',', '')

    match = re.search(r'(\d+)\s*(?:out of|/|:)\s*(\d+)', text)
    if match:
        return int(match.group(1)), int(match.group(2))

    numbers = re.findall(r'\d+', text)
    if len(numbers) >= 2:
        return int(numbers[0]), int(numbers[1])

    return None, None


def score_accuracy(text, problem_key):
    """Score accuracy: 1 if exact numerator and denominator, 0 otherwise."""
    correct = CORRECT_ANSWERS[problem_key]
    num, denom = extract_fraction(text)
    if num == correct['numerator'] and denom == correct['denominator']:
        return 1
    return 0


def score_accuracy_ppv(text, problem_key, tolerance_pct=0.5):
    """Alternative scoring by PPV percentage within tolerance_pct."""
    correct = CORRECT_ANSWERS[problem_key]
    num, denom = extract_fraction(text)
    if num is not None and denom is not None and denom > 0:
        if abs(num / denom * 100 - correct['ppv_pct']) < tolerance_pct:
            return 1
    return 0


# ============================================================
# BAYESIAN ALGORITHM CODING
# ============================================================

def code_bayesian_algorithm(text):
    """Code whether the participant used a Bayesian algorithm.

    A Bayesian algorithm is defined as identifying the correct denominator
    as the sum of true positives and false positives (all positive test
    results), rather than the total population or another incorrect
    denominator.

    Returns 1 (Bayesian) or 0 (non-Bayesian or uncodeable).

    This coder is automated and keyword-based. It is permissive relative to
    a human coder: it detects the vocabulary and arithmetic of the Bayesian
    algorithm rather than verifying that the algorithm was applied
    correctly. Rates produced here are therefore upper bounds.
    """
    if pd.isna(text) or len(str(text).strip()) < 5:
        return 0

    text = str(text).lower()

    bayesian_indicators = [
        # CORRECTED: previously written as `'adding' and (...)`, which Python
        # evaluated as just `(...)`, so "adding" was never actually tested.
        'adding' in text and ('positive' in text or 'true' in text or 'false' in text),
        'true positive' in text and 'false positive' in text,
        'added' in text and 'positive' in text,
        'sum' in text and 'positive' in text,
        'total' in text and 'positive' in text and ('test' in text or 'flagged' in text),
        'denominator' in text,
        'numerator' in text,
        '+ ' in text and ('100' in text or 'false' in text),
        'plus' in text and ('false' in text or 'positive' in text),
    ]

    pattern_matches = [
        re.search(r'add(ed|ing)?.*(true|false|positive)', text),
        re.search(r'(true|false).*(positive|negative).*add', text),
        re.search(r'\d+\s*\+\s*\d+', text),
        re.search(r'(true positive|tp).*\+.*(false positive|fp)', text),
        re.search(r'adding the (true|false|positive)', text),
    ]

    if any(bayesian_indicators) or any(pattern_matches):
        return 1
    return 0


# ============================================================
# PILOT 1 SCORING (free-text only)
# ============================================================

def score_pilot1(df):
    """Score Pilot 1 data.

    Expects columns: TP01s-TP05s (free-text show-your-work responses),
    IV01_01 (condition: 1=control, 2=treatment), TIME_SUM (seconds),
    FINISHED, STARTED.

    Adds in_analysis_sample: FINISHED == 1 and STARTED >= PILOT1_LAUNCH.
    Responses before launch are pretests, retained but flagged out.
    """
    df = df.copy()
    df['STARTED'] = pd.to_datetime(df['STARTED'], errors='coerce')

    for tp_key in CORRECT_ANSWERS:
        col = f'{tp_key}s'
        if col in df.columns:
            df[f'{tp_key}_correct'] = df[col].apply(
                lambda x: score_accuracy(x, tp_key))
            df[f'{tp_key}_bayes'] = df[col].apply(code_bayesian_algorithm)

    correct_cols = [f'{tp}_correct' for tp in CORRECT_ANSWERS if f'{tp}_correct' in df.columns]
    bayes_cols = [f'{tp}_bayes' for tp in CORRECT_ANSWERS if f'{tp}_bayes' in df.columns]

    df['accuracy'] = df[correct_cols].sum(axis=1)          # out of 5
    df['bayes_prop'] = df[bayes_cols].mean(axis=1)         # 0 to 1
    df['time_minutes'] = df['TIME_SUM'] / 60
    df['condition'] = df['IV01_01'].map({1: 'control', 2: 'treatment'})
    df['in_analysis_sample'] = (df['FINISHED'] == 1) & (df['STARTED'] >= PILOT1_LAUNCH)
    df['in_quality_sample'] = df['in_analysis_sample'] & (df['time_minutes'] >= 15)

    return df


# ============================================================
# PILOT 2 SCORING (structured + free-text)
# ============================================================

def score_pilot2(df):
    """Score Pilot 2 data.

    Expects columns: TP01_01-TP05_01 (structured answer fields),
    BN01-BN03 (Bayesian algorithm coding for 3 problems),
    TP01s-TP05s (free-text), IV01_01 (condition), TIME_SUM (seconds).
    """
    df = df.copy()

    for tp_key in CORRECT_ANSWERS:
        col = f'{tp_key}_01'
        if col in df.columns:
            df[f'{tp_key}_correct'] = df[col].apply(
                lambda x: score_accuracy(x, tp_key))

    bayes_cols = []
    for bn_col in ['BN01', 'BN02', 'BN03']:
        if bn_col in df.columns:
            df[f'{bn_col}_bayes'] = (df[bn_col] == 1).astype(int)
            bayes_cols.append(f'{bn_col}_bayes')

    for tp_key in CORRECT_ANSWERS:
        col = f'{tp_key}s'
        if col in df.columns and f'{tp_key}_bayes' not in df.columns:
            df[f'{tp_key}_bayes'] = df[col].apply(code_bayesian_algorithm)
            if f'{tp_key}_bayes' not in bayes_cols:
                bayes_cols.append(f'{tp_key}_bayes')

    correct_cols = [f'{tp}_correct' for tp in CORRECT_ANSWERS if f'{tp}_correct' in df.columns]

    df['accuracy'] = df[correct_cols].sum(axis=1)
    df['bayes_prop'] = df[bayes_cols].mean(axis=1) if bayes_cols else np.nan
    df['time_minutes'] = df['TIME_SUM'] / 60
    df['condition'] = df['IV01_01'].map({1: 'control', 2: 'treatment'})

    if 'TP06s' in df.columns:
        df['attn_pass'] = df['TP06s'].str.lower().str.strip() == 'banana'

    return df


# ============================================================
# PREREGISTERED EXCLUSION CRITERIA
# ============================================================

def apply_exclusions_pilot2(df):
    """Apply Pilot 2 preregistered exclusion criteria.

    Preregistered on OSF:
    1. Failed 1+ attention checks (TP06s != 'banana')
    2. Self-reported non-genuine effort (SC04 == 2 or SC05 == 2)
    3. Self-reported severe distraction

    Quality-filtered subsample: time_minutes >= 15 (preregistered)

    Note: Pilot 1 did NOT preregister a time cutoff.
    Any time-based filtering on Pilot 1 is post-hoc/exploratory.
    """
    excluded = pd.Series(False, index=df.index)

    if 'attn_pass' in df.columns:
        excluded |= ~df['attn_pass']
    if 'SC04' in df.columns:
        excluded |= (df['SC04'] == 2)
    if 'SC05' in df.columns:
        excluded |= (df['SC05'] == 2)

    full_sample = df[~excluded].copy()
    quality_sample = full_sample[full_sample['time_minutes'] >= 15].copy()

    return full_sample, quality_sample


# ============================================================
# INTERVALS AND EFFECT SIZES
# ============================================================

def compatibility_interval(x, conf=0.95):
    """Participant-level compatibility interval for a mean proportion.

    Computed across participants rather than by pooling items, because
    responses within a participant are strongly dependent.
    """
    from scipy import stats
    x = np.asarray(x, dtype=float)
    n = len(x)
    m = x.mean()
    t = stats.t.ppf(1 - (1 - conf) / 2, n - 1)
    se = x.std(ddof=1) / np.sqrt(n)
    return m, max(0.0, m - t * se), min(1.0, m + t * se)


def compute_effect_size(df, dv, label=""):
    """Treatment-control difference with Cohen's d and 95% interval."""
    from scipy import stats

    control = df[df['condition'] == 'control'][dv].dropna()
    treatment = df[df['condition'] == 'treatment'][dv].dropna()

    mean_diff = treatment.mean() - control.mean()
    pooled_std = np.sqrt(
        ((len(control) - 1) * control.std(ddof=1) ** 2 +
         (len(treatment) - 1) * treatment.std(ddof=1) ** 2) /
        (len(control) + len(treatment) - 2))

    d = mean_diff / pooled_std if pooled_std > 0 else 0
    se_d = np.sqrt((len(control) + len(treatment)) / (len(control) * len(treatment)) +
                   d ** 2 / (2 * (len(control) + len(treatment))))
    t_crit = stats.t.ppf(0.975, len(control) + len(treatment) - 2)

    print(f"\n{label}")
    print(f"  Control:   M={control.mean():.3f}, SD={control.std(ddof=1):.3f}, n={len(control)}")
    print(f"  Treatment: M={treatment.mean():.3f}, SD={treatment.std(ddof=1):.3f}, n={len(treatment)}")
    print(f"  Cohen's d: {d:+.3f} (95% CI: {d - t_crit * se_d:+.3f} to {d + t_crit * se_d:+.3f})")

    return {'d': d, 'ci_lo': d - t_crit * se_d, 'ci_hi': d + t_crit * se_d,
            'mean_diff': mean_diff, 'n_control': len(control), 'n_treatment': len(treatment)}


if __name__ == '__main__':
    p1 = score_pilot1(pd.read_csv('pilot1_complete_data.csv'))
    s = p1[p1.in_analysis_sample]
    print(f"Pilot 1 analysis sample: N = {len(s)}")
    print(s.groupby('condition')[['accuracy', 'bayes_prop']].agg(['size', 'mean']))
    for cond, g in s.groupby('condition'):
        m, lo, hi = compatibility_interval(g.accuracy / 5)
        print(f"  accuracy  {cond:10s} {m*100:.1f}% [{lo*100:.0f}, {hi*100:.0f}]")
        m, lo, hi = compatibility_interval(g.bayes_prop)
        print(f"  algorithm {cond:10s} {m*100:.1f}% [{lo*100:.0f}, {hi*100:.0f}]")
