#!/bin/bash
# ============================================================
# 迁移备份脚本 — 在当前 Mac (Intel) 上运行
# 用法: bash migrate-backup.sh
# 输出: ~/Desktop/migration-backup-xxx.tar.gz
# ============================================================
set -euo pipefail

BACKUP_DIR="$HOME/Desktop/migration-backup"
DEST_TAR="$HOME/Desktop/migration-backup-$(date +%Y%m%d).tar.gz"

echo "📦 创建备份目录: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"
cd "$BACKUP_DIR"

# --- SSH 密钥 ---
echo "🔑 备份 SSH 密钥..."
cp -r "$HOME/.ssh" .
chmod -R u+r .ssh

# --- Git 配置 ---
echo "📄 备份 Git 配置..."
cp "$HOME/.gitconfig" . 2>/dev/null && echo "  ✓ .gitconfig" || echo "  ⚠️  无 .gitconfig"

# --- Zsh 配置 ---
if [ -f "$HOME/.zshrc" ]; then
  cp "$HOME/.zshrc" . && echo "  ✓ .zshrc"
else
  echo "  - .zshrc 不存在（新建）"
  cat > .zshrc <<'ZSH_EOT'
# brew (ARM路径, 用于Mac Mini)
eval "$(/opt/homebrew/bin/brew shellenv)"

# 别名
alias ll='ls -la'
alias gs='git status'
alias gp='git pull'
alias gc='git commit'
alias ga='git add'
alias gl='git log --oneline --graph --decorate --all'
ZSH_EOT
fi

# --- VS Code 配置 ---
echo "🔌 备份 VS Code..."
VSCODE_USER="$HOME/Library/Application Support/Code/User"
if [ -f "$VSCODE_USER/settings.json" ]; then
  mkdir -p vscode
  cp "$VSCODE_USER/settings.json" vscode/
  cp "$VSCODE_USER/keybindings.json" vscode/ 2>/dev/null || true
  echo "  ✓ settings.json"
fi

# VS Code 扩展列表
if command -v code &>/dev/null; then
  code --list-extensions > vscode/extensions.txt 2>/dev/null
  echo "  ✓ 扩展列表 ($(wc -l < vscode/extensions.txt) 个)"
else
  echo "  ⚠️  code CLI 不可用，跳过扩展"
  touch vscode/extensions.txt
fi

# --- Claude Code ---
echo "🤖 备份 Claude Code 配置..."
CLAUDE_CONFIG="$HOME/.claude"
if [ -d "$CLAUDE_CONFIG" ]; then
  mkdir -p claude
  if [ -f "$CLAUDE_CONFIG/settings.json" ]; then
    cp "$CLAUDE_CONFIG/settings.json" claude/
    echo "  ✓ settings.json"
  fi
  # 导出 skill 列表（路径，不含内容）
  ls "$CLAUDE_CONFIG/skills/" 2>/dev/null > claude/skills-list.txt || echo "(无自定义 skill)" > claude/skills-list.txt
fi

# --- Homebrew 包列表 ---
echo "🍺 导出 Homebrew 包列表..."
if command -v brew &>/dev/null; then
  brew list --formula > brew-formulas.txt 2>/dev/null
  brew list --cask > brew-casks.txt 2>/dev/null
  echo "  ✓ formulas: $(wc -l < brew-formulas.txt)  casks: $(wc -l < brew-casks.txt)"
fi

# --- 汇总 ---
echo ""
echo "📋 备份清单:"
ls -la "$BACKUP_DIR"

# --- 打包 ---
echo ""
echo "🗜️  打包为: $DEST_TAR"
cd "$HOME/Desktop"
tar czf "$DEST_TAR" "$(basename "$BACKUP_DIR")" 2>/dev/null

# 清理临时目录
rm -rf "$BACKUP_DIR"

echo ""
echo "✅ 备份完成！文件: $DEST_TAR"
echo "   大小: $(du -h "$DEST_TAR" | cut -f1)"
echo ""
echo "👉 把这个文件传到 Mac Mini，然后在那边运行 setup-macmini.sh"
