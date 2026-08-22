@echo off
:: ============================================================
:: start_cloud.bat — BaGua System Windows Cloud Launcher
:: ============================================================
:: 与 start.bat（本地开发，前后端分离、8888+5173 两个端口）不同，
:: 这个脚本是给"云端 / 服务器"用的：
::   · 监听 0.0.0.0，可被公网 / 内网其他机器访问
::   · 默认端口 9000（明确避开 8000），也可用 PORT 环境变量覆盖
::   · 前端会被 npm run build 打包，然后由 FastAPI 在同一个端口
::     直接托管（main.py 已内置 StaticFiles 挂载 + SPA fallback），
::     所以云端只需要在防火墙/安全组里放行一个端口即可
::   · 前台运行、打印日志，方便配合 NSSM / 计划任务 / Windows 服务
::     包装成后台服务；直接双击运行也可以（用于临时测试）
::
:: 用法（在 cmd.exe 中）：
::   start_cloud.bat                  默认端口 9000
::   set PORT=8080 && start_cloud.bat 自定义端口
::   set SKIP_BUILD=1 && start_cloud.bat   跳过前端重新构建（已有 dist 时加速重启）
:: ============================================================

setlocal EnableDelayedExpansion
chcp 936 >nul 2>&1

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "BACKEND_DIR=%SCRIPT_DIR%"
set "FRONTEND_DIR=%SCRIPT_DIR%\frontend"
set "ENV_FILE=%SCRIPT_DIR%\.env"
set "ENV_EXAMPLE=%SCRIPT_DIR%\.env.example"
set "DIST_INDEX=%FRONTEND_DIR%\dist\index.html"

:: ── 端口 / 主机 ─────────────────────────────────────────────
set "HOST=0.0.0.0"
if "%PORT%"=="" set "PORT=9000"
if "%PORT%"=="8000" (
    echo [WARN] 检测到 PORT=8000，按要求自动改用 9000。
    set "PORT=9000"
)
if "%WORKERS%"=="" set "WORKERS=1"
if "%SKIP_BUILD%"=="" set "SKIP_BUILD=0"

:: 与 start.bat 共用同一套 venv / 依赖哈希缓存目录，避免重复安装
set "VENV_DIR=%USERPROFILE%\.bagua\venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "MARKERS_DIR=%USERPROFILE%\.bagua\markers"
if not exist "%MARKERS_DIR%" mkdir "%MARKERS_DIR%"
set "REQ_MARKER=%MARKERS_DIR%\requirements.hash"
set "PKG_MARKER=%MARKERS_DIR%\package.hash"

call :banner

call :check_python
if errorlevel 1 exit /b 1
call :setup_env
call :install_backend
if errorlevel 1 exit /b 1

if "%SKIP_BUILD%"=="1" (
    echo [ .. ] SKIP_BUILD=1，跳过前端构建（沿用现有 frontend\dist）
) else (
    call :check_node
    if errorlevel 1 exit /b 1
    call :build_frontend
    if errorlevel 1 exit /b 1
)

if not exist "%DIST_INDEX%" (
    echo [ERROR] 前端构建产物不存在：%DIST_INDEX%
    echo         请先正常跑一次（不要加 SKIP_BUILD=1），或手动进入 frontend 执行 npm run build
    exit /b 1
)
echo [ OK ] 前端已就绪：frontend\dist\

echo.
echo   +--------------------------------------------------+
echo   ^|  访问地址   http://^<服务器IP或域名^>:%PORT%/         ^|
echo   ^|  API 文档   http://^<服务器IP或域名^>:%PORT%/docs     ^|
echo   +--------------------------------------------------+
echo.
echo [ .. ] 启动 FastAPI（同时托管 API + 前端静态页面），Ctrl+C 停止 ...
echo ----------------------------------------------------------

:: build_frontend 内部通过 call 执行的辅助 bat 会把当前目录切到 frontend\，
:: call 是同进程执行、目录切换会带回这里，所以启动前必须显式切回项目根目录，
:: 否则 "main:app" 会因为找不到 main.py 而报 ModuleNotFoundError。
cd /d "%BACKEND_DIR%"
"%VENV_PY%" -m uvicorn main:app --host %HOST% --port %PORT% --workers %WORKERS%
goto END

:: ============================================================
:: FUNCTIONS
:: ============================================================

:banner
echo.
echo   +--------------------------------------------+
echo   ^|   BaGua System  Cloud Launcher (Windows)    ^|
echo   ^|   BaZi . LiuYao . QiMen . FengShui          ^|
echo   +--------------------------------------------+
echo.
goto :eof

:check_python
set "PYTHON_EXE="
for %%P in (python python3 py) do (
    if "!PYTHON_EXE!"=="" (
        %%P --version >nul 2>&1
        if not errorlevel 1 set "PYTHON_EXE=%%P"
    )
)
if "!PYTHON_EXE!"=="" (
    echo [ERROR] 未找到 Python 3.10+。
    echo         下载地址: https://www.python.org/downloads/
    echo         安装时务必勾选 "Add Python to PATH"！
    exit /b 1
)
for /f "tokens=2" %%V in ('!PYTHON_EXE! --version 2^>^&1') do echo [ OK ] 已找到 Python %%V  ^(!PYTHON_EXE!^)
exit /b 0

:check_node
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未找到 Node.js 18+。
    echo         下载地址: https://nodejs.org/
    exit /b 1
)
for /f %%V in ('node --version') do echo [ OK ] 已找到 Node %%V
exit /b 0

:setup_env
if not exist "!ENV_EXAMPLE!" goto skip_env_setup
if exist "!ENV_FILE!" goto skip_env_setup
copy /y "!ENV_EXAMPLE!" "!ENV_FILE!" >nul
echo [ OK ] 已从 .env.example 生成 .env，请按需填写 DEEPSEEK_API_KEY 等变量
:skip_env_setup
goto :eof

:install_backend
echo [ .. ] 检查 Python 依赖 ...
cd /d "!BACKEND_DIR!"

if exist "!VENV_DIR!" goto skip_venv_create
echo [ .. ] 创建虚拟环境 !VENV_DIR! ...
"!PYTHON_EXE!" -m venv "!VENV_DIR!"
if not exist "!VENV_PY!" (
    echo [ERROR] 虚拟环境创建失败。请尝试手动运行:
    echo         !PYTHON_EXE! -m venv "!VENV_DIR!"
    exit /b 1
)
echo [ OK ] 虚拟环境创建完成
if exist "!REQ_MARKER!" del /f "!REQ_MARKER!" >nul 2>&1
:skip_venv_create

set "REQ_HASH_NEW="
for /f "skip=1 tokens=*" %%H in ('certutil -hashfile "!BACKEND_DIR!\requirements.txt" MD5 2^>nul') do (
    if "!REQ_HASH_NEW!"=="" set "REQ_HASH_NEW=%%H"
)
set "REQ_HASH_OLD="
if exist "!REQ_MARKER!" set /p REQ_HASH_OLD=<"!REQ_MARKER!"

if "!REQ_HASH_NEW!"=="!REQ_HASH_OLD!" (
    if exist "!VENV_DIR!\Lib\site-packages\uvicorn" (
        echo [ OK ] 后端依赖已是最新
        goto :eof
    )
)

echo [ .. ] 安装 Python 依赖包 ...
"!VENV_PY!" -m pip install --quiet -r "!BACKEND_DIR!\requirements.txt"
if errorlevel 1 (
    echo [ERROR] pip install 失败 — 请检查网络连接
    exit /b 1
)
echo [ OK ] 后端依赖安装完成
echo !REQ_HASH_NEW!>"!REQ_MARKER!"
goto :eof

:build_frontend
echo [ .. ] 检查前端依赖 ...
set "PKG_HASH_NEW="
for /f "skip=1 tokens=*" %%H in ('certutil -hashfile "!FRONTEND_DIR!\package.json" MD5 2^>nul') do (
    if "!PKG_HASH_NEW!"=="" set "PKG_HASH_NEW=%%H"
)
set "PKG_HASH_OLD="
if exist "!PKG_MARKER!" set /p PKG_HASH_OLD=<"!PKG_MARKER!"

if exist "!FRONTEND_DIR!\node_modules" (
    if "!PKG_HASH_NEW!"=="!PKG_HASH_OLD!" (
        echo [ OK ] 前端依赖已是最新，跳过 npm install
        goto build_only
    )
)

echo [ .. ] 安装 Node 依赖包 ...
set "NHELPER=%TEMP%\bagua_cloud_npm_install.bat"
(
    echo @echo off
    echo cd /d "!FRONTEND_DIR!"
    echo npm install
) > "!NHELPER!"
call "!NHELPER!"
if errorlevel 1 (
    echo [ERROR] npm install 失败 — 请检查网络连接
    exit /b 1
)
echo !PKG_HASH_NEW!>"!PKG_MARKER!"

:build_only
echo [ .. ] 构建前端 (npm run build) ...
set "BHELPER=%TEMP%\bagua_cloud_npm_build.bat"
(
    echo @echo off
    echo cd /d "!FRONTEND_DIR!"
    echo npm run build
) > "!BHELPER!"
call "!BHELPER!"
if errorlevel 1 (
    echo [ERROR] 前端构建失败，请检查上方报错信息
    exit /b 1
)
echo [ OK ] 前端构建完成
goto :eof

:END
endlocal
