# AI系统改造方案

> 基于AI系统分析报告，从"知识库"升级为"具备长期记忆、技能、工作流、思考能力的AI工作系统"

---

## 一、目标架构总览

```
.claude/                          # Claude项目配置（现有）
├── MEMORY.md                     # 记忆索引（保持）
├── settings.local.json           # 本地配置（保持）
│
├── memory/                       # 🆕 重构 — 长期记忆层（Why）
│   ├── identity.md               #   我是谁（角色/定位/风格）
│   ├── preferences.md            #   偏好（工作习惯/沟通方式）
│   ├── organization.md           #   组织架构（保持现有）
│   ├── leadership.md             #   领导认知（从references迁入）
│   ├── experience.md             #   经验沉淀
│   ├── mistakes.md               # 🆕 错误记录
│   ├── thinking.md               # 🆕 思考流程
│   ├── decision.md               # 🆕 决策原则
│   └── history.md                # 🆕 会话摘要归档
│
├── context/                      # 🆕 动态上下文层（Now）
│   └── today.md                  #   今日状态（值班/重点/截止/风险）
│
├── workflow/                     # 🆕 工作流层（How）
│   ├── 日报生成.md
│   ├── 工作安排.md
│   ├── 会议纪要.md
│   ├── 制度查询分析.md
│   ├── 领导安排处理.md
│   └── 安全检查.md
│
├── templates/                    # 🆕 模板层（Output）
│   ├── 日报模板.md
│   ├── 工作安排模板.md
│   ├── 会议纪要模板.md
│   └── 制度分析模板.md
│
├── skills/                       # 🔄 重构 — 能力层（Can do）
│   ├── 工班管理/                 #   从原铁炉西工班拆分
│   ├── 安全管理/
│   ├── 台账管理/
│   └── 会议管理/
│
├── agents/                       # 🆕 专岗Agent层
│   ├── 值班管理.md
│   ├── 任务跟踪.md
│   └── 安全提醒.md
│
├── graph/                        # 🆕 知识关联层
│   └── 关联关系.md
│
├── learning/                     # 🆕 持续学习层
│   └── 学习建议.md
│
└── 铁炉西工班.md                 # 🔄 精简（现有）
```

```
知识库/                           # 保持 — 知识层（What）
├── INDEX.md                      # 完善
├── CLAUDE.md                     # 完善
├── 01-物资管理制度/
├── 02-安全管理/
├── 03-工作指导手册/
├── 04-工作台账与工具/
├── 05-培训与学习资料/
├── 06-公文模板与规范/
├── 07-现场管理与6S/
├── 08-三菱备件专项/
├── 09-评估表/
├── 10-旧版与归档/
├── 11-法规标准/
└── 99-知识库系统/
```

```
CLAUDE.md（根目录）               # 🔄 重构 — 总入口
```

---

## 二、现有 vs 目标 架构对比

| 现有 | 目标 | 操作 |
|:----|:----|:----:|
| `.claude/memory/` 7个扁平文件 | `.claude/memory/` 9个分类文件 | 🔄 拆分重构 |
| — | `.claude/memory/mistakes.md` | 🆕 创建 |
| — | `.claude/memory/thinking.md` | 🆕 创建 |
| — | `.claude/memory/decision.md` | 🆕 创建 |
| — | `.claude/context/` | 🆕 创建 |
| — | `.claude/workflow/` | 🆕 创建 |
| — | `.claude/templates/` | 🆕 创建 |
| `.claude/skills/铁炉西工班/` 1700行混合 | 多个独立Skill | 🔄 拆分 |
| `.claude/skills/铁炉西工班/references/领导认知档案.md` | `.claude/memory/leadership.md` | 🔄 迁入Memory |
| — | `.claude/agents/` | 🆕 创建 |
| — | `.claude/graph/` | 🆕 创建 |
| — | `.claude/learning/` | 🆕 创建 |
| `知识库/` 分类完成 | 不变 | ✅ 保持 |
| `CLAUDE.md` 41行 | 扩展为完整AI入口 | 🔄 重构 |
| `知识库/CLAUDE.md` | 完善同步 | 🔄 完善 |

---

## 三、保留清单（不动）

| 文件 | 原因 |
|:----|:----|
| `.claude/MEMORY.md` | 索引，保持 |
| `知识库/`全部目录 | 分类成熟，刚重构完 |
| `知识库/INDEX.md` | 全量索引可用 |
| `知识库/CLAUDE.md` | 知识使用规则完善 |
| `.claude/skills/铁炉西工班/references/人员档案.md` | 内容精细，引用广泛 |
| `.claude/skills/铁炉西工班/scripts/调用日志.py` | 日志机制可用 |
| `.claude/settings.local.json` | 本地配置不动 |

---

## 四、实施顺序

### 阶段一：Memory重构（P0）
```
1.1 创建 mistakes.md      ← 立即防止重复犯错
1.2 创建 thinking.md       ← 标准化思考流程
1.3 创建 decision.md       ← 归档决策原则
1.4 重构现有memory文件     ← 拆分identity/preferences等
1.5 迁入leadership.md      ← 从references迁到memory
1.6 更新 MEMORY.md索引
```

### 阶段二：Context创建（P0）
```
2.1 创建 context/today.md  ← 每日动态状态
```

### 阶段三：Workflow创建（P0）
```
3.1 创建工作安排workflow
3.2 创建日报生成workflow
3.3 创建制度查询分析workflow
3.4 创建领导安排处理workflow
3.5 创建安全检查workflow
```

### 阶段四：Skills拆分（P1）
```
4.1 拆分工班管理skill
4.2 拆分安全管理skill
4.3 拆分台账管理skill
4.4 精简原铁炉西工班.md
```

### 阶段五：Templates创建（P1）
```
5.1 工作安排模板
5.2 日报模板
5.3 会议纪要模板
5.4 制度分析模板
```

### 阶段六：Agents创建（P2）
```
6.1 值班管理agent
6.2 任务跟踪agent
6.3 安全提醒agent
```

### 阶段七：根CLAUDE.md重构 + Graph + Learning（P2-P3）
```
7.1 重构根目录CLAUDE.md
7.2 创建graph/关联关系
7.3 创建learning/学习机制
```

---

## 五、每个模块的三问验证（实施前必答）

每个新模块创建前，回答：
1. **解决了AI哪个能力缺陷？**
2. **与现有模块如何协作不重复？**
3. **对未来新AI是否有通用价值？**

不满足三条的模块不创建，优先复用现有结构。
