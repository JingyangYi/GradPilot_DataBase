#!/usr/bin/env python3
"""
Translate & clean graduate program data from Chinese to English (task step 5).

Usage:
    python translate_program_data.py <input_cleaned_csv> [output_csv] [--sample]

Arguments:
    input_cleaned_csv   Path to the cleaned CSV produced by `clean_program_data.py`.
    output_csv          Optional. If omitted, `_translated.csv` is appended to the input filename.
    --sample            Only process the first 20 rows (for quick testing).

Environment:
    DEEPSEEK_API_KEY    Your DeepSeek API key. Required.

Notes:
    • This script relies on DeepSeek's ChatCompletion-like endpoint. Adapt the `_call_deepseek` function if their
      HTTP interface differs.
    • Each column that requires translation/cleaning has its own function for clarity & testability.
    • A simple in-memory cache avoids repeating identical translation calls in one run.
"""
from __future__ import annotations

import os
import sys
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Tuple, Callable

import pandas as pd
import requests
from tqdm import tqdm  # progress bar

from dotenv import load_dotenv
load_dotenv(os.path.join(Path(__file__).parent, ".env"))

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

###############################################
# DeepSeek Translation backends
###############################################
_API_URL = "https://api.deepseek.com/v1/chat/completions"  # Update if necessary
_MODEL = "deepseek-chat"  # Placeholder – replace with actual model name
_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY', '')}",
}

if not _HEADERS["Authorization"].strip():
    log.warning("DEEPSEEK_API_KEY not set. Script will exit before making API calls.")

_translate_cache: Dict[str, str] = {}

def _call_deepseek(prompt: str) -> str:
    """Call DeepSeek chat completion API with a system-style translation prompt."""
    if prompt.strip() in _translate_cache:
        return _translate_cache[prompt.strip()]

    if not _HEADERS["Authorization"].strip():
        raise RuntimeError("DEEPSEEK_API_KEY environment variable not set.")

    payload: Dict[str, Any] = {
        "model": _MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a professional translator who always translates Chinese to English faithfully "
                    "while preserving factual numbers. Respond with **English only** and no additional commentary."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    response = requests.post(_API_URL, headers=_HEADERS, json=payload, timeout=60)
    try:
        response.raise_for_status()
    except Exception as exc:
        log.error("DeepSeek API error: %s - %s", exc, response.text[:200])
        raise

    data = response.json()
    answer = data["choices"][0]["message"]["content"].strip()
    _translate_cache[prompt.strip()] = answer
    return answer

###############################################
# Gemini (optional)
###############################################

_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
_GEMINI_MODEL = "gemini-2.5-flash"  # User requested model
_GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{_GEMINI_MODEL}:generateContent?key={_GEMINI_API_KEY}"
    if _GEMINI_API_KEY
    else ""
)

def _call_gemini(prompt: str) -> str:
    if prompt.strip() in _translate_cache:
        return _translate_cache[prompt.strip()]
    if not _GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY environment variable not set.")
    combined_prompt = (
        "You are a professional translator who always translates Chinese to English faithfully while preserving factual numbers. "
        "Respond with English only and no additional commentary.\n" + prompt
    )
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": combined_prompt}]
            }
        ],
        "generationConfig": {"temperature": 0.2}
    }
    resp = requests.post(_GEMINI_URL, json=payload, timeout=60)
    if resp.status_code != 200:
        log.error("Gemini API error %s: %s", resp.status_code, resp.text[:300])
        resp.raise_for_status()
    data = resp.json()
    try:
        candidate = data["candidates"][0]
        content = candidate.get("content", {})
        text = ""
        # content may be dict with parts list, or directly text string
        if isinstance(content, dict):
            if "parts" in content and content["parts"]:
                text = " ".join(part.get("text", "") for part in content["parts"])
            else:
                text = content.get("text", "")
        elif isinstance(content, str):
            text = content
        else:
            text = str(content)
        answer = text.strip()
    except Exception as exc:
        log.error("Unexpected Gemini response format: %s", data)
        raise RuntimeError("Gemini response parsing failed") from exc

    _translate_cache[prompt.strip()] = answer
    return answer


# Placeholder; will be set in main() when backend resolved
_translate_func: Callable[[str], str] | None = None

def translate_text(chinese_text: str, context: str | None = None) -> str:
    """Wrapper that calls the selected backend."""
    text = chinese_text.strip()
    if not text:
        return ""
    prompt = text if context is None else f"Context: {context}\nText: {text}"
    if _translate_func is None:
        raise RuntimeError("Translation backend not initialised. Call main() first.")
    return _translate_func(prompt)

###############################################
# Column-specific cleaning / translation
###############################################
_TERM_MAP = {
    "秋": "Fall",
    "春": "Spring",
    "夏": "Summer",
    "冬": "Winter",
    "fall": "Fall",
    "spring": "Spring",
    "summer": "Summer",
    "winter": "Winter",
}

_DEADLINE_DATE_RE = re.compile(r"(\d{1,2})[\-/月](\d{1,2})(?:日)?", re.I)
_ROLLING_PAT = re.compile(r"rolling|滚动", re.I)

def program_detail(text: str) -> str:
    return translate_text(text, "Graduate program description, keep academic terminology accurate.")

def program_length(text: str) -> str:
    # Typically like "2 年" -> "2 years".
    return translate_text(text, "Program length, respond with concise duration such as '2 years'.")

def terms_start(text: str) -> str:
    t = text.strip()
    if not t:
        return ""
    # Map simple Chinese keywords first.
    for cn, en in _TERM_MAP.items():
        if cn.lower() in t.lower():
            return en
    # Fallback to translation.
    trans = translate_text(t, "Academic term when program starts (Fall / Spring / Summer / Winter)")
    # Normalise output.
    return _TERM_MAP.get(trans.lower(), trans)

def deadline(text: str) -> Tuple[str, str]:
    """Return (clean_deadline, info_append) using DeepSeek-only logic.

    DeepSeek prompt rules:
    • If a definite date is present, DeepSeek should respond with the date in MM-DD format (e.g., 12-15).
    • Otherwise DeepSeek should translate the deadline info and we will store it in more_info prefixed with
      "More info about deadline.".
    """
    t = text.strip()
    if not t:
        return "", ""

    prompt = (
        "You are assisting with graduate application data cleaning. The user will give you Chinese text that describes "
        "an application deadline. If the text clearly contains a specific date, respond with only that date in MM-DD "
        "format (two-digit month dash two-digit day, no year). If the deadline is rolling admission, respond exactly with "
        "'rolling'. If there is no exact date and it is not rolling, respond with 'INFO:' followed by an accurate English "
        "translation of the deadline description. Respond in one line only.\n" + t
    )
    answer = _translate_func(prompt).strip()

    if answer.lower().strip() == "rolling":
        return "rolling", ""

    if answer.upper().startswith("INFO:"):
        info_text = answer[len("INFO:"):].strip()
        return "", f"More info about deadline. {info_text}"

    # Basic sanity for MM-DD pattern
    if re.fullmatch(r"\d{2}-\d{2}", answer):
        return answer, ""

    # Fallback: treat entire answer as info.
    return "", f"More info about deadline. {answer}"

def gpa_req(text: str) -> Tuple[str, str]:
    """Return (min_gpa, info_append).

    Behaviour:
    • If text contains an explicit minimum GPA (e.g. 3.0 / 4.0), return that number.
    • If text seems to describe *average* GPA or is otherwise unclear, leave min_gpa empty and
      return an English translation in info_append so analysts can review later.
    • DeepSeek is used to classify ambiguous cases and translate when necessary.
    """
    t = text.strip()
    if not t:
        return "", ""

    # Fast-path: extract first numeric GPA (0-4.0) if present and not labelled as average.
    simple_num = re.search(r"([0-3](?:\.\d{1,2})?|4(?:\.0)?)", t)
    if simple_num and ("均" not in t and "avg" not in t.lower()):
        return simple_num.group(1), ""

    # Otherwise ask DeepSeek to decide.
    ds_prompt = (
        "The following Chinese text describes GPA requirements for graduate admissions. "
        "If it specifies a *minimum* GPA, respond with only that number (e.g. 3.0). "
        "If it instead talks about *average* GPA, respond with '- GPA_AVERAGE:' "
        "followed by an accurate English translation. otherwise reply with no specific requirement"
        "Respond in one line only.\n" + t
    )
    answer = _translate_func(ds_prompt)
    answer = answer.strip()
    if answer.upper().startswith("- GPA_AVERAGE:"):
        return "", answer  # keep full average description in note
    num_match = re.search(r"([0-3](?:\.\d{1,2})?|4(?:\.0)?)", answer)
    if num_match:
        return num_match.group(1), ""
    # Fallback: treat as translation note.
    return "", ""

def simple_translate(text: str, field: str) -> str:
    """Legacy single-item translator kept for fallback and unit tests."""
    return translate_text(text, f"Translate {field} requirement to English.")


def batch_translate_column(series: pd.Series, field: str) -> pd.Series:
    """Translate an entire column in batches rather than cell-by-cell.

    The function sends up to `BATCH_SIZE` unique Chinese strings in one prompt and
    expects the backend to return English translations *line-by-line in the same order*.
    This greatly reduces the number of API calls (≈ one per column) while keeping
    behaviour deterministic.
    """
    BATCH_SIZE = 50  # Conservative to avoid hitting prompt length limits
    unique_vals = series.astype(str).unique().tolist()

    translation_map: Dict[str, str] = {}

    for i in range(0, len(unique_vals), BATCH_SIZE):
        chunk = unique_vals[i : i + BATCH_SIZE]
        # Skip entirely empty strings – they stay empty and we don't waste tokens.
        clean_chunk = [v for v in chunk if v.strip()]
        if not clean_chunk:
            continue

        joined = "\n".join(clean_chunk)
        context = (
            f"Translate each line of the following {field} values from Chinese to English. "
            "Preserve any numbers. Respond with the translations line-by-line in the same order with NO extra commentary."
        )
        answer = translate_text(joined, context)
        lines = [l.strip() for l in answer.splitlines() if l.strip()]

        if len(lines) != len(clean_chunk):
            # Fallback to per-item translation if backend response is unexpected.
            log.warning(
                "Batch translation mismatch on column %s (expected %d lines, got %d). Falling back to per-value calls.",
                field,
                len(clean_chunk),
                len(lines),
            )
            for val in chunk:
                translation_map[val] = simple_translate(val, field)
            continue

        # Map back translations.
        for original, translated in zip(clean_chunk, lines):
            translation_map[original] = translated
        # Ensure empty strings remain empty.
        translation_map[""] = ""

    # Apply mapping; unseen values stay as-is (shouldn't happen but safe).
    return series.map(lambda x: translation_map.get(str(x), str(x)))

def interview(text: str, degree_detail: str) -> str:
    # For PhD programs mark as Optional regardless of other text.
    dd_lower = degree_detail.lower()
    if "phd" in dd_lower or "ph.d" in dd_lower:
        return "Optional"
    t = text.strip()
    if not t:
        return "Not needed"
    trans = translate_text(t, "Interview requirement: choose one of Required / Optional / Not needed")
    # Normalise to three options.
    for opt in ("Required", "Optional", "Not needed"):
        if opt.lower() in trans.lower():
            return opt
    return "Unknown"

def application_fee_waiver(text: str) -> str:
    t = text.strip()
    if not t:
        return "Unknown"
    trans = translate_text(t, "Application fee waiver availability: Applicable / Not Applicable / Unknown")
    for opt in ("Applicable", "Not Applicable", "Unknown"):
        if opt.lower() in trans.lower():
            return opt
    return "Unknown"

_RE_NUM = re.compile(r"\d+")

###############################################
# Fee validation
###############################################

def application_fee_usd(text: str) -> Tuple[str, str]:
    """Validate and normalise `application_fee_usd`.

    Accepted inputs examples:
        100            -> 100
        100.00         -> 100.00
        $100           -> 100
        USD 120        -> 120
        费用100美元      -> 100 (note: first numeric sequence)
    Returns (numeric_string, warn_msg).
    """
    t = text.strip()
    if not t:
        return "", ""

    # Remove common currency tokens, commas, whitespace.
    cleaned = re.sub(r"[,$€£¥]|usd|USD", "", t).strip()

    if re.fullmatch(r"\d+(?:\.\d+)?", cleaned):
        return cleaned.lstrip("0") or "0", ""

    # Fallback: extract first number anywhere in original text.
    m = re.search(r"\d+(?:\.\d+)?", t)
    if m:
        extracted = m.group(0).lstrip("0") or "0"
        log.warning("application_fee_usd cleaned: '%s' -> '%s'", t, extracted)
        return extracted, f"Original application_fee_usd value corrected from '{t}'."

    # Not parsable.
    log.warning("application_fee_usd invalid: '%s'", t)
    return "", f"Invalid application_fee_usd value: {t}"

def recommendation_letters(text: str) -> str:
    nums = _RE_NUM.findall(text)
    if nums:
        return nums[0]
    if not text.strip():
        return "no explicit demand"
    trans = translate_text(text, "Number of recommendation letters required")
    nums = _RE_NUM.findall(trans)
    return nums[0] if nums else "no explicit demand"

def tags(text: str) -> str:
    return "" if "需要额外确认" in text else text.strip()

def professional_program(text: str) -> str:
    mapping = {
        "职业": "Professional",
        "专业": "Professional",
        "非职业": "Non-Professional",
        "未知": "Unknown",
    }
    for k, v in mapping.items():
        if k in text:
            return v
    # Translate then map.
    trans = translate_text(text, "Program type: Professional / Non-Professional / Unknown")
    for opt in ("Professional", "Non-Professional", "Unknown"):
        if opt.lower() in trans.lower():
            return opt
    return "Unknown"

###############################################
# Main pipeline
###############################################

def process_row(row: pd.Series) -> pd.Series:
    # program_detail
    row["program_detail"] = program_detail(row.get("program_detail", ""))
    row["program_length"] = program_length(row.get("program_length", ""))
    row["terms_start"] = terms_start(row.get("terms_start", ""))

    # deadline & more_info augment
    new_deadline, info_append = deadline(row.get("deadline", ""))
    row["deadline"] = new_deadline
    if info_append:
        row["more_info"] = (row.get("more_info", "") + "\n" if row.get("more_info", "") else "") + info_append

    gpa, gpa_info = gpa_req(row.get("gpa_req", ""))
    row["gpa_req"] = gpa
    if gpa_info:
        row["more_info"] = (row.get("more_info", "") + "\n" if row.get("more_info", "") else "") + gpa_info

    # application_fee_usd validation
    fee_val, fee_note = application_fee_usd(row.get("application_fee_usd", ""))
    row["application_fee_usd"] = fee_val
    if fee_note:
        row["more_info"] = (row.get("more_info", "") + "\n" if row.get("more_info", "") else "") + fee_note

    # NOTE: simple translate fields are now handled in batch after row processing

    row["interview"] = interview(row.get("interview", ""), row.get("degree_detail", ""))
    row["application_fee_waiver"] = application_fee_waiver(row.get("application_fee_waiver", ""))
    row["recommendation_letters"] = recommendation_letters(row.get("recommendation_letters", ""))
    row["tags"] = tags(row.get("tags", ""))
    row["professional_program"] = professional_program(row.get("professional_program", ""))
    return row


def main():
    if len(sys.argv) < 2:
        print("Usage: python translate_program_data.py <input_cleaned_csv> [output_csv] [--sample] [--backend deepseek|gemini]", file=sys.stderr)
        sys.exit(1)

    # Flags
    sample = False
    backend = "deepseek"
    if "--sample" in sys.argv:
        sample = True
        sys.argv.remove("--sample")
    if "--backend" in sys.argv:
        idx = sys.argv.index("--backend")
        backend = sys.argv[idx + 1]
        del sys.argv[idx:idx + 2]

    # Select backend
    global _translate_func
    if backend == "deepseek":
        _translate_func = _call_deepseek
    elif backend == "gemini":
        _translate_func = _call_gemini
    else:
        print(f"Unsupported backend {backend}. Choose 'deepseek' or 'gemini'.", file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1]).expanduser()
    if not input_path.exists():
        print(f"Input file {input_path} not found", file=sys.stderr)
        sys.exit(1)
    output_path = Path(sys.argv[2]).expanduser() if len(sys.argv) >= 3 else input_path.with_name(input_path.stem + "_translated.csv")

    df = pd.read_csv(input_path, dtype=str, keep_default_na=False)
    if sample:
        df = df.head(50)
        log.info("Processing first 20 rows only (--sample)")

    # Progress bar
    rows = []
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Translating"):
        rows.append(process_row(row))
    df = pd.DataFrame(rows)

    # -----------------------------------------------
    # Batch translate simple columns once per column
    # -----------------------------------------------
    simple_cols = ["toefl_req", "ielts_req", "gre_req", "gmat_req", "academic_background"]

    for col in simple_cols:
        if col not in df.columns:
            continue
        df[col] = batch_translate_column(df[col], col)

    df.to_csv(output_path, index=False)
    log.info("Translated CSV saved to %s", output_path)

    # Optionally, save translation cache for reuse/debugging.
    cache_path = output_path.with_suffix(".cache.json")
    with open(cache_path, "w", encoding="utf-8") as fh:
        json.dump(_translate_cache, fh, ensure_ascii=False, indent=2)
    log.info("Translation cache saved to %s", cache_path)


if __name__ == "__main__":
    main()
