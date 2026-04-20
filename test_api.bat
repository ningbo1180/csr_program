@echo off
REM CSR GenAI API 测试脚本 (Windows Batch)

setlocal enabledelayedexpansion

set BASE_URL=http://localhost:8000

echo.
echo =========================================
echo CSR GenAI API 功能测试
echo =========================================

REM 测试 1: Health Check
echo.
echo ^✓ 测试 1: 健康检查
curl -s "%BASE_URL%/health"
echo.

REM 测试 2: 创建项目
echo.
echo ^✓ 测试 2: 创建项目
for /f "delims=" %%A in ('curl -s -X POST "%BASE_URL%/api/projects/" ^
  -H "Content-Type: application/json" ^
  -d "{\"name\": \"Test Project\", \"description\": \"Testing CSR GenAI\"}"') do set PROJECT_RESPONSE=%%A

echo !PROJECT_RESPONSE!

REM 提取项目 ID (需要 jq 或其他 JSON 工具)
REM 如果没有安装，可以手动从响应中获取

echo.
echo 注: 需要手动从上面的项目响应中复制项目 ID 以继续后续测试
echo.

echo =========================================
echo 快速测试命令:
echo =========================================
echo 1. 创建项目:
echo   curl -X POST http://localhost:8000/api/projects/ ^
echo     -H "Content-Type: application/json" ^
echo     -d "{\"name\": \"My Project\"}"
echo.
echo 2. 创建章节 (将 PROJECT_ID 替换为实际 ID):
echo   curl -X POST http://localhost:8000/api/chapters/{PROJECT_ID} ^
echo     -H "Content-Type: application/json" ^
echo     -d "{\"title\": \"Chapter 10.2.6\", \"number\": \"10.2.6\"}"
echo.
echo 3. 查看操作日志:
echo   curl http://localhost:8000/api/logs/{PROJECT_ID}
echo.
echo =========================================

endlocal
