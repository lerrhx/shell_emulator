import tkinter as tk
from tkinter import scrolledtext
import os
import socket
import getpass
import argparse

CONFIG = {'start_script': None}
VFS = {}
current_dir = "/"
VFS_SOURCE_PATH = None

def get_username():
    try:
        return getpass.getuser()
    except Exception:
        return "user"

def get_hostname():
    try:
        return socket.gethostname()
    except Exception:
        return "localhost"

def expand_env_vars(text):
    if not text:
        return text
    return os.path.expandvars(text)

def parse_command(user_input):
    parts = user_input.strip().split()
    if not parts:
        return None, []
    command = parts[0]
    args = parts[1:]
    return command, args

def normalize_path(path):
    if not path.startswith("/"):
        path = os.path.join(current_dir, path)
    path = os.path.normpath(path).replace("\\", "/")
    if not path.startswith("/"):
        path = "/" + path
    return path

def load_vfs(path, output_widget):
    global VFS, VFS_SOURCE_PATH
    VFS.clear()
    VFS_SOURCE_PATH = path
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(',')
                if len(parts) < 2:
                    raise ValueError("Неверный формат строки: " + line)
                item_path = parts[0].strip()
                item_type = parts[1].strip()
                item_content = parts[2].strip() if len(parts) > 2 else ""
                if item_type not in ('dir', 'file'):
                    raise ValueError("Неверный тип: " + item_type)
                VFS[item_path] = {'type': item_type, 'content': item_content}
        output_widget.insert(tk.END, f"VFS успешно загружена из {path}\n")
    except FileNotFoundError:
        output_widget.insert(tk.END, f"Ошибка: файл VFS не найден: {path}\n")
    except Exception as e:
        output_widget.insert(tk.END, f"Ошибка загрузки VFS: {e}\n")

def process_command(command, args, output_widget):
    global current_dir, VFS, VFS_SOURCE_PATH

    if command is None:
        return True

    expanded_args = [expand_env_vars(arg) for arg in args]

    if command == "exit":
        output_widget.insert(tk.END, "Выход из эмулятора...\n")
        return False

    elif command == "conf-dump":
        output_widget.insert(tk.END, "--- Конфигурация ---\n")
        output_widget.insert(tk.END, f"vfs_path = {VFS_SOURCE_PATH}\n")
        output_widget.insert(tk.END, f"start_script = {CONFIG.get('start_script')}\n")
        output_widget.insert(tk.END, "--------------------\n")

    elif command == "vfs-init":
        VFS.clear()
        current_dir = "/"
        if VFS_SOURCE_PATH and os.path.exists(VFS_SOURCE_PATH):
            try:
                os.remove(VFS_SOURCE_PATH)
                output_widget.insert(tk.END, f"Физический файл {VFS_SOURCE_PATH} удалён.\n")
            except Exception as e:
                output_widget.insert(tk.END, f"Не удалось удалить файл: {e}\n")
        VFS_SOURCE_PATH = None
        output_widget.insert(tk.END, "VFS сброшена в состояние по умолчанию.\n")

    elif command == "ls":
        path = normalize_path(expanded_args[0] if expanded_args else current_dir)
        found = False
        for vfs_path in sorted(VFS.keys()):
            if vfs_path == path:
                continue
            if vfs_path.startswith(path.rstrip("/") + "/"):
                relative = vfs_path[len(path.rstrip("/")) + 1:]
                if "/" not in relative:
                    item = VFS[vfs_path]
                    suffix = "/" if item['type'] == 'dir' else ""
                    output_widget.insert(tk.END, f"{relative}{suffix}\n")
                    found = True
        if not found:
            output_widget.insert(tk.END, "Содержимое пусто или путь не найден\n")

    elif command == "cd":
        if not expanded_args:
            output_widget.insert(tk.END, "Ошибка: не указан путь\n")
        else:
            target = normalize_path(expanded_args[0])
            if target in VFS and VFS[target]['type'] == 'dir':
                current_dir = target
                output_widget.insert(tk.END, f"Текущая директория: {current_dir}\n")
            else:
                output_widget.insert(tk.END, f"Ошибка: директория не найдена: {target}\n")

    elif command == "tac":
        if not expanded_args:
            output_widget.insert(tk.END, "Ошибка: не указан файл\n")
        else:
            target = normalize_path(expanded_args[0])
            if target in VFS and VFS[target]['type'] == 'file':
                content = VFS[target]['content']
                lines = content.split("\n")
                for line in reversed(lines):
                    output_widget.insert(tk.END, f"{line}\n")
            else:
                output_widget.insert(tk.END, f"Ошибка: файл не найден: {target}\n")

    elif command == "find":
        if not expanded_args:
            output_widget.insert(tk.END, "Ошибка: не указан шаблон\n")
        else:
            pattern = expanded_args[0]
            found = False
            for vfs_path, item in VFS.items():
                if pattern in vfs_path:
                    suffix = "/" if item['type'] == 'dir' else ""
                    output_widget.insert(tk.END, f"{vfs_path}{suffix}\n")
                    found = True
            if not found:
                output_widget.insert(tk.END, f"Ничего не найдено по шаблону: {pattern}\n")

    elif command == "rmdir":
        if not expanded_args:
            output_widget.insert(tk.END, "Ошибка: не указан путь\n")
        else:
            target = normalize_path(expanded_args[0])
            if target not in VFS or VFS[target]['type'] != 'dir':
                output_widget.insert(tk.END, f"Ошибка: директория не найдена: {target}\n")
            else:
                for vfs_path in VFS:
                    if vfs_path.startswith(target.rstrip("/") + "/"):
                        output_widget.insert(tk.END, f"Ошибка: директория не пуста: {target}\n")
                        break
                else:
                    del VFS[target]
                    output_widget.insert(tk.END, f"Директория удалена: {target}\n")

    else:
        output_widget.insert(tk.END, f"Ошибка: команда '{command}' не найдена\n")

    return True

def run_script(script_path, output_widget):
    if not script_path:
        return
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        output_widget.insert(tk.END, f"Выполнение скрипта: {script_path}\n")
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            output_widget.insert(tk.END, f"> {line}\n")
            command, args = parse_command(line)
            process_command(command, args, output_widget)
        output_widget.insert(tk.END, "Скрипт выполнен.\n")
    except Exception as e:
        output_widget.insert(tk.END, f"Ошибка выполнения скрипта: {e}\n")

def on_enter(event, entry_widget, output_widget):
    user_input = entry_widget.get()
    if not user_input.strip():
        return

    output_widget.insert(tk.END, f"{current_dir}> {user_input}\n")

    command, args = parse_command(user_input)

    should_continue = process_command(command, args, output_widget)

    entry_widget.delete(0, tk.END)
    output_widget.see(tk.END)

    if not should_continue:
        entry_widget.master.destroy()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vfs', type=str, default=None)
    parser.add_argument('--script', type=str, default=None)
    args, unknown = parser.parse_known_args()
    
    CONFIG['start_script'] = args.script

    root = tk.Tk()
    
    username = get_username()
    hostname = get_hostname()
    root.title(f"Эмулятор - [{username}@{hostname}]")
    
    root.geometry("700x500")
    
    output_widget = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='normal')
    output_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    
    output_widget.insert(tk.END, "Добро пожаловать в эмулятор оболочки!\n")
    output_widget.insert(tk.END, "Доступные команды: ls, cd, tac, find, rmdir, exit, conf-dump, vfs-init\n")
    output_widget.insert(tk.END, "Поддерживается раскрытие переменных окружения (например, $HOME)\n\n")
    
    entry_widget = tk.Entry(root)
    entry_widget.pack(padx=10, pady=(0, 10), fill=tk.X)
    entry_widget.focus_set()
    
    entry_widget.bind("<Return>", lambda event: on_enter(event, entry_widget, output_widget))
    
    if args.vfs:
        load_vfs(args.vfs, output_widget)
    
    if CONFIG['start_script']:
        run_script(CONFIG['start_script'], output_widget)
    
    root.mainloop()

if __name__ == "__main__":
    main()
    /empty,dir,