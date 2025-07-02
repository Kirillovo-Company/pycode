import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import os
import sys
import subprocess
import platform
import json
import webbrowser
import re
from tkinter.font import Font

class PythonCodeEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("PyCode 1.2")
        self.root.geometry("1200x800")
        
        # Инициализация переменных
        self.current_file = None
        self.dark_mode = False
        self.project_folder = None
        self.process = None
        self.console_process = None
        self.languages = {}
        self.current_language = "en"
        self.syntax_colors = {}
        self.settings = {
            "language": "en",
            "dark_mode": False,
            "font_size": 12,
            "font_family": "Consolas"
        }
        
        # Настройка виртуального окружения
        self.venv_name = "pyvenv"
        self.venv_path = os.path.abspath(os.path.join(os.getcwd(), self.venv_name))
        self.venv_active = False
        
        # GitHub репозиторий для проверки обновлений
        self.github_repo = "https://github.com/yourusername/yourrepository"
        
        # Сначала загружаем языки, цвета и настройки
        self.load_languages()
        self.load_syntax_colors()
        self.load_settings()
        
        # Затем создаем интерфейс
        self.setup_ui()
        
        # Затем настраиваем виртуальное окружение
        self.init_venv()
    
    def load_languages(self):
        """Загружает языковые файлы из папки languages"""
        lang_dir = os.path.join(os.path.dirname(__file__), "languages")
        if not os.path.exists(lang_dir):
            os.makedirs(lang_dir)
        
        # Загружаем все JSON файлы из папки languages
        for file in os.listdir(lang_dir):
            if file.endswith(".json"):
                lang_code = file.split(".")[0]
                try:
                    with open(os.path.join(lang_dir, file), "r", encoding="utf-8") as f:
                        self.languages[lang_code] = json.load(f)
                except Exception as e:
                    print(f"Error loading language {lang_code}: {str(e)}")
        
        # Если нет языков, создаем английский по умолчанию
        if not self.languages:
            self.languages["en"] = {
                "file": "File",
                "edit": "Edit",
                "view": "View",
                "run": "Run",
                "settings": "Settings",
                "new": "New",
                "open": "Open",
                "save": "Save",
                "exit": "Exit",
                "dark_mode": "Dark Mode",
                "language": "Language",
                "settings_title": "Settings",
                "check_updates": "Check for Updates",
                "open_folder": "Open Folder",
                "save_as": "Save As",
                "about": "About",
                "settings_saved": "Settings saved successfully",
                "ready": "Ready",
                "python_code_editor": "Python Code Editor",
                "features": "Features",
                "syntax_highlighting": "Syntax highlighting",
                "project_work": "Project work",
                "virtual_environment": "Virtual environment",
                "run_code": "Run code",
                "dark_light_mode": "Dark/light mode",
                "builtin_console": "Built-in console with pip support",
                "author": "Author",
                "version": "Version",
                "cancel": "Cancel",
                "undo": "Undo",
                "redo": "Redo",
                "cut": "Cut",
                "copy": "Copy",
                "paste": "Paste",
                "select_all": "Select All",
                "refresh_file_tree": "Refresh File Tree",
                "run_python": "Run Python Code",
                "stop_execution": "Stop Execution",
                "activate_venv": "Activate venv",
                "new_file_created": "New file created",
                "file_opened": "File opened",
                "file_open_error": "Failed to open file",
                "folder_opened": "Folder opened",
                "file_saved": "File saved",
                "file_save_error": "Failed to save file",
                "no_code_to_execute": "No code to execute",
                "temp_file_error": "Failed to create temp file",
                "running_code_with": "Running code with",
                "executing_code": "Executing code...",
                "error": "Error",
                "execution_completed": "Execution completed",
                "output_read_error": "Error reading output",
                "execution_stopped": "Execution stopped",
                "stop_process_error": "Failed to stop process",
                "file_tree_updated": "File tree updated",
                "warning": "Warning",
                "open_folder_first": "Please open folder first",
                "enter_file_name": "Enter file name:",
                "enter_folder_name": "Enter folder name:",
                "confirmation": "Confirmation",
                "confirm_delete": "Are you sure you want to delete",
                "file_create_error": "Failed to create file",
                "folder_create_error": "Failed to create folder",
                "delete_error": "Failed to delete",
                "confirm_exit": "Are you sure you want to exit?"
            }
    
    def load_syntax_colors(self):
        """Загружает цвета подсветки синтаксиса из файла"""
        colors_path = os.path.join(os.path.dirname(__file__), "colors.json")
        default_colors = {
            "keywords": {"foreground": "blue", "font": "bold"},
            "strings": {"foreground": "green"},
            "comments": {"foreground": "gray", "font": "italic"},
            "numbers": {"foreground": "purple"},
            "functions": {"foreground": "dark blue"},
            "builtins": {"foreground": "dark cyan"}
        }
        
        if os.path.exists(colors_path):
            try:
                with open(colors_path, "r", encoding="utf-8") as f:
                    self.syntax_colors = json.load(f)
            except Exception as e:
                print(f"Error loading colors: {str(e)}")
                self.syntax_colors = default_colors
        else:
            # Создаем файл с цветами по умолчанию
            self.syntax_colors = default_colors
            try:
                with open(colors_path, "w", encoding="utf-8") as f:
                    json.dump(default_colors, f, indent=4)
            except Exception as e:
                print(f"Error creating colors file: {str(e)}")
    
    def setup_syntax_highlighting(self):
        """Настраивает подсветку синтаксиса"""
        # Очищаем все существующие теги
        for tag in self.text_editor.tag_names():
            self.text_editor.tag_remove(tag, "1.0", "end")
        
        # Добавляем теги с настройками из colors.json
        for tag_name, tag_config in self.syntax_colors.items():
            self.text_editor.tag_configure(tag_name, **tag_config)
        
        # Применяем подсветку
        self.highlight_syntax()
    
    def highlight_syntax(self, event=None):
        """Применяет подсветку синтаксиса к коду"""
        if not self.current_file or not self.current_file.endswith(".py"):
            return
        
        # Удаляем предыдущую подсветку
        for tag in self.text_editor.tag_names():
            self.text_editor.tag_remove(tag, "1.0", "end")
        
        # Получаем весь текст
        code = self.text_editor.get("1.0", "end-1c")
        
        # Шаблоны для подсветки
        patterns = {
            "keywords": r"\b(and|as|assert|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b",
            "strings": r"(\"\"\".*?\"\"\"|\'\'\'.*?\'\'\'|\".*?\"|\'.*?\')",
            "comments": r"#.*?$",
            "numbers": r"\b\d+\.?\d*\b",
            "functions": r"\bdef\s+(\w+)\s*\(",
            "builtins": r"\b(print|len|range|str|int|float|list|dict|set|tuple|bool|type|isinstance|super|__init__)\b"
        }
        
        # Применяем подсветку для каждого типа
        for tag_name, pattern in patterns.items():
            for match in re.finditer(pattern, code, re.MULTILINE|re.DOTALL):
                start = f"1.0 + {match.start()}c"
                end = f"1.0 + {match.end()}c"
                self.text_editor.tag_add(tag_name, start, end)
    
    def load_settings(self):
        """Загружает настройки из файла"""
        settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    self.settings.update(json.load(f))
                    self.current_language = self.settings.get("language", "en")
                    self.dark_mode = self.settings.get("dark_mode", False)
            except Exception as e:
                print(f"Error loading settings: {str(e)}")
    
    def save_settings(self):
        """Сохраняет настройки в файл"""
        settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
        try:
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {str(e)}")
    
    def tr(self, key):
        """Возвращает перевод для указанного ключа"""
        lang = self.languages.get(self.current_language, {})
        return lang.get(key, key)
    
    def setup_ui(self):
        """Инициализация пользовательского интерфейса"""
        # Настройка стилей
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TButton", padding=6, relief="flat", background="#f0f0f0")
        self.style.map("TButton", background=[("active", "#e0e0e0")])
        self.style.configure("Treeview", font=('Segoe UI', 10))
        
        self.create_menu()
        self.create_toolbar()
        self.create_main_panels()
        self.create_status_bar()
        self.setup_console()
        
        # Применяем настройки
        if self.dark_mode:
            self.toggle_dark_mode()
        
        # Настраиваем подсветку синтаксиса
        self.setup_syntax_highlighting()
        
        # Привязываем подсветку к изменениям текста
        self.text_editor.bind("<KeyRelease>", self.highlight_syntax)
    
    def create_menu(self):
        """Создание меню приложения"""
        menubar = tk.Menu(self.root)
        
        # Меню "Файл"
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label=self.tr("new"), command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label=self.tr("open"), command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label=self.tr("open_folder"), command=self.open_folder, accelerator="Ctrl+K Ctrl+O")
        file_menu.add_command(label=self.tr("save"), command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label=self.tr("save_as"), command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label=self.tr("settings"), command=self.show_settings)
        file_menu.add_command(label=self.tr("check_updates"), command=self.check_for_updates)
        file_menu.add_separator()
        file_menu.add_command(label=self.tr("about"), command=self.show_about)
        file_menu.add_command(label=self.tr("exit"), command=self.exit_app)
        menubar.add_cascade(label=self.tr("file"), menu=file_menu)
        
        # Меню "Правка"
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label=self.tr("undo"), command=lambda: self.text_editor.edit_undo(), accelerator="Ctrl+Z")
        edit_menu.add_command(label=self.tr("redo"), command=lambda: self.text_editor.edit_redo(), accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label=self.tr("cut"), command=lambda: self.text_editor.event_generate("<<Cut>>"), accelerator="Ctrl+X")
        edit_menu.add_command(label=self.tr("copy"), command=lambda: self.text_editor.event_generate("<<Copy>>"), accelerator="Ctrl+C")
        edit_menu.add_command(label=self.tr("paste"), command=lambda: self.text_editor.event_generate("<<Paste>>"), accelerator="Ctrl+V")
        edit_menu.add_command(label=self.tr("select_all"), command=lambda: self.text_editor.tag_add("sel", "1.0", "end"), accelerator="Ctrl+A")
        menubar.add_cascade(label=self.tr("edit"), menu=edit_menu)
        
        # Меню "Вид"
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_checkbutton(label=self.tr("dark_mode"), command=self.toggle_dark_mode, variable=tk.BooleanVar(value=self.dark_mode))
        view_menu.add_command(label=self.tr("refresh_file_tree"), command=self.refresh_file_tree)
        menubar.add_cascade(label=self.tr("view"), menu=view_menu)
        
        # Меню "Запуск"
        run_menu = tk.Menu(menubar, tearoff=0)
        run_menu.add_command(label=self.tr("run_python"), command=self.run_python_code, accelerator="F5")
        run_menu.add_command(label=self.tr("stop_execution"), command=self.stop_execution, accelerator="F6")
        run_menu.add_separator()
        run_menu.add_command(label=self.tr("activate_venv"), command=self.activate_venv_manually)
        menubar.add_cascade(label=self.tr("run"), menu=run_menu)
        
        self.root.config(menu=menubar)
        
        # Горячие клавиши
        self.root.bind_all("<Control-n>", lambda event: self.new_file())
        self.root.bind_all("<Control-o>", lambda event: self.open_file())
        self.root.bind_all("<Control-s>", lambda event: self.save_file())
        self.root.bind_all("<F5>", lambda event: self.run_python_code())
        self.root.bind_all("<F6>", lambda event: self.stop_execution())
        self.root.bind_all("<Control-k><Control-o>", lambda event: self.open_folder())
    
    def check_for_updates(self):
        """Проверяет обновления, открывая страницу GitHub"""
        try:
            webbrowser.open(self.github_repo)
            self.status_bar.config(text=self.tr("check_updates") + ": " + self.github_repo)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open GitHub: {str(e)}")
    
    def show_settings(self):
        """Показывает окно настроек"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title(self.tr("settings_title"))
        settings_window.geometry("400x300")
        settings_window.resizable(False, False)
        
        # Язык
        lang_label = ttk.Label(settings_window, text=self.tr("language") + ":")
        lang_label.pack(pady=(10, 0), padx=10, anchor="w")
        
        lang_var = tk.StringVar(value=self.current_language)
        lang_combobox = ttk.Combobox(settings_window, textvariable=lang_var, state="readonly")
        lang_combobox['values'] = list(self.languages.keys())
        lang_combobox.pack(pady=5, padx=10, fill=tk.X)
        
        # Темный режим
        dark_mode_var = tk.BooleanVar(value=self.dark_mode)
        dark_mode_check = ttk.Checkbutton(
            settings_window, 
            text=self.tr("dark_mode"), 
            variable=dark_mode_var
        )
        dark_mode_check.pack(pady=5, padx=10, anchor="w")
        
        # Кнопки
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(pady=20, fill=tk.X, padx=10)
        
        ttk.Button(
            button_frame, 
            text=self.tr("save"), 
            command=lambda: self.save_settings_values(
                lang_var.get(),
                dark_mode_var.get(),
                settings_window
            )
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame, 
            text=self.tr("cancel"), 
            command=settings_window.destroy
        ).pack(side=tk.RIGHT, padx=5)
    
    def save_settings_values(self, language, dark_mode, window):
        """Сохраняет настройки и применяет их"""
        self.current_language = language
        self.settings["language"] = language
        
        if self.dark_mode != dark_mode:
            self.dark_mode = dark_mode
            self.settings["dark_mode"] = dark_mode
            self.toggle_dark_mode()
        
        self.save_settings()
        window.destroy()
        messagebox.showinfo(self.tr("settings_title"), self.tr("settings_saved"))
        
        # Обновляем интерфейс с новым языком
        self.update_ui_language()
    
    def update_ui_language(self):
        """Обновляет язык интерфейса"""
        # Здесь нужно обновить все тексты в интерфейсе
        # В реальном приложении нужно реализовать более сложную систему
        self.update_title()
        self.status_bar.config(text=self.tr("ready"))
    
    def create_toolbar(self):
        """Создание панели инструментов"""
        toolbar = ttk.Frame(self.root, padding=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Кнопки панели инструментов
        ttk.Button(toolbar, text=self.tr("new"), command=self.new_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text=self.tr("open"), command=self.open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text=self.tr("open_folder"), command=self.open_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text=self.tr("save"), command=self.save_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text=self.tr("run_python"), command=self.run_python_code).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text=self.tr("stop_execution"), command=self.stop_execution).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        ttk.Button(toolbar, text=self.tr("dark_mode"), command=self.toggle_dark_mode).pack(side=tk.LEFT, padx=2)
        
        self.venv_btn = ttk.Button(toolbar, text=f"Venv: {'ON' if self.venv_active else 'OFF'}", 
                                 command=self.toggle_venv_status)
        self.venv_btn.pack(side=tk.LEFT, padx=2)
    
    def create_main_panels(self):
        """Создание основных панелей интерфейса"""
        main_panel = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_panel.pack(fill=tk.BOTH, expand=True)
        
        # Левая панель - дерево файлов
        self.left_panel = ttk.Frame(main_panel, width=200)
        main_panel.add(self.left_panel, weight=1)
        
        self.file_tree = ttk.Treeview(self.left_panel)
        self.file_tree.heading("#0", text=self.tr("files"), anchor=tk.W)
        
        tree_scroll = ttk.Scrollbar(self.left_panel, orient="vertical", command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=tree_scroll.set)
        
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_tree.pack(fill=tk.BOTH, expand=True)
        self.file_tree.bind("<Double-1>", self.on_file_double_click)
        
        # Правая панель - редактор и вывод
        right_panel = ttk.Frame(main_panel)
        main_panel.add(right_panel, weight=4)
        
        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Вкладка редактора кода
        editor_frame = ttk.Frame(self.notebook)
        self.notebook.add(editor_frame, text=self.tr("editor"))
        
        self.text_editor = scrolledtext.ScrolledText(
            editor_frame, 
            wrap=tk.WORD, 
            font=(self.settings["font_family"], self.settings["font_size"]),
            undo=True,
            autoseparators=True,
            maxundo=-1
        )
        self.text_editor.pack(fill=tk.BOTH, expand=True)
        
        # Вкладка вывода
        output_frame = ttk.Frame(self.notebook)
        self.notebook.add(output_frame, text=self.tr("output"))
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            font=(self.settings["font_family"], self.settings["font_size"]),
            state="disabled"
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Вкладка консоли
        console_frame = ttk.Frame(self.notebook)
        self.notebook.add(console_frame, text=self.tr("console"))
        
        self.console_text = scrolledtext.ScrolledText(
            console_frame,
            wrap=tk.WORD,
            font=(self.settings["font_family"], self.settings["font_size"]),
            state="normal"
        )
        self.console_text.pack(fill=tk.BOTH, expand=True)
        
        self.setup_context_menu()
        self.setup_file_tree_context_menu()
        self.setup_text_tags()
    
    def setup_text_tags(self):
        """Настройка тегов для подсветки текста"""
        self.output_text.tag_config("error", foreground="red")
        self.output_text.tag_config("success", foreground="green")
        self.console_text.tag_config("command", foreground="blue")
        self.console_text.tag_config("output", foreground="black")
        self.console_text.tag_config("error", foreground="red")
    
    def create_status_bar(self):
        """Создание строки состояния"""
        self.status_bar = ttk.Label(
            self.root, 
            text=self.tr("ready"), 
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(5, 2)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_console(self):
        """Настройка консоли с возможностью ввода команд"""
        self.console_text.bind("<Return>", self.execute_console_command)
        self.console_prompt()
    
    def console_prompt(self):
        """Добавляет приглашение в консоль"""
        self.console_text.config(state="normal")
        self.console_text.insert(tk.END, ">>> ")
        self.console_text.mark_set(tk.INSERT, tk.END)
        self.console_text.config(state="normal")
    
    def execute_console_command(self, event=None):
        """Выполняет команду из консоли"""
        # Получаем последнюю строку с командой
        last_line = self.console_text.get("end-2c linestart", "end-1c").strip()
        command = last_line.replace(">>> ", "")
        
        if not command:
            self.console_prompt()
            return "break"
        
        # Добавляем команду в историю
        self.console_text.config(state="normal")
        self.console_text.insert(tk.END, "\n")
        
        # Определяем, нужно ли использовать venv
        if command.startswith("pip install"):
            python_exec = self.get_python_executable()
            if python_exec != sys.executable:
                # Используем pip из виртуального окружения
                if platform.system() == "Windows":
                    pip_exec = os.path.join(self.venv_path, "Scripts", "pip.exe")
                else:
                    pip_exec = os.path.join(self.venv_path, "bin", "pip")
                
                command = f'"{pip_exec}" {command[4:]}'
        
        try:
            # Выполняем команду
            process = subprocess.Popen(
                command if platform.system() != "Windows" else ["cmd", "/c", command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                shell=True,
                universal_newlines=True,
                cwd=self.project_folder if self.project_folder else os.getcwd()
            )
            
            # Читаем вывод
            output, error = process.communicate()
            
            if output:
                self.console_text.insert(tk.END, output, "output")
            if error:
                self.console_text.insert(tk.END, error, "error")
            
        except Exception as e:
            self.console_text.insert(tk.END, f"Ошибка выполнения команды: {str(e)}\n", "error")
        
        self.console_prompt()
        return "break"
    
    def setup_context_menu(self):
        """Настройка контекстного меню для редактора"""
        self.context_menu = tk.Menu(self.text_editor, tearoff=0)
        self.context_menu.add_command(label=self.tr("cut"), command=lambda: self.text_editor.event_generate("<<Cut>>"))
        self.context_menu.add_command(label=self.tr("copy"), command=lambda: self.text_editor.event_generate("<<Copy>>"))
        self.context_menu.add_command(label=self.tr("paste"), command=lambda: self.text_editor.event_generate("<<Paste>>"))
        self.context_menu.add_separator()
        self.context_menu.add_command(label=self.tr("select_all"), command=lambda: self.text_editor.tag_add("sel", "1.0", "end"))
        
        self.text_editor.bind("<Button-3>", self.show_context_menu)
    
    def setup_file_tree_context_menu(self):
        """Настройка контекстного меню для дерева файлов"""
        self.tree_context_menu = tk.Menu(self.file_tree, tearoff=0)
        self.tree_context_menu.add_command(label=self.tr("refresh_file_tree"), command=self.refresh_file_tree)
        self.tree_context_menu.add_separator()
        self.tree_context_menu.add_command(label=self.tr("new"), command=self.create_new_file)
        self.tree_context_menu.add_command(label=self.tr("new_folder"), command=self.create_new_folder)
        self.tree_context_menu.add_separator()
        self.tree_context_menu.add_command(label=self.tr("delete"), command=self.delete_selected_file)
        self.tree_context_menu.add_command(label=self.tr("open_in_terminal"), command=self.open_in_terminal)
        
        self.file_tree.bind("<Button-3>", self.show_tree_context_menu)
    
    def init_venv(self):
        """Инициализация виртуального окружения с проверкой ошибок"""
        try:
            if os.path.exists(self.venv_path):
                self.venv_active = True
                self.update_venv_status("Venv активирован")
                return True
            
            self.venv_active = False
            self.update_venv_status("Venv не активирован")
            return False
            
        except Exception as e:
            self.status_bar.config(text=f"Ошибка проверки venv: {str(e)}")
            return False
    
    def create_venv(self):
        """Создание виртуального окружения"""
        try:
            if platform.system() == "Windows":
                subprocess.run([sys.executable, "-m", "venv", self.venv_name], 
                             check=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.run([sys.executable, "-m", "venv", self.venv_name], check=True)
            
            self.venv_active = True
            self.update_venv_status("Venv активирован")
            return True
            
        except subprocess.CalledProcessError as e:
            self.venv_active = False
            self.update_venv_status(f"Ошибка создания venv: {str(e)}")
            return False
    
    def update_venv_status(self, message):
        """Обновляет статус venv в интерфейсе"""
        self.status_bar.config(text=message)
        self.venv_btn.config(text=f"Venv: {'ON' if self.venv_active else 'OFF'}")
    
    def toggle_venv_status(self):
        """Безопасное переключение статуса venv"""
        if self.venv_active:
            self.venv_active = False
            self.update_venv_status("Venv отключен")
        else:
            if self.create_venv():
                self.update_venv_status("Venv активирован")
            else:
                self.update_venv_status("Ошибка активации venv")
    
    def activate_venv_manually(self):
        """Ручная активация виртуального окружения"""
        if self.create_venv():
            messagebox.showinfo("Venv", f"Виртуальное окружение активировано: {self.venv_path}")
    
    def get_python_executable(self):
        """Безопасное получение пути к Python"""
        if not self.venv_active:
            return sys.executable
            
        try:
            if platform.system() == "Windows":
                venv_python = os.path.join(self.venv_path, "Scripts", "python.exe")
            else:
                venv_python = os.path.join(self.venv_path, "bin", "python")
            
            if os.path.exists(venv_python):
                return venv_python
            return sys.executable
        except Exception as e:
            print(f"Ошибка получения Python: {str(e)}")
            return sys.executable
    
    def open_in_terminal(self):
        """Открывает выбранную папку в терминале"""
        selected_item = self.file_tree.selection()
        path = self.project_folder or os.getcwd()
        
        if selected_item:
            item_path = self.file_tree.item(selected_item[0], "values")[0]
            if item_path:
                path = item_path if os.path.isdir(item_path) else os.path.dirname(item_path)
        
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", "-a", "Terminal", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть терминал:\n{str(e)}")
    
    def show_context_menu(self, event):
        """Показывает контекстное меню редактора"""
        self.context_menu.tk_popup(event.x_root, event.y_root)
        
    def show_tree_context_menu(self, event):
        """Показывает контекстное меню дерева файлов"""
        item = self.file_tree.identify_row(event.y)
        if item:
            self.file_tree.selection_set(item)
            self.tree_context_menu.tk_popup(event.x_root, event.y_root)
    
    def new_file(self):
        """Создает новый файл"""
        self.text_editor.delete(1.0, tk.END)
        self.current_file = None
        self.update_title()
        self.status_bar.config(text=self.tr("new_file_created"))
    
    def open_file(self, file_path=None):
        """Открывает файл"""
        if not file_path:
            file_path = filedialog.askopenfilename(
                filetypes=[("Python Files", "*.py"), ("Text Files", "*.txt"), ("All Files", "*.*")]
            )
        
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    self.text_editor.delete(1.0, tk.END)
                    self.text_editor.insert(tk.END, content)
                
                self.current_file = file_path
                self.update_title()
                self.status_bar.config(text=f"{self.tr('file_opened')}: {file_path}")
                
                if self.project_folder and file_path.startswith(self.project_folder):
                    self.highlight_file_in_tree(file_path)
                
                # Применяем подсветку синтаксиса
                self.highlight_syntax()
            except Exception as e:
                messagebox.showerror(self.tr("error"), f"{self.tr('file_open_error')}:\n{str(e)}")
    
    def open_folder(self):
        """Открывает папку как проект"""
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.project_folder = folder_path
            self.update_title()
            self.status_bar.config(text=f"{self.tr('folder_opened')}: {folder_path}")
            self.build_file_tree(folder_path)
    
    def build_file_tree(self, folder_path):
        """Строит дерево файлов для указанной папки"""
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        root_node = self.file_tree.insert("", "end", text=os.path.basename(folder_path), 
                                        values=[folder_path], open=True)
        self.add_folder_contents(root_node, folder_path)
    
    def add_folder_contents(self, parent_node, folder_path):
        """Добавляет содержимое папки в дерево файлов"""
        try:
            for item in os.listdir(folder_path):
                full_path = os.path.join(folder_path, item)
                
                if os.path.isdir(full_path):
                    node = self.file_tree.insert(parent_node, "end", text=item, 
                                               values=[full_path], open=False)
                    self.add_folder_contents(node, full_path)
                else:
                    self.file_tree.insert(parent_node, "end", text=item, 
                                      values=[full_path])
        except PermissionError:
            pass
    
    def on_file_double_click(self, event):
        """Обработчик двойного клика по файлу"""
        item = self.file_tree.selection()[0]
        file_path = self.file_tree.item(item, "values")[0]
        
        if os.path.isfile(file_path):
            self.open_file(file_path)
    
    def highlight_file_in_tree(self, file_path):
        """Выделяет файл в дереве файлов"""
        for item in self.file_tree.get_children():
            if self.file_tree.item(item, "values") and self.file_tree.item(item, "values")[0] == file_path:
                self.file_tree.selection_set(item)
                self.file_tree.focus(item)
                return
        
        for item in self.file_tree.get_children():
            self._search_and_highlight_file(item, file_path)
    
    def _search_and_highlight_file(self, parent_item, file_path):
        """Рекурсивный поиск файла в дереве"""
        for item in self.file_tree.get_children(parent_item):
            if self.file_tree.item(item, "values") and self.file_tree.item(item, "values")[0] == file_path:
                self.file_tree.selection_set(item)
                self.file_tree.focus(item)
                self.expand_parents(item)
                return
            self._search_and_highlight_file(item, file_path)
    
    def expand_parents(self, item):
        """Раскрывает родительские папки для элемента"""
        parent = self.file_tree.parent(item)
        if parent:
            self.file_tree.item(parent, open=True)
            self.expand_parents(parent)
    
    def save_file(self):
        """Сохраняет текущий файл"""
        if self.current_file:
            try:
                content = self.text_editor.get(1.0, tk.END)
                with open(self.current_file, "w", encoding="utf-8") as file:
                    file.write(content)
                
                self.status_bar.config(text=f"{self.tr('file_saved')}: {self.current_file}")
            except Exception as e:
                messagebox.showerror(self.tr("error"), f"{self.tr('file_save_error')}:\n{str(e)}")
        else:
            self.save_file_as()
    
    def save_file_as(self):
        """Сохраняет файл с указанием имени"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python Files", "*.py"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if file_path:
            self.current_file = file_path
            self.save_file()
            self.update_title()
            
            if self.project_folder and file_path.startswith(self.project_folder):
                self.refresh_file_tree()
                self.highlight_file_in_tree(file_path)
    
    def update_title(self):
        """Обновляет заголовок окна"""
        title = "PyCode 1.2"
        if self.project_folder:
            title += f" - {os.path.basename(self.project_folder)}"
        if self.current_file:
            title += f" - {os.path.basename(self.current_file)}"
        self.root.title(title)
    
    def run_python_code(self):
        """Запускает Python-код с обработкой временного файла"""
        code = self.text_editor.get(1.0, tk.END)
        
        if not code.strip():
            self.output_text.config(state="normal")
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, f"{self.tr('no_code_to_execute')}\n")
            self.output_text.config(state="disabled")
            return
        
        if self.process and self.process.poll() is None:
            self.stop_execution()
        
        python_exec = self.get_python_executable()
        temp_dir = self.project_folder if self.project_folder else os.getcwd()
        temp_file = os.path.join(temp_dir, "__temp_execution.py")
        
        try:
            # Сохраняем код во временный файл
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(code)
            
            # Убедимся, что файл записался на диск
            if not os.path.exists(temp_file):
                raise FileNotFoundError(f"{self.tr('temp_file_error')}: {temp_file}")
            
            self.output_text.config(state="normal")
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, f"{self.tr('running_code_with')} {python_exec}...\n")
            self.output_text.see(tk.END)
            self.output_text.config(state="disabled")
            
            # Запускаем процесс с указанием рабочей директории
            self.process = subprocess.Popen(
                [python_exec, temp_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                universal_newlines=True,
                cwd=temp_dir,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            
            self.root.after(100, self.read_process_output)
            self.notebook.select(1)
            self.status_bar.config(text=self.tr("executing_code"))
            
            # Удаляем временный файл после завершения процесса
            self.root.after(100, lambda: self.cleanup_temp_file(temp_file))
        except Exception as e:
            self.output_text.config(state="normal")
            self.output_text.insert(tk.END, f"{self.tr('error')}: {str(e)}\n", "error")
            self.output_text.config(state="disabled")
            self.status_bar.config(text=self.tr("execution_error"))
            # Удаляем временный файл в случае ошибки
            self.cleanup_temp_file(temp_file)

    def cleanup_temp_file(self, temp_file):
        """Безопасное удаление временного файла"""
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception as e:
            print(f"{self.tr('temp_file_delete_error')}: {str(e)}")
    
    def read_process_output(self):
        """Читает вывод выполняемого процесса с обработкой ошибок"""
        if self.process is None:
            return
            
        try:
            # Чтение stdout
            stdout = self.process.stdout
            if stdout:
                output = stdout.readline()
                if output:
                    self.output_text.config(state="normal")
                    self.output_text.insert(tk.END, output)
                    self.output_text.see(tk.END)
                    self.output_text.config(state="disabled")
            
            # Чтение stderr
            stderr = self.process.stderr
            if stderr:
                error = stderr.readline()
                if error:
                    self.output_text.config(state="normal")
                    self.output_text.insert(tk.END, error, "error")
                    self.output_text.see(tk.END)
                    self.output_text.config(state="disabled")
            
            if self.process.poll() is None:
                self.root.after(100, self.read_process_output)
            else:
                self.process = None
                self.status_bar.config(text=self.tr("execution_completed"))
        except Exception as e:
            self.output_text.config(state="normal")
            self.output_text.insert(tk.END, f"{self.tr('output_read_error')}: {str(e)}\n", "error")
            self.output_text.config(state="disabled")
            self.process = None
    
    def stop_execution(self):
        """Останавливает выполнение кода"""
        if self.process and self.process.poll() is None:
            try:
                if platform.system() == "Windows":
                    self.process.terminate()
                else:
                    self.process.kill()
                self.output_text.config(state="normal")
                self.output_text.insert(tk.END, f"\n{self.tr('execution_stopped')}\n", "error")
                self.output_text.see(tk.END)
                self.output_text.config(state="disabled")
                self.status_bar.config(text=self.tr("execution_stopped"))
            except Exception as e:
                messagebox.showerror(self.tr("error"), f"{self.tr('stop_process_error')}:\n{str(e)}")
            finally:
                self.process = None
    
    def toggle_dark_mode(self):
        """Переключает темный/светлый режим"""
        self.dark_mode = not self.dark_mode
        
        if self.dark_mode:
            # Темная тема
            bg_color = "#1e1e1e"
            fg_color = "#d4d4d4"
            self.text_editor.config(
                bg=bg_color,
                fg=fg_color,
                insertbackground="white",
                selectbackground="#264f78",
                selectforeground="white"
            )
            self.output_text.config(
                bg=bg_color,
                fg=fg_color,
                insertbackground="white",
                selectbackground="#264f78",
                selectforeground="white"
            )
            self.console_text.config(
                bg=bg_color,
                fg=fg_color,
                insertbackground="white",
                selectbackground="#264f78",
                selectforeground="white"
            )
            self.file_tree.config(
                background="#252526",
                foreground=fg_color,
                fieldbackground="#252526"
            )
            self.style.configure("Treeview", 
                              background="#252526",
                              foreground=fg_color,
                              fieldbackground="#252526")
        else:
            # Светлая тема
            bg_color = "white"
            fg_color = "black"
            self.text_editor.config(
                bg=bg_color,
                fg=fg_color,
                insertbackground="black",
                selectbackground="#cce8ff",
                selectforeground="black"
            )
            self.output_text.config(
                bg=bg_color,
                fg=fg_color,
                insertbackground="black",
                selectbackground="#cce8ff",
                selectforeground="black"
            )
            self.console_text.config(
                bg=bg_color,
                fg=fg_color,
                insertbackground="black",
                selectbackground="#cce8ff",
                selectforeground="black"
            )
            self.file_tree.config(
                background=bg_color,
                foreground=fg_color,
                fieldbackground=bg_color
            )
            self.style.configure("Treeview", 
                              background=bg_color,
                              foreground=fg_color,
                              fieldbackground=bg_color)
        
        # Обновляем подсветку синтаксиса при смене темы
        self.setup_syntax_highlighting()
    
    def refresh_file_tree(self):
        """Обновляет дерево файлов"""
        if self.project_folder:
            self.build_file_tree(self.project_folder)
            self.status_bar.config(text=self.tr("file_tree_updated"))
    
    def create_new_file(self):
        """Создает новый файл в проекте"""
        selected_item = self.file_tree.selection()
        if not selected_item:
            if not self.project_folder:
                messagebox.showwarning(self.tr("warning"), self.tr("open_folder_first"))
                return
            parent_path = self.project_folder
        else:
            parent_path = self.file_tree.item(selected_item[0], "values")[0]
            if not os.path.isdir(parent_path):
                parent_path = os.path.dirname(parent_path)
        
        file_name = simpledialog.askstring(self.tr("new_file"), self.tr("enter_file_name"))
        if file_name:
            file_path = os.path.join(parent_path, file_name)
            try:
                with open(file_path, "w") as f:
                    f.write("")
                self.refresh_file_tree()
                self.open_file(file_path)
            except Exception as e:
                messagebox.showerror(self.tr("error"), f"{self.tr('file_create_error')}:\n{str(e)}")
    
    def create_new_folder(self):
        """Создает новую папку в проекте"""
        selected_item = self.file_tree.selection()
        if not selected_item:
            if not self.project_folder:
                messagebox.showwarning(self.tr("warning"), self.tr("open_folder_first"))
                return
            parent_path = self.project_folder
        else:
            parent_path = self.file_tree.item(selected_item[0], "values")[0]
            if not os.path.isdir(parent_path):
                parent_path = os.path.dirname(parent_path)
        
        folder_name = simpledialog.askstring(self.tr("new_folder"), self.tr("enter_folder_name"))
        if folder_name:
            folder_path = os.path.join(parent_path, folder_name)
            try:
                os.mkdir(folder_path)
                self.refresh_file_tree()
            except Exception as e:
                messagebox.showerror(self.tr("error"), f"{self.tr('folder_create_error')}:\n{str(e)}")
    
    def delete_selected_file(self):
        """Удаляет выбранный файл или папку"""
        selected_item = self.file_tree.selection()
        if not selected_item:
            return
        
        item_path = self.file_tree.item(selected_item[0], "values")[0]
        if not item_path:
            return
        
        confirm = messagebox.askyesno(self.tr("confirmation"), 
                                    f"{self.tr('confirm_delete')} {os.path.basename(item_path)}?")
        if confirm:
            try:
                if os.path.isdir(item_path):
                    os.rmdir(item_path)
                else:
                    os.remove(item_path)
                self.refresh_file_tree()
                
                if self.current_file and self.current_file == item_path:
                    self.text_editor.delete(1.0, tk.END)
                    self.current_file = None
                    self.update_title()
            except Exception as e:
                messagebox.showerror(self.tr("error"), f"{self.tr('delete_error')}:\n{str(e)}")
    
    def show_about(self):
        """Показывает информацию о программе"""
        about_text = f"""PyCode 1.2 - {self.tr('python_code_editor')}

{self.tr('features')}:
- {self.tr('syntax_highlighting')}
- {self.tr('project_work')}
- {self.tr('virtual_environment')}
- {self.tr('run_code')} (F5)
- {self.tr('dark_light_mode')}
- {self.tr('builtin_console')}

{self.tr('author')}: Kirillovo Company
{self.tr('version')}: 1.2
GitHub: {self.github_repo}"""
        
        messagebox.showinfo(self.tr("about"), about_text)
    
    def exit_app(self):
        """Завершает работу приложения"""
        self.stop_execution()
        
        if messagebox.askokcancel(self.tr("exit"), self.tr("confirm_exit")):
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PythonCodeEditor(root)
    root.mainloop()
