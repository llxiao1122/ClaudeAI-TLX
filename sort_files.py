#!/usr/bin/env python3
"""
知识库新 文件整理脚本
======================
比对 1/ 和 2/ 中的文件，根据文件名和修改时间确定最新版，
将最新非安全类文件放入 最新版非安全类规章制度/，
历史版本放入 历史版本/，
同时保留原文件不动（仅复制）。
"""

import os
import re
import shutil
from datetime import datetime
from collections import defaultdict

BASE = "/Users/mi/Documents/claudeai/知识库新"
OUT_LATEST = os.path.join(BASE, "最新版非安全类规章制度")
OUT_OLD = os.path.join(BASE, "历史版本")
LAW_DIR = os.path.join(BASE, "法规和安全管理制度")

# ========== 工具函数 ==========

def get_files(dirpath):
    """递归获取目录下所有文件"""
    files = []
    if not os.path.exists(dirpath):
        return files
    for root, dirs, filenames in os.walk(dirpath):
        for fn in filenames:
            if fn.startswith('.') or fn == '.DS_Store':
                continue
            fp = os.path.join(root, fn)
            rel = os.path.relpath(fp, BASE)
            mtime = os.path.getmtime(fp)
            files.append((fn, fp, mtime, rel))
    return files

def extract_base_name(name):
    """提取文件名的核心名称（去掉版本号、括号、日期等）"""
    n = name.lower()
    n = re.sub(r'（[^）]*版?）', '', n)   # （A1版）（B2版）
    n = re.sub(r'\([^)]*版?\)', '', n)     # (A1版)(B2版)
    n = re.sub(r'[（(]\d*[)）]', '', n)    # (1)(2)(1)(1)
    n = re.sub(r'-\d{8}', '', n)           # -20250430
    n = re.sub(r'\d{4}\.\d{1,2}\.\d{1,2}', '', n)  # 2025.12.2
    n = re.sub(r'\d{4}-\d{1,2}-\d{1,2}', '', n)    # 2026-1-8
    n = re.sub(r'20\d{2}', '', n)          # 2026
    n = re.sub(r'v\d+\.?\d*', '', n)       # v1, v1.1
    n = re.sub(r'（最新）', '', n)
    n = re.sub(r'\[最新\]', '', n)
    n = n.strip(' ._-\t')
    return n

def parse_version(name):
    """从文件名中解析版本号，用于排序"""
    # 匹配 (A1版) (B2版) (A0版) 等
    m = re.search(r'[（(]([A-Z])(\d*)[)）]', name)
    if m:
        letter = m.group(1)
        num = int(m.group(2)) if m.group(2) else 0
        return (ord(letter), num)
    # 匹配 V1, V1.1, V12025.12.2 等
    m = re.search(r'[Vv](\d+(?:\.\d+)?)', name)
    if m:
        parts = m.group(1).split('.')
        return (ord('Z'), int(parts[0]))
    return None

def is_safety_file(filename, relpath):
    """判断文件是否属于安全/法规类"""
    safety_keywords = [
        '安全', '消防', '防汛', '防寒', '应急', '预案', '事故',
        '隐患', '危废', '废旧', '环保', '法规', '法律', '条例',
        '固体废物', '化学品', '泄漏', '灭火', '特种设备',
        '职业病', '劳保', '防护', '救援', '疏散', '演练',
    ]
    name_lower = filename.lower()
    for kw in safety_keywords:
        if kw in name_lower:
            return True
    return False

def is_same_document(name1, name2):
    """判断两个文件名是否指向同一文档"""
    base1 = extract_base_name(name1)
    base2 = extract_base_name(name2)
    if not base1 or not base2:
        return False
    # 如果核心名称相同
    if base1 == base2:
        return True
    # 如果一个包含另一个
    if base1 in base2 or base2 in base1:
        return True
    return False

def group_by_topic(files):
    """将文件按主题分组"""
    groups = defaultdict(list)
    assigned = set()

    # 先用精确文件名分组
    name_map = defaultdict(list)
    for fn, fp, mt, rel in files:
        base = extract_base_name(fn)
        if base:
            name_map[base].append((fn, fp, mt, rel))

    # 合并相似的文件名
    used_bases = set()
    for base, items in sorted(name_map.items(), key=lambda x: -len(x[1])):
        if base in used_bases or not base:
            continue
        group = list(items)
        used_bases.add(base)

        # 尝试合并相似的其他组
        for other_base, other_items in sorted(name_map.items()):
            if other_base in used_bases or not other_base:
                continue
            if is_same_document(base, other_base) or is_same_document(other_base, base):
                group.extend(other_items)
                used_bases.add(other_base)

        if group:
            groups[base].extend(group)

    # 没被分组的单个文件
    all_assigned = set()
    for items in groups.values():
        for item in items:
            all_assigned.add(item[1])  # fp

    singles = [f for f in files if f[1] not in all_assigned]
    for fn, fp, mt, rel in singles:
        base = extract_base_name(fn)
        if base:
            groups[base].append((fn, fp, mt, rel))

    return groups


# ========== 主流程 ==========

def main():
    print("=" * 60)
    print("知识库新 文件整理")
    print("=" * 60)

    # 获取所有文件
    files1 = get_files(os.path.join(BASE, "1"))
    files2 = get_files(os.path.join(BASE, "2"))
    files_all = files1 + files2
    law_files = get_files(LAW_DIR)
    law_names = {f[0] for f in law_files}

    print(f"\n📊 统计")
    print(f"  1/: {len(files1)} 个文件")
    print(f"  2/: {len(files2)} 个文件")
    print(f"  法规和安全管理制度: {len(law_files)} 个文件")

    # 按主题分组
    groups = group_by_topic(files_all)

    # 已处理文件路径
    processed = set()

    print(f"\n📋 共识别 {len(groups)} 个主题组")

    # 分类逻辑
    latest_files = []
    old_files = []

    for topic, items in sorted(groups.items(), key=lambda x: -len(x[1])):
        # 按修改时间从新到旧排序
        items_sorted = sorted(items, key=lambda x: -x[2])

        # 检查是否在法规目录中
        in_law = any(f[0] in law_names for f in items_sorted)

        # 检查是否安全类
        is_safety = any(is_safety_file(f[0], f[3]) for f in items_sorted)

        if len(items_sorted) == 1:
            # 单个文件
            fn, fp, mt, rel = items_sorted[0]
            if fn in processed:
                continue
            processed.add(fp)

            if is_safety and in_law:
                # 安全类且已在法规目录中 -> 旧版
                old_files.append((fn, fp, mt, rel, "法规目录中已有"))
            elif is_safety and not in_law:
                # 安全类但不在法规目录中 -> 需要判断
                old_files.append((fn, fp, mt, rel, "安全类待确认"))
            else:
                # 非安全类
                latest_files.append((fn, fp, mt, rel, "唯一版本"))
        else:
            # 多个版本
            # 按日期排序，最新的为最新版
            latest_item = items_sorted[0]

            # 如果有版本号，用版本号比较
            versions = []
            for fn, fp, mt, rel in items_sorted:
                v = parse_version(fn)
                versions.append((v, fn, fp, mt, rel))

            # 按版本号排序（如果有）
            if any(v[0] for v in versions):
                versions.sort(key=lambda x: (
                    x[0][0] if x[0] else ord('Z')+1,
                    x[0][1] if x[0] else 0,
                    -x[3]  # 同版本号取最新的
                ), reverse=True)
                latest_item_v = versions[0]
                latest_fn, latest_fp, latest_mt, latest_rel = latest_item_v[1:]
                old_items = [(v[1], v[2], v[3], v[4]) for v in versions[1:]]
            else:
                latest_fn, latest_fp, latest_mt, latest_rel = latest_item
                old_items = [(f, p, t, r) for f, p, t, r in items_sorted[1:]]

            if latest_fp in processed:
                continue
            processed.add(latest_fp)

            # 检查最新版是否在法规目录
            latest_in_law = latest_fn in law_names

            if latest_in_law:
                # 最新版已在法规目录 -> 旧版
                old_files.append((latest_fn, latest_fp, latest_mt, latest_rel, "法规目录中有更新版本"))
            elif is_safety and latest_in_law:
                old_files.append((latest_fn, latest_fp, latest_mt, latest_rel, "安全类，法规目录已有"))
            else:
                latest_files.append((latest_fn, latest_fp, latest_mt, latest_rel, f"共{len(items_sorted)}个版本，此为最新"))

            # 旧版本
            for fn, fp, mt, rel in old_items:
                if fp in processed:
                    continue
                processed.add(fp)
                old_files.append((fn, fp, mt, rel, f"旧版本"))

    # ========== 输出结果 ==========
    print(f"\n{'='*60}")
    print(f"📦 整理结果")
    print(f"{'='*60}")
    print(f"\n✅ 最新版非安全类文件: {len(latest_files)} 个")
    print(f"📦 历史版本文件: {len(old_files)} 个")
    print(f"   (原始文件全部保留不动)")

    # 显示最新版文件清单
    print(f"\n{'─'*60}")
    print("📋 最新版文件清单（将复制到 最新版非安全类规章制度/）")
    print(f"{'─'*60}")
    for fn, fp, mt, rel, reason in sorted(latest_files, key=lambda x: x[3]):
        date = datetime.fromtimestamp(mt).strftime("%Y-%m-%d")
        print(f"  [{date}] {rel}")
        print(f"          └─ {reason}")

    print(f"\n{'─'*60}")
    print("📋 历史版本文件清单（将复制到 历史版本/）")
    print(f"{'─'*60}")
    for fn, fp, mt, rel, reason in sorted(old_files, key=lambda x: x[3]):
        date = datetime.fromtimestamp(mt).strftime("%Y-%m-%d")
        print(f"  [{date}] {rel}")
        print(f"          └─ {reason}")

    # ========== 执行复制 ==========
    print(f"\n{'='*60}")
    print("🚀 开始复制文件...")
    print(f"{'='*60}")

    for folder, files in [(OUT_LATEST, latest_files), (OUT_OLD, old_files)]:
        if not os.path.exists(folder):
            os.makedirs(folder)

        for fn, fp, mt, rel, reason in files:
            # 保持相对路径结构
            rel_dir = os.path.dirname(rel)
            target_dir = os.path.join(folder, rel_dir) if rel_dir else folder
            os.makedirs(target_dir, exist_ok=True)

            target = os.path.join(target_dir, fn)
            if not os.path.exists(target):
                shutil.copy2(fp, target)
                print(f"  ✅ 复制: {rel}")
            else:
                print(f"  ⏭️  已存在: {rel}")

    print(f"\n{'='*60}")
    print("✅ 整理完成！")
    print(f"{'='*60}")
    print(f"\n📂 最新版: {OUT_LATEST}")
    print(f"📂 历史版本: {OUT_OLD}")
    print(f"📂 原始文件: 1/ 和 2/（未改动）")
    print(f"📂 法规和安全管理制度: 已确认最新版（未改动）")

if __name__ == "__main__":
    main()
