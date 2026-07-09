# Telegram Bridge 架构分析

> 分析日期: 2026-07-08
> 仅分析，不修改

---

## 一、文件清单

### 当前生效

| 文件 | 类型 | 用途 |
|:-----|:------|:------|
| `tg.sh` | Shell | 一体化检查+发送（当前主力） |
| `tg_check.sh` | Shell | 仅检查（tg.sh 的子集，废弃） |
| `tg_send.sh` | Shell | 仅发送（tg.sh 的子集，废弃） |
| `inbox.md` | 数据 | 消息存档 |
| `outbox.md` | 数据 | bot.py 的发送触发器（随 bot.py 一起废弃） |
| `chat_id.txt` | 数据 | 聊天对象 ID |
| `offset.txt` | 数据 | bot.py 的偏移量（随 bot.py 一起废弃） |
| `counter.txt` | 数据 | bot.py 的消息计数（随 bot.py 一起废弃） |
| `/tmp/tg_off` | 数据 | tg.sh 的偏移量 |

### 已废弃（macOS TCC 封杀，不可用）

| 文件 | 原因 |
|:-----|:------|
| `bot.py` | 后台进程被 macOS 禁止读文件 |
| `cron_bot.sh` | cron 启动的 bot 同样被禁 |
| `run_bot.sh` | 启动脚本，本身不解决阻塞问题 |
| `start.command` | 桌面双击启动脚本 |
| `server.py` | Flask webhook，未配置 frp 隧道 |
| `bot.log` | 仅记录了 "Operation not permitted" 错误 |

---

## 二、调用链

### 当前生效

```
你: "查看"
  └→ Claude: bash tg.sh
       ├→ 读 /tmp/tg_off (offset)
       ├→ GET api.telegram.org/getUpdates?offset=X&timeout=10
       │      ↕ Clash代理 127.0.0.1:7897
       ├→ 有新消息?
       │   ├→ 是 → 写入 inbox.md → 输出 "新消息: NAME: TEXT"
       │   └→ 否 → 输出 "无新消息"
       └→ Claude 看到结果 → 决定下一步

Claude: "需要回复"
  └→ bash tg.sh "回复内容"
       ├→ POST api.telegram.org/sendMessage
       │      ↕ Clash代理 127.0.0.1:7897
       └→ 输出 "已发送: 回复内容"
```

### 已废弃（bot.py 生命周期）

```
bot.py 启动
  └→ 循环每 3 秒:
       ├→ GET getUpdates(offset, timeout=30) → 有新消息?
       │   └→ 是 → 写入 inbox.md + 更新 offset.txt
       ├→ 检查 outbox.md 文件大小
       │   └→ 变了 → 读新增内容 → POST sendMessage
       └→ sleep 3
```

---

## 三、数据流

```
                    ┌──────────────────────┐
                    │    Telegram API      │
                    │ api.telegram.org     │
                    └──────┬──────────┬────┘
                           ↕ Clash    ↕ Clash
                           │ 7897     │ 7897
                    ┌──────┴──┐  ┌────┴──────┐
                    │tg.sh     │  │tg.sh      │
                    │getUpdates│  │sendMessage│
                    └────┬─────┘  └────┬──────┘
                         │             │
                    ┌────┴─────┐       │
                    │/tmp/tg_off│      │
                    │ (offset)  │      │
                    └──────────┘       │
                         │             │
                    ┌────┴─────┐       │
                    │ inbox.md │←──────┘ (Claude读此文件看消息)
                    │ (存档)   │
                    └──────────┘
                         ↑
                    Claude Code 读取 → 处理 → 回复
```

---

## 四、冗余与问题

| 问题 | 说明 |
|:-----|:------|
| 3 个脚本做同一件事 | tg.sh = tg_check.sh + tg_send.sh，后两个可删 |
| bot.py + 配套文件已死 | offset.txt, counter.txt, outbox.md, bot.log, cron_bot.sh, run_bot.sh, start.command, server.py 无人使用 |
| inbox.md 有 26 行测试垃圾 | 超过一半是测试阶段的重复消息 |
| 两个 offset 文件 | /tmp/tg_off vs /tmp/tg_offset，各有用户 |
| .processed 文件无用 | 已无代码引用 |

---

## 五、简化目标

```
你: "查看" ─→ tg.sh 检查 ─→ 有新消息? ─→ 是 → Claude 处理 + tg.sh 回复
                                           └→ 否 → 输出 "无新消息"

文件精简到最低:
  保留: tg.sh, inbox.md, chat_id.txt, /tmp/tg_off
  删除: 其余所有
```
