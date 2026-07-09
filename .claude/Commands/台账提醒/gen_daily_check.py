#!/usr/bin/env python3
"""工班长每日台账核查提醒生成器

用法:
  python3 gen_daily_check.py              # 今天
  python3 gen_daily_check.py 2026-07-10   # 指定日期

输出格式化的 Markdown 提醒文本，可直接粘贴至 today.md
"""

import sys
from datetime import datetime, date, timedelta

today = date.today()
if len(sys.argv) > 1:
    today = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()

weekday = today.weekday()  # 0=Mon ... 6=Sun
weekday_cn = ["一", "二", "三", "四", "五", "六", "日"][weekday]
dom = today.day

# ============================================================
# 台账主数据
# ============================================================
LEDGERS = [
    (1,  "消防安全巡查记录本",        "每日",         "每日"),
    (2,  "防火检查记录表",            "每半月一次",    "每月15日、每月30日"),
    (3,  "灭火器情况统计表",          "每月18日",      "每月18日"),
    (4,  "灭火器巡视记录卡",          "科室发文时间",  "当日"),
    (5,  "防爆手电筒充电记录",        "每季度一次",    "每季度最后一个工作日"),
    (6,  "🚜 起重机、叉车日管控记录",  "已移交车辆中心", "已移交"),
    (7,  "消防档案",                  "发生变动即更新", "随更随查"),
    (8,  "杂品库应急物资",            "每月18日",      "每月18日"),
    (9,  "防寒防汛物资",              "每月18日/汛期每周", "每周五（汛期）"),
    (10, "安全培训（包含消防）",      "按年度计划时间", "每月25日"),
    (11, "巡更记录",                  "每日",         "每周五"),
    (12, "应急演练台账（纸质+上传系统）","演练后3个工作日", "每月20日"),
    (13, "个人演练档案",              "演练后2个工作日内", "演练后第2个工作日"),
    (14, "叉车等充电记录表、电量检查记录表", "每月一次", "每月25日"),
    (15, "🚜 起重机、叉车等日常使用记录表", "已移交车辆中心", "已移交"),
    (16, "断电登记本、断电安全群断电信息", "每日",     "每日"),
    (17, "外来人员安全告知书、入库登记记录", "外来人员入库时", "随来随查"),
    (18, "安全自查记录",              "每周一次",      "每周五"),
    (19, "隐患排查清单",              "每周一次",      "每周五"),
    (20, "CIMS系统内故障提报记录",    "每周一次",      "每周五"),
]


def prev_workday(d):
    """从d往前找第一个工作日（如果d本身是工作日则返回d）"""
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def generate():
    lines = []
    lines.append("")
    lines.append(f"### 📋 今日台账核查 ({today} 周{weekday_cn})")
    lines.append("")

    check_items = []   # (section_title, [(n, name, freq), ...])

    # 1. 每日必查（排除已移交项）
    daily = [l for l in LEDGERS if "每日" in l[3] and "每周" not in l[3] and "已移交" not in l[2]]
    if daily:
        check_items.append(("🔴 每日必查", daily))

    # 2. 每周五
    if weekday == 4:
        friday = [l for l in LEDGERS if "每周五" in l[3] and "已移交" not in l[2]]
        if friday:
            check_items.append(("🟡 每周五检查", friday))

    # 3. 每月固定日期（排除已移交项）
    monthly_map = {15: [2], 18: [3, 8, 9], 20: [12], 25: [10, 14], 30: [2]}
    if dom in monthly_map:
        ids = monthly_map[dom]
        monthly = [l for l in LEDGERS if l[0] in ids and "已移交" not in l[2]]
        if monthly:
            check_items.append((f"🔵 每月{dom}日检查", monthly))

    # 4. 季度末
    quarter_dates = [
        ((3, 31), "Q1"),
        ((6, 30), "Q2"),
        ((9, 30), "Q3"),
        ((12, 31), "Q4"),
    ]
    for (qm, qd), qlabel in quarter_dates:
        target = date(today.year if today.month <= qm or (today.month == qm and today.day <= qd) else today.year, qm, qd)
        target = prev_workday(target)
        if today == target:
            check_items.append((f"🟢 {qlabel}末检查", [l for l in LEDGERS if l[0] == 5]))

    # --- 输出 ---
    if check_items:
        for title, items in check_items:
            lines.append(f"**{title}**")
            for n, name, freq, _ in items:
                lines.append(f"- [ ] [{n:02d}] {name}（{freq}）")
            lines.append("")

        # 节假日提醒
        notes = []
        if dom in monthly_map:
            for lid in monthly_map[dom]:
                l = [x for x in LEDGERS if x[0] == lid][0]
                if today.weekday() >= 5:
                    prev = prev_workday(today)
                    notes.append(f"> ⚠ [{l[0]:02d}] {l[1]} 逢节假日，建议提前至 {prev}")
        if notes:
            lines.extend(notes)
            lines.append("")

    # 附录：全部台账
    lines.append("<details>")
    lines.append('<summary><small>📖 全部20项台账清单（点击展开）</small></summary>')
    lines.append("")
    lines.append("| # | 台账名称 | 填写周期 | 核查时间 |")
    lines.append("|:-:|:---------|:---------|:---------|")
    for n, name, freq, check in LEDGERS:
        lines.append(f"| {n:02d} | {name} | {freq} | {check} |")
    lines.append("")
    lines.append("</details>")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    print(generate())
