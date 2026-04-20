#!/bin/bash

# CSR GenAI API 测试脚本
# 测试所有核心 API 端点

BASE_URL="http://localhost:8000"

echo "========================================="
echo "CSR GenAI API 功能测试"
echo "========================================="

# 测试 1: Health Check
echo ""
echo "✓ 测试 1: 健康检查"
curl -s "$BASE_URL/health" | python -m json.tool

# 测试 2: 创建项目
echo ""
echo "✓ 测试 2: 创建项目"
PROJECT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/projects/" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Project", "description": "Testing CSR GenAI"}')

echo "$PROJECT_RESPONSE" | python -m json.tool

PROJECT_ID=$(echo "$PROJECT_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
  echo "⚠️  项目创建失败，无法继续测试"
  exit 1
fi

echo ""
echo "✓ 项目 ID: $PROJECT_ID"

# 测试 3: 获取项目
echo ""
echo "✓ 测试 3: 获取项目"
curl -s "$BASE_URL/api/projects/$PROJECT_ID" | python -m json.tool

# 测试 4: 列出项目
echo ""
echo "✓ 测试 4: 列出项目"
curl -s "$BASE_URL/api/projects/" | python -m json.tool

# 测试 5: 创建章节
echo ""
echo "✓ 测试 5: 创建章节 (10.2.6)"
CHAPTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/chapters/$PROJECT_ID" \
  -H "Content-Type: application/json" \
  -d '{"title": "新增章节", "number": "10.2.6", "content": "这是一个新增的章节"}')

echo "$CHAPTER_RESPONSE" | python -m json.tool

CHAPTER_ID=$(echo "$CHAPTER_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)

# 测试 6: 获取章节树
echo ""
echo "✓ 测试 6: 获取章节树"
curl -s "$BASE_URL/api/chapters/$PROJECT_ID/tree" | python -m json.tool

# 测试 7: 更新章节
if [ -n "$CHAPTER_ID" ]; then
  echo ""
  echo "✓ 测试 7: 更新章节标题"
  curl -s -X PUT "$BASE_URL/api/chapters/$PROJECT_ID/$CHAPTER_ID" \
    -H "Content-Type: application/json" \
    -d '{"title": "修改后的章节标题"}' | python -m json.tool
fi

# 测试 8: 列出操作日志
echo ""
echo "✓ 测试 8: 列出操作日志"
curl -s "$BASE_URL/api/logs/$PROJECT_ID?limit=10" | python -m json.tool

# 测试 9: 日志摘要
echo ""
echo "✓ 测试 9: 日志摘要"
curl -s "$BASE_URL/api/logs/$PROJECT_ID/summary?days=7" | python -m json.tool

echo ""
echo "========================================="
echo "✓ 所有基础 API 测试完成"
echo "========================================="
