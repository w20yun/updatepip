__version__ = "2.0.0"

import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import threading
import queue
import re
from typing import List, Dict
import os
import urllib.request

LANGS = {
    'zh': {
        'title': 'Python包安装更新工具',
        'input_placeholder': '请输入包名...',
        'btn_install': '直接更新',
        'btn_file': '文件安装',
        'btn_query': '查询',
        'btn_update': '全部更新',
        'menu_file': '文件',
        'menu_exit': '退出',
        'menu_lang': '语言',
        'menu_help': '帮助',
        'menu_about': '关于',
        'about': '作者: w20yun\n版本: V{version}\n文件: pip install.py\n描述: 更新/安装python包',
        'msg_input_required': '请先输入包名！',
        'msg_no_file': '没有选择文件',
        'msg_no_packages': '没有需要升级的包。',
        'msg_getting_list': '获取pip更新列表，请稍等...',
        'msg_getting_update': '正在获取需要更新的包...',
        'msg_all_done': '恭喜！全部升级完成了！',
        'msg_file_read_error': '读取文件失败: {e}',
        'msg_pkg_done': '第 {idx} 个包升级完成',
        'msg_pkg_fail': '升级 {pkg} 失败: {err}',
        'msg_pkg_error': '升级 {pkg} 时发生错误: {err}',
        'msg_pkg_updating': '正在升级第 {idx} 个包: {pkg}',
        'msg_pkg_updating_one': '正在升级 {pkg} ...',
        'msg_pkg_done_one': '{pkg} 升级完成！',
        'msg_pkg_error_one': '升级 {pkg} 时发生错误: {err}',
        'msg_pkg_fail_one': '升级 {pkg} 失败: {err}',
        'msg_need_update_count': '需更新的包数量: {count}',
        'msg_pkg_version': '{name}: 当前{version} → 最新{latest}',
        'msg_update_count': '共需更新 {count} 个包，开始升级...',
        'msg_switch_zh': '切换到中文',
        'msg_switch_en': 'Switch to English',
        'msg_no_update': '没有需要更新的包。',
    },
    'en': {
        'title': 'Python Package Install/Update Tool',
        'input_placeholder': 'Please enter package name...',
        'btn_install': 'Update',
        'btn_file': 'Install from File',
        'btn_query': 'Query',
        'btn_update': 'Update All',
        'menu_file': 'File',
        'menu_exit': 'Exit',
        'menu_lang': 'Language',
        'menu_help': 'Help',
        'menu_about': 'About',
        'about': 'Author: w20yun\nVersion: V{version}\nFile: pip install.py\nDescribe: Update/Install python packages',
        'msg_input_required': 'Please enter a package name!',
        'msg_no_file': 'No file selected',
        'msg_no_packages': 'No packages to update.',
        'msg_getting_list': 'Getting pip update list, please wait...',
        'msg_getting_update': 'Getting packages to update...',
        'msg_all_done': 'All packages updated!',
        'msg_file_read_error': 'File read error: {e}',
        'msg_pkg_done': 'Package {idx} updated',
        'msg_pkg_fail': 'Failed to update {pkg}: {err}',
        'msg_pkg_error': 'Error updating {pkg}: {err}',
        'msg_pkg_updating': 'Updating package {idx}: {pkg}',
        'msg_pkg_updating_one': 'Updating {pkg} ...',
        'msg_pkg_done_one': '{pkg} updated!',
        'msg_pkg_error_one': 'Error updating {pkg}: {err}',
        'msg_pkg_fail_one': 'Failed to update {pkg}: {err}',
        'msg_need_update_count': 'Packages to update: {count}',
        'msg_pkg_version': '{name}: current {version} → latest {latest}',
        'msg_update_count': '{count} packages to update, starting...',
        'msg_switch_zh': '切换到中文',
        'msg_switch_en': 'Switch to English',
        'msg_no_update': 'No packages to update.',
    }
}

class PackageInstallerGUI:
    def __init__(self):
        self.lang = 'zh'
        self.root = tk.Tk()
        self.root.title(self._t('title'))

        # 设置窗口图标，支持用户更换app.ico或app.png
        icon_path_ico = os.path.join(os.path.dirname(__file__), 'app.ico')
        icon_path_png = os.path.join(os.path.dirname(__file__), 'app.png')
        if os.path.exists(icon_path_ico):
            self.root.iconbitmap(icon_path_ico)
        elif os.path.exists(icon_path_png):
            try:
                from tkinter import PhotoImage
                self.root.iconphoto(True, PhotoImage(file=icon_path_png))
            except Exception:
                pass  # PNG不支持时忽略

        width, height = 500, 350
        screenwidth = self.root.winfo_screenwidth()
        screenheight = self.root.winfo_screenheight()
        alignstr = f'{width}x{height}+{int((screenwidth-width)/2)}+{int((screenheight-height)/2)}'
        self.root.geometry(alignstr)
        self.root.minsize(width, height)
        self.root.resizable(width=False, height=False)

        self.msg_queue = queue.Queue()
        self._build_widgets()
        self._build_menu()
        self.root.after(100, self._process_queue)
        self._bind_shortcuts()

    def _t(self, key, **kwargs):
        return LANGS[self.lang][key].format(**kwargs)

    def _build_menu(self):
        self.menubar = tk.Menu(self.root)
        self.menu_file = tk.Menu(self.menubar, tearoff=0)
        self.menu_file.add_command(label=self._t('menu_exit'), command=self.root.quit)
        self.menubar.add_cascade(label=self._t('menu_file'), menu=self.menu_file)

        self.lang_menu = tk.Menu(self.menubar, tearoff=0)
        self.lang_menu.add_command(label='中文', command=lambda: self._set_language('zh'))
        self.lang_menu.add_command(label='English', command=lambda: self._set_language('en'))
        self.menubar.add_cascade(label=self._t('menu_lang'), menu=self.lang_menu)

        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.help_menu.add_command(label=self._t('menu_about'), command=self._show_about)
        self.help_menu.add_command(label='检查更新', command=self._check_update)
        self.menubar.add_cascade(label=self._t('menu_help'), menu=self.help_menu)
        self.root.config(menu=self.menubar)

    def _build_widgets(self):
        # 设置grid权重，让输出框和滚动条能自动填充
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=0)
        self.root.grid_columnconfigure(2, weight=0)
        self.root.grid_columnconfigure(3, weight=0)

        self.entry_package = tk.Entry(self.root, font=("Arial", 12), width=25, fg='grey')
        self.entry_package.insert(0, self._t('input_placeholder'))
        self.entry_package.bind('<FocusIn>', self._clear_entry_placeholder)
        self.entry_package.bind('<FocusOut>', self._restore_entry_placeholder)
        self.entry_package.grid(row=0, column=0, padx=8, pady=8, sticky='w')

        self.btn_install = tk.Button(self.root, text=self._t('btn_install'), width=10, command=self._install_package_thread)
        self.btn_install.grid(row=0, column=1, padx=5, pady=8)
        self.btn_file = tk.Button(self.root, text=self._t('btn_file'), width=12, command=self._file_install_thread)
        self.btn_file.grid(row=0, column=2, padx=5, pady=8)
        self.btn_query = tk.Button(self.root, text=self._t('btn_query'), width=10, command=self._pip_updatelist_thread)
        self.btn_query.grid(row=1, column=1, padx=5, pady=8)
        self.btn_update = tk.Button(self.root, text=self._t('btn_update'), width=12, command=self._update_all_thread)
        self.btn_update.grid(row=1, column=2, padx=5, pady=8)

        self.text_output = tk.Text(self.root, font=("Consolas", 10), width=60, height=15, wrap='word')
        self.text_output.grid(row=2, column=0, columnspan=3, padx=8, pady=8, sticky='nsew')
        scroll = tk.Scrollbar(self.root, command=self.text_output.yview)
        scroll.grid(row=2, column=3, sticky='ns', pady=8)
        self.text_output.config(yscrollcommand=scroll.set)

        self._add_context_menu(self.entry_package)
        self._add_context_menu(self.text_output, is_text=True)

    def _refresh_texts(self):
        self.root.title(self._t('title'))
        self.btn_install.config(text=self._t('btn_install'))
        self.btn_file.config(text=self._t('btn_file'))
        self.btn_query.config(text=self._t('btn_query'))
        self.btn_update.config(text=self._t('btn_update'))
        # 重新构建菜单栏以刷新顶层菜单的label
        self._build_menu()
        # 输入框提示
        if not self.entry_package.get() or self.entry_package.get() == LANGS['zh']['input_placeholder'] or self.entry_package.get() == LANGS['en']['input_placeholder']:
            self.entry_package.delete(0, tk.END)
            self.entry_package.insert(0, self._t('input_placeholder'))
            self.entry_package.config(fg='grey')

    def _set_language(self, lang):
        self.lang = lang
        self._refresh_texts()
        self._add_message(self._t('msg_switch_zh') if lang == 'zh' else self._t('msg_switch_en'))

    def _add_context_menu(self, widget, is_text=False):
        menu = tk.Menu(widget, tearoff=0)
        menu.add_command(label='复制', command=lambda: widget.event_generate('<<Copy>>'))
        if is_text:
            menu.add_command(label='全选', command=lambda: widget.event_generate('<<SelectAll>>'))
        else:
            menu.add_command(label='剪切', command=lambda: widget.event_generate('<<Cut>>'))
            menu.add_command(label='粘贴', command=lambda: widget.event_generate('<<Paste>>'))
        widget.bind('<Button-3>', lambda e: menu.tk_popup(e.x_root, e.y_root))

    def _bind_shortcuts(self):
        self.root.bind_all('<Control-q>', lambda e: self.root.quit())
        self.root.bind_all('<Control-Q>', lambda e: self.root.quit())

    def _clear_entry_placeholder(self, event):
        if self.entry_package.get() == LANGS['zh']['input_placeholder'] or self.entry_package.get() == LANGS['en']['input_placeholder']:
            self.entry_package.delete(0, tk.END)
            self.entry_package.config(fg='black')

    def _restore_entry_placeholder(self, event):
        if not self.entry_package.get():
            self.entry_package.insert(0, self._t('input_placeholder'))
            self.entry_package.config(fg='grey')

    def _show_about(self):
        messagebox.showinfo(self._t('menu_about'), self._t('about', version=__version__))

    def _add_message(self, message: str):
        self.msg_queue.put(message)

    def _process_queue(self):
        while not self.msg_queue.empty():
            msg = self.msg_queue.get()
            self.text_output.insert('1.0', msg + '\n')
            self.text_output.yview_moveto(0)
        self.root.after(100, self._process_queue)

    def _install_package_thread(self):
        package = self.entry_package.get().strip()
        if not package or package == LANGS['zh']['input_placeholder'] or package == LANGS['en']['input_placeholder']:
            self._add_message(self._t('msg_input_required'))
            return
        threading.Thread(target=self._install_package, args=(package,), daemon=True).start()

    def _install_package(self, package: str):
        self._add_message(self._t('msg_pkg_updating_one', pkg=package))
        try:
            subprocess.run(['pip', 'install', '--upgrade', package], check=True, capture_output=True, text=True)
            self._add_message(self._t('msg_pkg_done_one', pkg=package))
        except subprocess.CalledProcessError as e:
            self._add_message(self._t('msg_pkg_fail_one', pkg=package, err=e.stderr.strip() if e.stderr else e))
        except Exception as e:
            self._add_message(self._t('msg_pkg_error_one', pkg=package, err=e))

    def _file_install_thread(self):
        threading.Thread(target=self._file_install, daemon=True).start()

    def _file_install(self):
        self.text_output.delete('1.0', tk.END)
        file_path = filedialog.askopenfilename(title=self._t('btn_file'), filetypes=[('Text Files', '*.txt'), ('All Files', '*.*')])
        if not file_path:
            self._add_message(self._t('msg_no_file'))
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                packages = [line.strip() for line in f if line.strip()]
            if not packages:
                self._add_message(self._t('msg_no_packages'))
                return
            self._add_message(f"{self._t('msg_update_count', count=len(packages))}")
            for idx, package in enumerate(packages, 1):
                self._add_message(self._t('msg_pkg_updating', idx=idx, pkg=package))
                try:
                    subprocess.run(['pip', 'install', '--upgrade', package], check=True, capture_output=True, text=True)
                    self._add_message(self._t('msg_pkg_done', idx=idx))
                except subprocess.CalledProcessError as e:
                    self._add_message(self._t('msg_pkg_fail', pkg=package, err=e.stderr.strip() if e.stderr else e))
                except Exception as e:
                    self._add_message(self._t('msg_pkg_error', pkg=package, err=e))
            self._add_message(self._t('msg_all_done'))
        except Exception as e:
            self._add_message(self._t('msg_file_read_error', e=e))

    def _pip_updatelist_thread(self):
        threading.Thread(target=self._pip_updatelist, daemon=True).start()

    def _pip_updatelist(self):
        self._add_message(self._t('msg_getting_list'))
        try:
            result = subprocess.run(['pip', 'list', '--outdated'], capture_output=True, text=True, check=True)
            packages = self._parse_packages(result.stdout)
            self._add_message(self._t('msg_need_update_count', count=len(packages)))
            for pkg in packages:
                self._add_message(self._t('msg_pkg_version', name=pkg['name'], version=pkg['version'], latest=pkg['latest']))
        except subprocess.CalledProcessError as e:
            self._add_message(self._t('msg_pkg_fail', pkg='pip', err=e.stderr.strip() if e.stderr else e))
        except Exception as e:
            self._add_message(self._t('msg_pkg_error', pkg='pip', err=e))

    def _update_all_thread(self):
        threading.Thread(target=self._update_all, daemon=True).start()

    def _update_all(self):
        self._add_message(self._t('msg_getting_update'))
        try:
            result = subprocess.run(['pip', 'list', '--outdated'], capture_output=True, text=True, check=True)
            packages = self._parse_packages(result.stdout)
            if not packages:
                self._add_message(self._t('msg_no_update'))
                return
            self._add_message(self._t('msg_update_count', count=len(packages)))
            for idx, pkg in enumerate(packages, 1):
                name = pkg['name']
                self._add_message(self._t('msg_pkg_updating', idx=idx, pkg=name))
                try:
                    subprocess.run(['pip', 'install', '--upgrade', name], check=True, capture_output=True, text=True)
                    self._add_message(self._t('msg_pkg_done', idx=idx))
                except subprocess.CalledProcessError as e:
                    self._add_message(self._t('msg_pkg_fail', pkg=name, err=e.stderr.strip() if e.stderr else e))
                except Exception as e:
                    self._add_message(self._t('msg_pkg_error', pkg=name, err=e))
            self._add_message(self._t('msg_all_done'))
        except subprocess.CalledProcessError as e:
            self._add_message(self._t('msg_pkg_fail', pkg='pip', err=e.stderr.strip() if e.stderr else e))
        except Exception as e:
            self._add_message(self._t('msg_pkg_error', pkg='pip', err=e))

    @staticmethod
    def _parse_packages(text: str) -> List[Dict[str, str]]:
        pattern = r"^([\w\.-]+)\s+([\d\.]+(?:[a-z]+)?)\s+([\d\.]+(?:[a-z]+)?)\s+(\w+)"
        return [
            {
                'name': match.group(1),
                'version': match.group(2),
                'latest': match.group(3),
                'type': match.group(4)
            }
            for line in text.split('\n')
            if (match := re.match(pattern, line.strip()))
        ]

    def _check_update(self):
        # 请将下面两个URL替换为你自己的服务器地址
        remote_version_url = 'https://your-server.com/version.txt'  # 远程version.txt地址
        remote_py_url = 'https://your-server.com/pip%20install.py'  # 远程pip install.py地址
        self._add_message('正在检查更新...')
        def do_update():
            remote_version = self._get_remote_version(remote_version_url)
            if not remote_version:
                self._add_message('无法获取远程版本号')
                return
            if self._check_version_newer(__version__, remote_version):
                if messagebox.askyesno('更新', f'检测到新版本V{remote_version}，是否下载并自动替换？'):
                    save_path = os.path.abspath(__file__)
                    if self._download_file(remote_py_url, save_path):
                        messagebox.showinfo('更新', '更新成功，请重启程序！')
                        self.root.quit()
                    else:
                        messagebox.showerror('更新', '下载失败！')
            else:
                self._add_message('当前已是最新版')
        threading.Thread(target=do_update, daemon=True).start()

    def _get_remote_version(self, url):
        try:
            with urllib.request.urlopen(url, timeout=5) as f:
                return f.read().decode().strip()
        except Exception as e:
            return None

    def _check_version_newer(self, local_version, remote_version):
        def parse(v): return [int(x) for x in v.split('.')]
        try:
            return parse(remote_version) > parse(local_version)
        except Exception:
            return False

    def _download_file(self, url, save_path):
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                data = response.read()
            with open(save_path, 'wb') as f:
                f.write(data)
            return True
        except Exception as e:
            return False

if __name__ == '__main__':
    gui = PackageInstallerGUI()
    gui.root.mainloop()