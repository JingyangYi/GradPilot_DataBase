#!/usr/bin/env python3
"""
Clean program data CSV according to task_program_data_clean.md steps 1-4.

Usage:
    python clean_program_data.py <input_csv_path> [output_csv_path]

If output path is omitted, `_cleaned.csv` is appended to the input filename.
"""

import re
import sys
from pathlib import Path
from typing import List
import pandas as pd
import logging
import json
logging.basicConfig(level=logging.WARNING)

UNHANDLED_ROWS: List[dict] = []

# Mapping of Chinese column headers to desired English headers (manual)
COLUMN_HEADER_MAP = {
    "大学排名": "univ_rank",
    "大学英文名称": "univ_name",
    "所在城市": "city",
    "专业英文名称": "program_name",
    "学位": "degree_detail",
    "所属院系英文名称": "department",
    "所属院系网址": "department_url",
    "专业领域": "program_detail",
    "课程长度": "program_length",
    "申请费（美元)": "application_fee_usd",
    "申请费减免": "application_fee_waiver",
    "开学期": "terms_start",
    "截止日期": "deadline",
    "GPA": "gpa_req",
    "托福": "toefl_req",
    "雅思": "ielts_req",
    "GRE": "gre_req",
    "GMAT": "gmat_req",
    "托福送分ETS code": "ets_code",
    "推荐信": "recommendation_letters",
    "学术背景": "academic_background",
    "材料要求": "material_requirements",
    "招生网址": "admission_url",
    "专业网址": "program_url",
    "课程网址": "course_url",
    "面试newp": "interview",
    "更多项目信息": "more_info",
    "项目标签（英文)": "tags",
    "项目标签（英文）": "tags",  # full-width right paren
    "职业项目": "professional_program",
    "Gemini最终毕业要求": "grad_requirement",
}

# Columns that have English duplicates; if these exist we discard the CN version
DUPLICATE_DISCARD_PAIRS = {
    "大学名称": "大学英文名称",
    "专业中文名称": "专业英文名称",
    "所属院系": "所属院系英文名称",
    "项目标签（中文)": "项目标签（英文)",
    "项目标签（中文）": "项目标签（英文）",  # both variants
}


TERM_SPLIT_REGEX = re.compile(r"[、，；,;]+")
DATE_SPLIT_REGEX = re.compile(r"[、，；,;]+")


def split_terms_and_deadlines(df: pd.DataFrame) -> pd.DataFrame:
    """Step 2 logic (terms splitting).

    Rules:
    1. If there are multiple terms and the number of deadlines matches exactly, split rows pair-wise.
    2. If there are multiple terms but deadlines do NOT match in count, just split by terms (keep the original deadline string as-is).
    3. If there is only one term, leave the row unchanged.
    After this function, `process_deadlines` will further handle multiple deadlines per row."""
    # Removed stray bullet lines with unicode and commented out accordingly
    # • If multiples of terms and deadlines are equal, split one-to-one.
    # • If multiple terms, single deadline – duplicate deadline for each term.
    # • If single term, multiple deadlines – keep first, move others to more_info.
    rows: List[pd.Series] = []
    for _, row in df.iterrows():
        terms = [t.strip() for t in TERM_SPLIT_REGEX.split(str(row.get("terms_start", ""))) if t.strip()]
        dls   = [d.strip() for d in DATE_SPLIT_REGEX.split(str(row.get("deadline", ""))) if d.strip()]

        # Case 1: pair-wise split when counts match (>1)
        if len(terms) > 1 and len(terms) == len(dls):
            for term, dl in zip(terms, dls):
                new_row = row.copy()
                new_row["terms_start"] = term
                new_row["deadline"] = dl
                rows.append(new_row)
            continue

        # Case 2: multiple terms but count mismatch – split by term only
        if len(terms) > 1:
            for term in terms:
                new_row = row.copy()
                new_row["terms_start"] = term
                rows.append(new_row)
            continue

        # Case 3: single term – keep as-is
        rows.append(row)

    return pd.DataFrame(rows)


def split_terms(df: pd.DataFrame) -> pd.DataFrame:
    """Step 2: split multiple terms in 开学期 into separate rows."""
    rows: List[pd.Series] = []
    for _, row in df.iterrows():
        terms = [t.strip() for t in TERM_SPLIT_REGEX.split(str(row.get("terms_start", ""))) if t.strip()]
        if not terms:
            rows.append(row)
            continue
        for term in terms:
            new_row = row.copy()
            new_row["terms_start"] = term
            rows.append(new_row)
    return pd.DataFrame(rows)


def process_deadlines(df: pd.DataFrame) -> pd.DataFrame:
    """Step 3: keep first deadline, append others to more_info column.

    We avoid using .at on potentially non-unique indexes by processing row-wise with apply.
    """
    if "deadline" not in df.columns:
        return df

    def _handle_row(row: pd.Series) -> pd.Series:
        deadline_val = str(row.get("deadline", ""))
        parts = [p.strip() for p in DATE_SPLIT_REGEX.split(deadline_val) if p.strip()]
        if len(parts) > 1:
            row["deadline"] = parts[0]
            extra = "- Additional deadlines: " + "; ".join(parts[1:])
            existing = str(row.get("more_info", ""))
            row["more_info"] = (existing + "\n" if existing else "") + extra
        return row

    return df.apply(_handle_row, axis=1)


def clean_ets_code(df: pd.DataFrame):
    """Step 4: clear ETS code if not 4 digit numeric."""
    for idx, code in df["ets_code"].items():
        if pd.isna(code):
            continue
        code_str = str(code).strip()
        if not (code_str.isdigit() and len(code_str) == 4):
            df.at[idx, "ets_code"] = ""


def main():
    # Extract optional debug flag
    debug = False
    if "--debug" in sys.argv:
        debug = True
        sys.argv.remove("--debug")

    if len(sys.argv) < 2:
        print("Usage: python clean_program_data.py <input_csv_path> [output_csv_path] [--debug]")
        sys.exit(1)
    input_path = Path(sys.argv[1]).expanduser()
    if not input_path.exists():
        print(f"Input file {input_path} not found", file=sys.stderr)
        sys.exit(1)
    output_path = Path(sys.argv[2]).expanduser() if len(sys.argv) >= 3 else input_path.with_name(input_path.stem + "_cleaned.csv")

    # Read CSV with pandas, allow multiline fields
    df = pd.read_csv(input_path, dtype=str, keep_default_na=False, engine="python")

    # Step1: retain/translate English info
    # Drop duplicate CN columns if EN counterpart exists
    for cn, en in DUPLICATE_DISCARD_PAIRS.items():
        if cn in df.columns and en in df.columns:
            df.drop(columns=[cn], inplace=True)
    # Rename columns per map
    rename_map = {cn: en for cn, en in COLUMN_HEADER_MAP.items() if cn in df.columns}
    df.rename(columns=rename_map, inplace=True)

    if debug:
        print("\n=== After Step 1: Drop duplicates & rename ===")
        print("Columns:", df.columns.tolist())
        print(df.head())
        intermediate_path = output_path.with_name(output_path.stem + "_step1.csv")
        df.to_csv(intermediate_path, index=False)
        print(f"Intermediate CSV saved to {intermediate_path}")
        return

    # Ensure required columns exist
    for col in ["more_info", "ets_code"]:
        if col not in df.columns:
            df[col] = ""

    # Step2: split terms (may duplicate rows)
    df = split_terms_and_deadlines(df)

    # Step3: process deadlines (handle multiple deadlines per row)
    df = process_deadlines(df)

    # Step4
    clean_ets_code(df)

    # Write output
    df.to_csv(output_path, index=False)
    print(f"Cleaned CSV saved to {output_path}")

    # Export unhandled rows if any
    if UNHANDLED_ROWS:
        unhandled_path = output_path.with_name(output_path.stem + "_unhandled.csv")
        pd.DataFrame(UNHANDLED_ROWS).to_csv(unhandled_path, index=False)
        print(f"Unhandled rows exported to {unhandled_path}")


if __name__ == "__main__":
    main()
