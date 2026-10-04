import tkinter as tk
from tkinter import scrolledtext
import os
import socket
import getpass

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

def process_command(command, args, output_widget):
    if command is None:
        return True

    expanded_args = [expand_env_vars(arg) for arg in args]

    if command == "exit":
        output_widget.insert(tk.END, "Выход из эмулятора...\n")
        return False

    elif command == "ls":
        output_widget.insert(tk.END, f"ls: команда вызвана с аргументами: {expanded_args}\n")

    elif command == "cd":
        output_widget.insert(tk.END, f"cd: команда вызвана с аргументами: {expanded_args}\n")

    else:
        output_widget.insert(tk.END, f"Ошибка: команда '{command}' не найдена\n")

    return True

def on_enter(event, entry_widget, output_widget):
    user_input = entry_widget.get()
    if not user_input.strip():
        return

    output_widget.insert(tk.END, f"> {user_input}\n")

    command, args = parse_command(user_input)

    should_continue = process_command(command, args, output_widget)

    entry_widget.delete(0, tk.END)
    output_widget.see(tk.END)

    if not should_continue:
        entry_widget.master.destroy()

def main():
    root = tk.Tk()
    
    username = get_username()
    hostname = get_hostname()
    root.title(f"Эмулятор - [{username}@{hostname}]")
    
    root.geometry("700x500")
    
    output_widget = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='normal')
    output_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    
    output_widget.insert(tk.END, "Добро пожаловать в эмулятор оболочки!\n")
    output_widget.insert(tk.END, "Доступные команды: ls, cd, exit\n")
    output_widget.insert(tk.END, "Поддерживается раскрытие переменных окружения (например, $HOME)\n\n")
    
    entry_widget = tk.Entry(root)
    entry_widget.pack(padx=10, pady=(0, 10), fill=tk.X)
    entry_widget.focus_set()
    
    entry_widget.bind("<Return>", lambda event: on_enter(event, entry_widget, output_widget))
    
    root.mainloop()

if __name__ == "__main__":
    main()