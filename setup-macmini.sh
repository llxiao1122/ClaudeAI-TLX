#!/bin/bash
# ============================================================
# Mac Mini 环境恢复脚本 — 在 Mac Mini (Apple Silicon) 上运行
# 用法:
#   1. 把 migration-backup-xxx.tar.gz 放到桌面
#   2. bash setup-macmini.sh
# ============================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info()  { echo -e "${GREEN}✅${NC} $1"; }
warn()  { echo -e "${YELLOW}⚠️${NC} $1"; }
err()   { echo -e "${RED}❌${NC} $1"; }
step()  { echo ""; echo "━━━ $1 ━━━"; }

# 检测架构
ARCH=$(uname -m)
if [ "$ARCH" != "arm64" ]; then
  warn "当前架构: $ARCH（不是 arm64），确保你在 Mac Mini 上运行"
fi
echo "🔧 架构: $ARCH"

# ---------- 1. 解压备份 ----------
step "1/8 解压备份文件"
BACKUP_FILE="$HOME/Desktop/migration-backup-*.tar.gz"
TARGET=$(ls $BACKUP_FILE 2>/dev/null | head -1 || echo "")
if [ -z "$TARGET" ]; then
  warn "未在桌面找到备份文件 migration-backup-*.tar.gz"
  warn "请先把备份文件放到桌面，然后重新运行"
  warn "或者按 Ctrl+C 跳过，手动处理"
  echo "按回车键继续（跳过备份恢复）..."
  read -r
  BACKUP_DIR=""
else
  echo "找到: $TARGET"
  BACKUP_DIR=$(mktemp -d)
  tar xzf "$TARGET" -C "$BACKUP_DIR"
  BACKUP_CONTENT="$BACKUP_DIR/migration-backup"
  info "解压到: $BACKUP_CONTENT"
  ls -la "$BACKUP_CONTENT"
fi

# ---------- 2. Rosetta 2 ----------
step "2/8 Rosetta 2（Intel 兼容层）"
if /usr/bin/pgrep -q oahd 2>/dev/null; then
  info "Rosetta 2 已安装"
else
  echo "安装 Rosetta 2..."
  softwareupdate --install-rosetta --agree-to-license
  info "Rosetta 2 安装完成"
fi

# ---------- 3. Homebrew ----------
step "3/8 Homebrew (ARM 版)"
if command -v brew &>/dev/null && [ -f /opt/homebrew/bin/brew ]; then
  info "Homebrew (ARM) 已安装"
else
  echo "安装 Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

  # 加入 PATH（ARM 路径）
  if ! grep -q 'brew shellenv' "$HOME/.zshrc" 2>/dev/null; then
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$HOME/.zshrc"
  fi
  eval "$(/opt/homebrew/bin/brew shellenv)"
  info "Homebrew 安装完成"
fi
BREW_PREFIX=$(brew --prefix 2>/dev/null || echo "/opt/homebrew")
echo "  Homebrew 路径: $BREW_PREFIX"

# ---------- 4. 恢复 SSH ----------
step "4/8 恢复 SSH 密钥和 Git 配置"
if [ -n "${BACKUP_CONTENT:-}" ] && [ -d "$BACKUP_CONTENT/.ssh" ]; then
  cp -r "$BACKUP_CONTENT/.ssh" "$HOME/"
  chmod 700 "$HOME/.ssh"
  chmod 600 "$HOME/.ssh/id_rsa" 2>/dev/null || true
  chmod 644 "$HOME/.ssh/id_rsa.pub" 2>/dev/null || true
  chmod 644 "$HOME/.ssh/known_hosts" 2>/dev/null || true
  info "SSH 密钥已恢复"
fi

if [ -n "${BACKUP_CONTENT:-}" ] && [ -f "$BACKUP_CONTENT/.gitconfig" ]; then
  cp "$BACKUP_CONTENT/.gitconfig" "$HOME/"
  info "Git 配置已恢复"
else
  # 如果没备份，写一个基本配置
  if [ ! -f "$HOME/.gitconfig" ]; then
    git config --global user.name "Emmyer"
    git config --global user.email "paintlee@163.com"
    info "Git 基本配置已创建"
  fi
fi

# ---------- 5. 安装 CLI 工具 ----------
step "5/8 安装 CLI 工具"
PACKAGES="git gh node python@3.12"

for pkg in $PACKAGES; do
  if brew list "$pkg" &>/dev/null; then
    info "$pkg 已安装"
  else
    echo "安装 $pkg..."
    brew install "$pkg" || warn "$pkg 安装失败"
  fi
done

# 安装之前的环境中的软件包（如果有备份且想恢复）
if [ -n "${BACKUP_CONTENT:-}" ] && [ -f "$BACKUP_CONTENT/brew-formulas.txt" ]; then
  echo ""
  echo "之前环境的 brew formulas:"
  cat "$BACKUP_CONTENT/brew-formulas.txt"
  echo ""
  echo "是否安装上面的包？(y/n) 默认 n"
  read -r INSTALL_BREW
  if [ "$INSTALL_BREW" = "y" ] || [ "$INSTALL_BREW" = "Y" ]; then
    while IFS= read -r pkg; do
      [ -z "$pkg" ] && continue
      if brew list "$pkg" &>/dev/null; then
        echo "  ✓ $pkg (已存在)"
      else
        echo "  安装 $pkg..."
        brew install "$pkg" 2>/dev/null || echo "  ⚠️  $pkg 安装跳过"
      fi
    done < "$BACKUP_CONTENT/brew-formulas.txt"
    info "brew formulas 恢复完成"
  fi
fi

# ---------- 6. Claude Code ----------
step "6/8 Claude Code"
if brew list --cask claude-code &>/dev/null; then
  info "Claude Code 已安装"
else
  echo "安装 Claude Code..."
  brew install --cask claude-code
  info "Claude Code 安装完成"
fi

# 恢复配置
if [ -n "${BACKUP_CONTENT:-}" ] && [ -f "$BACKUP_CONTENT/claude/settings.json" ]; then
  mkdir -p "$HOME/.claude"
  cp "$BACKUP_CONTENT/claude/settings.json" "$HOME/.claude/"
  info "Claude Code 配置已恢复"
fi

# ---------- 7. VS Code ----------
step "7/8 Visual Studio Code"
if brew list --cask visual-studio-code &>/dev/null; then
  info "VS Code 已安装"
else
  echo "安装 VS Code..."
  brew install --cask visual-studio-code
  info "VS Code 安装完成"
fi

# 恢复配置和扩展
if [ -n "${BACKUP_CONTENT:-}" ] && [ -d "$BACKUP_CONTENT/vscode" ]; then
  VSCODE_USER="$HOME/Library/Application Support/Code/User"
  mkdir -p "$VSCODE_USER"

  if [ -f "$BACKUP_CONTENT/vscode/settings.json" ]; then
    cp "$BACKUP_CONTENT/vscode/settings.json" "$VSCODE_USER/"
    info "VS Code 设置已恢复"
  fi

  if [ -f "$BACKUP_CONTENT/vscode/keybindings.json" ]; then
    cp "$BACKUP_CONTENT/vscode/keybindings.json" "$VSCODE_USER/"
    info "VS Code 快捷键已恢复"
  fi

  if [ -f "$BACKUP_CONTENT/vscode/extensions.txt" ] && [ -s "$BACKUP_CONTENT/vscode/extensions.txt" ]; then
    echo "安装 VS Code 扩展（$TOTAL 个）..."
    TOTAL=$(wc -l < "$BACKUP_CONTENT/vscode/extensions.txt")
    COUNT=0
    while IFS= read -r ext; do
      [ -z "$ext" ] && continue
      COUNT=$((COUNT + 1))
      echo "  [$COUNT/$TOTAL] $ext"
      code --install-extension "$ext" --force 2>/dev/null || true
    done < "$BACKUP_CONTENT/vscode/extensions.txt"
    info "VS Code 扩展安装完成"
  fi
fi

# ---------- 8. 恢复 ~/Documents/claudeai ----------
step "8/8 恢复项目文件"
PROJECT_DIR="$HOME/Documents/claudeai"
if [ ! -d "$PROJECT_DIR" ]; then
  echo "⚠️  ~/Documents/claudeai 目录不存在"
  echo "  请手动将项目文件夹复制到这个位置"
  echo "  或者运行: mkdir -p $PROJECT_DIR"
else
  info "~/Documents/claudeai 已存在"
fi

# ---------- 最后检查 ----------
step "✅ 安装检查"
echo ""

check() {
  local cmd=$1
  if command -v "$cmd" &>/dev/null; then
    info "$cmd: $($cmd --version 2>&1 | head -1)"
  else
    err "$cmd: 未安装"
  fi
}

check brew
check git
check gh
check node
check python3
check code

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎉 Mac Mini 环境设置完成！${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "👉 接下来:"
echo "   1. 执行 source ~/.zshrc 让 PATH 生效"
echo "   2. 把 ~/Documents/claudeai 项目复制到 Mac Mini"
echo "   3. 如果 android-platform-tools 还需要: brew install --cask android-platform-tools"
echo "   4. 测试 SSH 连接: ssh -T git@github.com"
echo "   5. 打开 Claude Code: claude"
echo ""

# 清理
if [ -n "${BACKUP_DIR:-}" ] && [ -d "$BACKUP_DIR" ]; then
  rm -rf "$BACKUP_DIR"
fi
