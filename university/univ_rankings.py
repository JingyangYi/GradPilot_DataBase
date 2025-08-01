#!/usr/bin/env python3
"""
merge_subject_rankings.py
=========================

将 WUR by Subject (多个 sheet) 的学科排名合并到总体排名表格中。

用法:
python univ_rankings.py \
    --wur "2025 QS WUR by Subject - Public Results V1.1.2 (for qs.com) 2_34.xlsx" \
    --overall "2026QS+&+2026USNews+&+2025THE+&+2024ARWU+世界大学排名对照+完整版.xlsx" \
    --out merged_rankings.csv

参数说明:
    --wur      WUR by Subject 的 Excel 文件路径, 每个 sheet 为一个学科, 第一列为 2025 QS 学科排名, 第三列为大学英文名称.
    --overall  总体排名 Excel 文件路径, 需包含列 "学校英文名".
    --out      输出 CSV 文件路径 (默认 output.csv).

依赖:
    pip install pandas openpyxl rapidfuzz

匹配逻辑:
    1. **严格匹配(忽略大小写空格)**
    2. **规范化匹配**: 移除常见停用词 (university, the, of, etc.) 与标点
    3. **缩写匹配**: 比较字符串大写字母缩写 (例: "University College London" -> "UCL")
    4. **模糊匹配**: RapidFuzz token_set_ratio >= THRESHOLD

作者: ChatGPT
日期: 2025-07-22
"""
import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

try:
    from rapidfuzz import process, fuzz  # type: ignore
    _HAS_RAPIDFUZZ = True
except ImportError:  # 兼容环境无 rapidfuzz
    from difflib import SequenceMatcher

    _HAS_RAPIDFUZZ = False
    print("[WARN] rapidfuzz 未安装, 将降级使用 difflib, 匹配精度与速度可能受影响", file=sys.stderr)


STOP_WORDS = {
    "university", "universiti", "college", "the", "of", "at", "and", "school", "in",
    "for", "institute", "technological", "technology", "national", "state", "federal",
}

# 手动名称映射: 处理无法通过算法匹配的特殊别名 → 总体排名表中的标准名称
MANUAL_NAME_MAP: Dict[str, str] = {
    # UCL
    "ucl": "University College London（UCL）",
    "university college london": "University College London（UCL）",
    "university college london (ucl)": "University College London（UCL）",
    # Free University of Berlin
    "freie universitaet berlin": "Free University of Berlin",
    "freie universität berlin": "Free University of Berlin",
    "free university berlin": "Free University of Berlin",
}
MANUAL_NAME_MAP.update({
    # Nanyang Technological University
    "nanyang technological university (ntu)": "Nanyang Technological University",
    "nanyang tech university": "Nanyang Technological University",
    "ntu": "Nanyang Technological University",

    # École Polytechnique Fédérale de Lausanne
    "epfl": "École Polytechnique Fédérale de Lausanne",
    "ecole polytechnique federale de lausanne": "École Polytechnique Fédérale de Lausanne",

    # PSL University
    "paris sciences & lettres": "PSL University",
    "psl research university paris": "PSL University",

    # University of Malaya
    "universiti malaya": "University of Malaya",

    # University of California, San Diego
    "university of california san diego": "University of California, San Diego",
    "University of California, San Diego (UCSD)": "University of California, San Diego",
    "ucsd": "University of California, San Diego",

    # Sorbonne Universite
    "sorbonne university": "Sorbonne Universite",

    # Trinity College Dublin
    "Trinity College Dublin": "Trinity College Dublin, The University of Dublin",

    # Heidelberg University
    "ruprecht karls university heidelberg": "Heidelberg University",
    "ruprecht-karls-universität heidelberg": "Heidelberg University",
    "university of heidelberg": "Heidelberg University",

    # Penn State
    "pennsylvania state university": "Penn State (Main campus)",
    "pennsylvania state university university park": "Penn State (Main campus)",
    "penn state university": "Penn State (Main campus)",

    # Osaka University
    "university of osaka": "Osaka University",

    # RWTH Aachen
    "rwth aachen university": "Rheinisch-Westfälische Technische Hochschule Aachen",
    "rwth aachen": "Rheinisch-Westfälische Technische Hochschule Aachen",

    # Pontificia Universidad Católica de Chile
    "pontificia universidad catolica de chile": "Pontificial Catholic University of Chile",
    "pontifical catholic university of chile": "Pontificial Catholic University of Chile",

    # UNAM
    "universidad nacional autonoma de mexico": "National Autonomous University of Mexico",
    "unam": "National Autonomous University of Mexico",

    # Technical University of Berlin
    "technical university of berlin": "Technical University of Berlin",
    "tu berlin": "Technical University of Berlin",

    # Autonomous University of Barcelona
    "universitat autonoma de barcelona": "Autonomous University of Barcelona",
    "uab": "Autonomous University of Barcelona",

    "New York University (NYU)": "New York University",

    # Khalifa University
    "khalifa university": "Khalifa University",

    # University of Indonesia
    "universitas indonesia": "University of Indonesia",

    "The University of New South Wales (UNSW Sydney)": "The University of New South Wales",
    "Trinity College Dublin, The University of Dublin": "Trinity College Dublin",



    # Queen’s University
    "Queen's University Belfast": "Queen’s University",
    "queens university": "Queen’s University",

    # UCLouvain
    "uclouvain": "Université Catholique de Louvain",
    "catholic university of louvain": "Université Catholique de Louvain",
})

FUZZY_THRESHOLD = 85  # 相似度阈值略微降低，提升匹配率


# 更新 canonicalize: 额外去除全角括号等常用中文标点
_CN_PUNCTUATION = "（）【】《》“”‘’，。；！￥、"

def canonicalize(name: str) -> str:
    """返回字符串规范化版本: 小写, 去除标点, 去除停用词, 去除多余空格."""
    # 将中文标点替换为空格
    tbl = str.maketrans({ch: " " for ch in _CN_PUNCTUATION})
    name = name.translate(tbl)
    name = re.sub(r"[()'`\.\-,]", " ", name.lower())
    tokens = [t for t in name.split() if t and t not in STOP_WORDS]
    return " ".join(tokens)


def acronym(name: str) -> str:
    """从名称中提取大写字母形成缩写, 如 University College London -> UCL"""
    letters = re.findall(r"[A-Z]", name)
    if letters:
        return "".join(letters)
    # 如果原名本身已是大写缩写
    return name if name.isupper() and len(name) <= 6 else ""


def build_lookup(names: List[str]) -> Dict[str, str]:
    """根据总体排名表中的学校名称构建多个索引 -> 原始名称."""
    lookup = {}
    for n in names:
        orig = n
        n_clean = n.strip()
        lookup[n_clean.lower()] = orig  # exact lower-case
        lookup[canonicalize(n_clean)] = orig  # canonical form
        acro = acronym(n_clean)
        if acro:
            lookup[acro] = orig
    return lookup


def fuzzy_match(name: str, candidates: List[str]) -> Optional[str]:
    """使用 RapidFuzz (或 difflib) 找到最佳匹配."""
    if not candidates:
        return None

    if _HAS_RAPIDFUZZ:
        match, score, _ = process.extractOne(
            name,
            candidates,
            scorer=fuzz.token_set_ratio,
        )
        return match if score >= FUZZY_THRESHOLD else None
    # fall back to difflib
    best = max(
        candidates,
        key=lambda x: SequenceMatcher(None, name, x).ratio(),
    )
    score = SequenceMatcher(None, name, best).ratio() * 100
    return best if score >= (FUZZY_THRESHOLD / 100) else None


# ----------- 关键字/正则匹配 (仅针对极少数难匹配高校) ------------
REGEX_RULES: List[tuple[re.Pattern, str]] = [
    (re.compile(r"\bnanyang\b", re.I), "Nanyang Technological University"),
    (re.compile(r"\bpsl\b", re.I), "PSL University"),
    (re.compile(r"\bmalaya\b", re.I), "University of Malaya"),
    (re.compile(r"\bosaka\b", re.I), "Osaka University"),
    (re.compile(r"(catholic\\s*university\\s*of\\s*chile|pontific(?:ia|al).*chile)", re.I), "Pontificial Catholic University of Chile"),
    (re.compile(r"\b(unam|autonomous\\s+university\\s+of\\s+mexico)\b", re.I), "National Autonomous University of Mexico"),
    (re.compile(r"(technical\\s*university\\s*of\\s*berlin|technische\\s+universit[aä]t\\s+berlin|tu\\s*berlin)", re.I), "Technical University of Berlin"),
    (re.compile(r"(autonomous\\s*university\\s*of\\s*barcelona|universitat\\s+aut[oò]noma\\s+de\\s+barcelona|uab)" , re.I), "Autonomous University of Barcelona"),
    (re.compile(r"\bkhalifa\b", re.I), "Khalifa University"),
    (re.compile(r"queen['’]?s\\s+university(\\s+at\\s+kingston)?", re.I), "Queen’s University"),
    (re.compile(r"(uclouvain|catholic\\s+university\\s+of\\s+louvain)", re.I), "Université Catholique de Louvain"),
    # 新增规则
    (re.compile(r"(unsw|university\\s+of\\s+new\\s+south\\s+wales)", re.I), "The University of New South Wales"),
    (re.compile(r"(cuhk|chinese\\s+university\\s+of\\s+hong\\s+kong)" , re.I), "Chinese University Hong Kong"),
    # 新增 UC San Diego & Trinity College Dublin
    (re.compile(r"(ucsd|uc\\s*san\\s*diego|university\\s+of\\s+california[ ,]?\\s+san\\s+diego)", re.I), "University of California, San Diego"),
    (re.compile(r"(trinity\\s+college\\s+dublin|university\\s+of\\s+dublin)", re.I), "Trinity College Dublin"),
    (re.compile(r"(nyu|new\\s+york\\s+university)", re.I), "New York University"),
]


def match_name(name: str, lookup: Dict[str, str]) -> Optional[str]:
    """返回总体排名表中的标准学校名, 若匹配失败返回 None."""
    if not isinstance(name, str) or not name:
        return None

    name_strip = name.strip()

    # 0. 手动映射优先
    manual = MANUAL_NAME_MAP.get(name_strip.lower())
    if manual and manual in lookup.values():
        return manual

    # 0.1 正则规则匹配
    for pattern, target in REGEX_RULES:
        if pattern.search(name_strip):
            if target in lookup.values():
                return target

    # 1. exact lower-case
    exact = lookup.get(name_strip.lower())
    if exact:
        return exact

    # 2. canonical form match
    canon = canonicalize(name_strip)
    exact = lookup.get(canon)
    if exact:
        return exact

    # 3. acronym match
    acro = acronym(name_strip)
    if acro and acro in lookup:
        return lookup[acro]

    # 4. fuzzy match
    candidate_names = list({v for v in lookup.values()})  # unique original names
    best = fuzzy_match(name_strip, candidate_names)
    return best


# -------------------- 解析排名辅助 --------------------

def parse_rank(value) -> int:
    """将排名字符串或数字转换为整数, 处理"=7"、"51-100"等格式. 未知返回9999"""
    if pd.isna(value):
        return 9999
    s = str(value).strip()
    # 移除前导 '='
    if s.startswith('='):
        s = s[1:]
    # 处理区间 "51-100" 取最小值
    if '-' in s:
        s = s.split('-')[0]
    # 处理逗号数字
    s = s.replace(',', '')
    try:
        return int(s)
    except ValueError:
        return 9999


def main():
    parser = argparse.ArgumentParser(description="Merge WUR subject rankings with overall rankings.")
    parser.add_argument("--wur", required=True, help="Path to WUR by Subject Excel file")
    parser.add_argument("--overall", required=True, help="Path to Overall rankings Excel file")
    parser.add_argument("--out", default="merged_rankings.csv", help="Output CSV path")
    args = parser.parse_args()

    wur_path = Path(args.wur)
    overall_path = Path(args.overall)

    if not wur_path.exists():
        print(f"[ERROR] WUR file not found: {wur_path}", file=sys.stderr)
        sys.exit(1)
    if not overall_path.exists():
        print(f"[ERROR] Overall rankings file not found: {overall_path}", file=sys.stderr)
        sys.exit(1)

    # 读取总体排名表格
    overall_df = pd.read_excel(overall_path, header=1) # 使用第二行作为列名
    if "学校英文名" not in overall_df.columns:
        print("[ERROR] 总体排名文件缺少列 '学校英文名'", file=sys.stderr)
        sys.exit(1)

    # 构建名称查找
    overall_names = overall_df["学校英文名"].dropna().astype(str).tolist()
    lookup = build_lookup(overall_names)

    # 读取 WUR by Subject 的所有 sheet
    wur_xl = pd.ExcelFile(wur_path)
    subject_sheets = [s for s in wur_xl.sheet_names if s != wur_xl.sheet_names[0]]  # 跳过第一个菜单sheet

    print(f"处理 {len(subject_sheets)} 个学科 sheet …")
    for sheet in subject_sheets:
        print(f"  -> 处理学科: {sheet}")
        df_subject = wur_xl.parse(sheet, header=10) # 使用第11行作为列名

        if df_subject.shape[1] < 3:
            print(f"[WARN] Sheet '{sheet}' 列数不足, 跳过", file=sys.stderr)
            continue

        # 第一列为排名, 第三列为学校英文名
        ranking_col = df_subject.columns[0]
        name_col = df_subject.columns[2]
        subject_map: Dict[str, int] = {}

        for _, row in df_subject.iterrows():
            rank = row[ranking_col]
            uni_name = str(row[name_col]).strip()
            if pd.isna(rank) or not uni_name:
                continue
            matched_name = match_name(uni_name, lookup)
            if matched_name:
                # 只保留最好排名 (若某些学科多个排名)
                prev = subject_map.get(matched_name)
                if prev is None or rank < prev:
                    subject_map[matched_name] = rank
            else:
                print(f"[INFO] 未匹配: '{uni_name}' in subject '{sheet}'", file=sys.stderr)

        # 将排名加入总体 df
        overall_df[sheet] = overall_df["学校英文名"].apply(lambda x: subject_map.get(x, pd.NA))

    # 保存结果
    output_path = Path(args.out)
    overall_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"已生成合并文件: {output_path}")

    # 统计未匹配任何学科排名的学校 (仅限 QS<=200)
    unmatched_mask = overall_df[subject_sheets].isna().all(axis=1)
    if "QS 2026" in overall_df.columns:
        qs_rank_series = overall_df["QS 2026"].apply(parse_rank)
        top200_mask = qs_rank_series <= 200
    else:
        top200_mask = pd.Series([True] * len(overall_df))  # 若无列就全部True

    filtered_df = overall_df.loc[unmatched_mask & top200_mask, ["学校英文名", "QS 2026"]]

    if not filtered_df.empty:
        print("\n[注意] 以下 QS 前200 的学校未匹配到任何学科排名:")
        for name, rank in filtered_df.itertuples(index=False):
            print(f" - {name} (QS {rank})")


if __name__ == "__main__":
    main()
