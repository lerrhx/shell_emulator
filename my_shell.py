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
        output_widget.insert(tk.END, f"ls: команда вызвана с аргументами: {expanded_args}\n")

    elif command == "cd":
        output_widget.insert(tk.END, f"cd: команда вызвана с аргументами: {expanded_args}\n")

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
    global current_dir
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
    global VFS_SOURCE_PATH
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
    output_widget.insert(tk.END, "Доступные команды: ls, cd, exit, conf-dump, vfs-init\n")
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