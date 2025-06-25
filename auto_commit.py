import datetime
import os
import subprocess

# 1. 生成 changelog 内容（可根据实际情况修改）
changelog = f"""
## 版本 2.1.0 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 更新内容
- 优化输入框和按钮布局
- 按钮字体加粗加大
- 输出框字体调大
- 修复若干界面细节
"""

readme_path = "README.md"

# 2. 追加 changelog 到 README.md（如已存在则不重复追加）
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
    if changelog.strip() not in content:
        with open(readme_path, "a", encoding="utf-8") as f:
            f.write(changelog)
else:
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("# 项目更新日志\n" + changelog)

# 3. 自动执行 git 命令
def run(cmd):
    print(f"执行: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode

run("git add .")
run(f'git commit -m "自动更新代码和changelog"')
run("git push")