import datetime
import os
import subprocess

version = "2.1.2"
changelog = f"""
## 版本 {version} - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 更新内容
- 优化输入框和按钮布局
- 按钮字体加粗加大
- 输出框字体调大
- 修复若干界面细节
"""

readme_path = "README.md"
log_path = "updatepip.log"

# 只要包含本版本 changelog 标题就不再追加
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
    if f"## 版本 {version}" not in content:
        with open(readme_path, "a", encoding="utf-8") as f:
            f.write(changelog)
else:
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("# 项目更新日志\n" + changelog)

# 日志文件超过 1MB 时自动清理
if os.path.exists(log_path) and os.path.getsize(log_path) > 1024 * 1024:
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("")


def run(cmd):
    print(f"执行: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode


run("git pull --rebase")
run("git add .")
run(f'git commit -m "自动更新代码和changelog"')
run("git push")
