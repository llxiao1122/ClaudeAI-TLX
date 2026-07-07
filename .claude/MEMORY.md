# 组织记忆

> 此为索引文件。具体内容在各模块目录中。

---

## 模块导航

### ⚖️ 宪法
| 文件 | 说明 |
|:----|:----|
| [AI_CONSTITUTION.md](AI_CONSTITUTION.md) | 最高行为准则（真实/不越权/安全优先/持续学习/信息密度） |

### 🤖 工作规则
| 文件 | 说明 |
|:----|:----|
| [CLAUDE.md](CLAUDE.md) | 消息处理五步流程 + 人员/领导分析规则 |

### 👥 Management/
| 子模块 | 文件 | 内容 |
|:------|:----|------|
| People/ | 李林骁班组.md | 班组全员档案（工作特点/能力/沟通/成长） |
| Leaders/ | leadership.md | 领导行为模式/关注点/汇报策略 |
| Tasks/ | tasks.md | 待办清单（紧急/常规/持续/已完结） |
| Events/ | history.md | 关键事件/决策/会话摘要 |
| Observations/ | （可增长） | 人员行为观察记录 |
| Rules/ | 决策原则.md, mistakes.md, 思考流程.md | 决策准则/错误记录/思考路径 |

### 🧠 Memory/
| 文件 | 内容 |
|:----|:----|
| Preferences.md | AI工作偏好/输出习惯 |
| Experience.md | 经验沉淀（可复用） |
| Organization.md | 组织架构/岗位/师徒/人员速写 |

### 📋 Context/
| 文件 | 内容 |
|:----|:----|
| Today.md | 今日动态（值班/重点/截止/风险） |
| ThisWeek.md | 本周重点 |
| CurrentProjects.md | 当前专项项目 |

### ⚡ Commands/
| 文件 | 功能 |
|:----|:----|
| 日报.md | 日报生成工作流 |
| 会议.md | 会议纪要模板 |
| 制度分析.md | 制度查询分析流程 |
| 工作安排模板.md | 工作安排输出模板 |

### 📊 Analysis/
| 子模块 | 功能 |
|:------|:----|
| Weekly/ | 周分析 |
| Monthly/ | 月度分析 |
| Leadership/ | 领导风格分析 |
| Team/ | 团队状态分析 |
| Risk/ | 风险评估 |

### 📚 Knowledge/
| 子模块 | 说明 |
|:------|:----|
| Documents/ | 制度/规范/流程文档 |
| Objects/ | 物资/资产对象信息 |
| Archive/ | 历史归档 |
| *知识库/* | 完整制度/安全/手册库（外部目录） |

### 🗄️ Archive/
| 说明 |
|:----|
| 历史版本/已完成项目/过期任务归档 |

---

## 启动加载顺序

每次对话开始，自动加载：
1. `AI_CONSTITUTION.md` → 宪法
2. `CLAUDE.md` → 工作规则
3. `Context/Today.md` → 今日动态
4. `Context/ThisWeek.md` → 本周重点
5. `Management/Tasks/tasks.md` → 当前待办
6. `Context/CurrentProjects.md` → 当前项目
7. `知识库/INDEX.md` → 按需定位
