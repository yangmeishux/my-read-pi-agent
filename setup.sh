# 读书智能体 - 快速开始脚本

#!/bin/bash
set -e

echo "=== 读书智能体安装向导 ==="
echo ""

# 检查 Node 版本
echo "1. 检查 Node.js 版本..."
NODE_VERSION=$(node -v 2>/dev/null | sed 's/v//' | cut -d. -f1)
if [ -z "$NODE_VERSION" ] || [ "$NODE_VERSION" -lt 22 ]; then
    echo "❌ Node.js 版本过低（需要 >= 22.19.0）"
    echo "   当前版本: $(node -v 2>/dev/null || echo '未安装')"
    echo ""
    echo "请升级 Node.js："
    echo "  brew install node@22"
    echo "  或使用 nvm: nvm install 22"
    exit 1
fi
echo "✓ Node.js $(node -v)"

# 检查 Python
echo ""
echo "2. 检查 Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi
echo "✓ Python $(python3 --version)"

# 安装 Node 依赖
echo ""
echo "3. 安装 Node 依赖..."
npm install

# 安装 Python 依赖
echo ""
echo "4. 安装 Python 依赖..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt

# 配置 .env
echo ""
echo "5. 配置环境变量..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ 已创建 .env 文件"
    echo ""
    echo "请编辑 .env 并填入你的 DashScope API Key："
    echo "  DASHSCOPE_API_KEY=sk-xxx"
    echo ""
    echo "获取 Key: https://dashscope.console.aliyun.com/"
else
    echo "✓ .env 已存在"
fi

# 初始化 Pi Agent
echo ""
echo "6. 初始化 Pi Agent..."
npx pi install -l . --approve

echo ""
echo "=== 安装完成 ==="
echo ""
echo "下一步："
echo "  1. 编辑 .env 填入 DashScope API Key"
echo "  2. 起一本新书："
echo "     python scripts/new_book.py '书名' --author '作者' --file ~/Downloads/book.pdf"
echo "     python scripts/ingest.py ~/Downloads/book.pdf"
echo "  3. 启动 Pi Agent："
echo "     npm run pi"
echo "  4. 在 Pi 对话中执行："
echo "     /skill:book-summary"
echo "     /skill:book-insights"
echo "     /skill:book-review-search"
echo "     /skill:reading-report"
echo ""
echo "完整文档: docs/guides/使用指南.md"
