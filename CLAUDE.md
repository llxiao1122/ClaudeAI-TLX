# 铁炉西工班 — AI工作系统

> 这不是一个知识库，这是一个具有长期记忆、技能、工作流和思考能力的AI工作系统。

---

## 🏗 系统架构

```
六层架构：
Memory（Why）→ AI身份/偏好/错误/经验/决策/领导认知
Context（Now）→ 今日动态：值班/重点/截止/风险
Workflow（How）→ 标准化工作流程
Skill（Can do）→ 专注能力
Template（Output）→ 统一输出格式
Knowledge（What）→ 制度/规范/文件
```

## 🚀 启动加载顺序

每次对话开始，自动按序加载：
1. **MEMORY.md** → 模块索引
2. **memory/** → 身份/思考/决策/错误/经验/领导认知/历史
3. **context/today.md** → 今日状态（值班/重点/截止/风险）
4. **任务与记录.md** → 当前待办清单
5. **知识库/INDEX.md** → 按需定位

## 🧠 回答八步流程（详见 memory/thinking.md）

```
输入 → 判断类型 → 读Memory → 读Context → 关联Skill → 检索Knowledge → 引用Template → 输出 → 更新
```

## 📂 模块索引

| 层 | 位置 | 内容 | 说明 |
|:---|:----|:----|------|
| Memory | `.claude/memory/` | 10个文件 | 身份/偏好/思考/决策/错误/经验/领导/历史/任务/组织 |
| Context | `.claude/context/today.md` | 每日更新 | 值班人/重点/截止/风险/人员状态 |
| Workflow | `.claude/workflow/` | 4个流程 | 工作安排/制度查询/领导安排/信息记录 |
| Templates | `.claude/templates/` | 4个模板 | 工作安排/制度分析/日报/会议纪要 |
| Skill | `.claude/skills/铁炉西工班/SKILL.md` | 核心入口 | 班组速查+交互模式 |
| Knowledge | `知识库/` (173文件) | 11类 | 制度/安全/手册/台账/培训/公文/现场/三菱 |
| Knowledge Index | `知识库/INDEX.md` | 全量索引 | 关键词+版本对照+关联关系 |
| Knowledge Rules | `知识库/CLAUDE.md` | AI知识规则 | 使用/引用/版本/新增规范 |

## 👥 人员速查

| 角色 | 姓名 |
|:----|:----:|
| 工班长 | 李林骁 |
| 保管员 | 杨梦卓 / 陈红洁 / 张志斌 / 苗笑天 / 谭继衡 |
| 直接上级 | 王敬宇（物资调配室主任） |
| 安全对口 | 卢丽英（副主任）/ 王亮 |
| 包保人 | 董文静 |
| 危废对接 | 王超 / 荆幸斌 |

## 🔄 跨设备同步规范

```bash
git pull                          # 拉取另一台设备更新的记忆
# 工作...
git add -A
git commit -m "记忆更新：摘要"
git push
```

各设备独立（不同步）：`.claude/settings.local.json` / `.claude/scheduled_tasks.*`

## 🛠️ 日常入口

- `/铁炉西工班` — 工班管理主入口
- `/铁炉西工班管理知识库` — 知识库查询
- `memory/thinking.md` — 思考流程
- `workflow/` — 标准工作流
- `templates/` — 输出模板

## ⚠️ 核心规则

1. **先读后写** — Edit前必须Read目标文件最新状态
2. **查数据不推算** — 值班表/人员信息查原始数据
3. **标注来源** — 引用制度必须带版本号
4. **不确定要说** — 标注【推测】/【需确认】
5. **每轮检查更新** — 新任务/新错误/新经验 → 写入对应文件
