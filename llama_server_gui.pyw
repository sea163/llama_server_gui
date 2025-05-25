import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import json
import subprocess
import re
import io
import pystray
from PIL import Image, ImageTk

# 默认参数，更丰富的参数类型，添加参数描述和类型提示
DEFAULT_PARAMS = {
            # 模型路径，启动时设置，类型为 path，不需要用户编辑
            "m": {
                "default": "",
                "type": "path",
                "desc": "模型路径"
            },
            # GPU 图层数，类型为整数，最小值验证
            "ngl": {
                "default": 80,
                "type": "integer",
                "desc": "GPU 图层数",
                "validation": {
                    "type": "integer",
                    "min": 0
                }
            },
            # 服务器 Host，类型为字符串
            "host": {
                "default": "127.0.0.1",
                "type": "string",
                "desc": "服务器Host"
            },
            # 服务器端口，类型为整数，端口范围验证
            "port": {
                "default": 8000,
                "type": "integer",
                "desc": "服务器端口",
                "validation": {
                    "type": "integer",
                    "min": 1,
                    "max": 65535
                }
            },
            # 上下文长度, 类型为整数，最小值验证
            "ctx-size": {
                "default": 2048,
                "type": "integer",
                "desc": "上下文长度",
                "validation": {
                    "type": "integer",
                    "min": 1
                }
            },
            # 温度
            "temp": {
                "default": 0.8,
                "type": "float",
                "desc": "温度 (默认值: 0.8)",
                "validation": {
                    "type": "float",
                    "min": 0
                }
            },
            # 启用 Flash Attention
            "flash-attn": {
                "default": False,
                "type": "boolean",
                "desc": "启用快速注意力机制"
            },
            # 详细日志
            "verbose": {
                "default": False,
                "type": "boolean",
                "desc": "启用详细日志"
            },
            # 重复惩罚系数
            "repeat-penalty": {
                "default": 1.0,
                "type": "float",
                "desc": "重复惩罚系数 (默认值: 1.0, 1.0 = 禁用)",
                "validation": {
                    "type": "float",
                    "min": 0
                }
            },
            # 考虑重复惩罚的最后 N 个标记
            "repeat-last-n": {
                "default": 64,
                "type": "integer",
                "desc": "最近的tokens的范围 \n(默认值: 64, 0 = 禁用, -1= ctx_size)",
                "validation": {
                    "type": "integer"
                }
            },
            # 存在惩罚系数
            "presence-penalty": {
                "default": 0.0,
                "type": "float",
                "desc": "存在惩罚系数 (默认值：0.0，0.0 = 禁用)",
                "validation": {
                    "type": "float",
                    "min": 0
                }
            },
            # 频率惩罚系数
            "frequency-penalty": {
                "default": 0.0,
                "type": "float",
                "desc": "频率惩罚系数 (默认值：0: 0.0, 0.0 = 禁用)",
                "validation": {
                    "type": "float",
                    "min": 0
                }
            },
            # 多模态投影文件路径
            "mmproj": {
                "default": "",
                "type": "string",
                "desc": "多模态投影模型路径"
            },
            # 是否禁用多模态投影加载到GPU
            "no-mmproj-offload": {
                "default": False,
                "type": "boolean", 
                "desc": "禁用多模态投影加载到GPU"
            },

            # 模型备注信息，类型为字符串
            "model_remark": {
                "default": "",
                "type": "string",
                "is_multiple": True,
                "desc": "备注信息"
            },


            # ... 可以根据 llama-server.exe 的参数列表继续添加，并定义类型和验证规则
        }

# 参数前缀映射表，根据 llama-server.exe 的参数文档生成
PARAM_PREFIX_MAP = {
    "help": ["-h", "--help", "--usage"],
    "version": ["--version"],
    "completion-bash": ["--completion-bash"],
    "verbose-prompt": ["--verbose-prompt"],
    "threads": ["-t", "--threads"],
    "threads-batch": ["-tb", "--threads-batch"],
    "cpu-mask": ["-C", "--cpu-mask"],
    "cpu-range": ["-Cr", "--cpu-range"],
    "cpu-strict": ["--cpu-strict"],
    "prio": ["--prio"],
    "poll": ["--poll"],
    "cpu-mask-batch": ["-Cb", "--cpu-mask-batch"],
    "cpu-range-batch": ["-Crb", "--cpu-range-batch"],
    "cpu-strict-batch": ["--cpu-strict-batch"],
    "prio-batch": ["--prio-batch"],
    "poll-batch": ["--poll-batch"],
    "ctx-size": ["-c", "--ctx-size"],
    "predict": ["-n", "--predict", "--n-predict"],
    "batch-size": ["-b", "--batch-size"],
    "ubatch-size": ["-ub", "--ubatch-size"],
    "keep": ["--keep"],
    "flash-attn": ["-fa", "--flash-attn"],
    "no-perf": ["--no-perf"],
    "escape": ["-e", "--escape"],
    "no-escape": ["--no-escape"],
    "rope-scaling": ["--rope-scaling"],
    "rope-scale": ["--rope-scale"],
    "rope-freq-base": ["--rope-freq-base"],
    "rope-freq-scale": ["--rope-freq-scale"],
    "yarn-orig-ctx": ["--yarn-orig-ctx"],
    "yarn-ext-factor": ["--yarn-ext-factor"],
    "yarn-attn-factor": ["--yarn-attn-factor"],
    "yarn-beta-slow": ["--yarn-beta-slow"],
    "yarn-beta-fast": ["--yarn-beta-fast"],
    "dump-kv-cache": ["-dkvc", "--dump-kv-cache"],
    "no-kv-offload": ["-nkvo", "--no-kv-offload"],
    "cache-type-k": ["-ctk", "--cache-type-k"],
    "cache-type-v": ["-ctv", "--cache-type-v"],
    "defrag-thold": ["-dt", "--defrag-thold"],
    "parallel": ["-np", "--parallel"],
    "rpc": ["--rpc"],
    "mlock": ["--mlock"],
    "no-mmap": ["--no-mmap"],
    "numa": ["--numa"],
    "device": ["-dev", "--device"],
    "list-devices": ["--list-devices"],
    "ngl": ["-ngl", "--gpu-layers", "--n-gpu-layers"],
    "split-mode": ["-sm", "--split-mode"],
    "tensor-split": ["-ts", "--tensor-split"],
    "main-gpu": ["-mg", "--main-gpu"],
    "check-tensors": ["--check-tensors"],
    "override-kv": ["--override-kv"],
    "lora": ["--lora"],
    "lora-scaled": ["--lora-scaled"],
    "control-vector": ["--control-vector"],
    "control-vector-scaled": ["--control-vector-scaled"],
    "control-vector-layer-range": ["--control-vector-layer-range"],
    "m": ["-m", "--model"],
    "model-url": ["-mu", "--model-url"],
    "hf-repo": ["-hf", "-hfr", "--hf-repo"],
    "hf-repo-draft": ["-hfd", "-hfrd", "--hf-repo-draft"],
    "hf-file": ["-hff", "--hf-file"],
    "hf-repo-v": ["-hfv", "-hfrv", "--hf-repo-v"],
    "hf-file-v": ["-hffv", "--hf-file-v"],
    "hf-token": ["-hft", "--hf-token"],
    "log-disable": ["--log-disable"],
    "log-file": ["--log-file"],
    "log-colors": ["--log-colors"],
    "verbose": ["-v", "--verbose", "--log-verbose"],
    "verbosity": ["-lv", "--verbosity", "--log-verbosity"],
    "log-prefix": ["--log-prefix"],
    "log-timestamps": ["--log-timestamps"],
    "samplers": ["--samplers"],
    "seed": ["-s", "--seed"],
    "sampler-seq": ["--sampling-seq", "--sampler-seq"],
    "ignore-eos": ["--ignore-eos"],
    "temp": ["--temp"],
    "top-k": ["--top-k"],
    "top-p": ["--top-p"],
    "min-p": ["--min-p"],
    "xtc-probability": ["--xtc-probability"],
    "xtc-threshold": ["--xtc-threshold"],
    "typical": ["--typical"],
    "repeat-last-n": ["--repeat-last-n"],
    "repeat-penalty": ["--repeat-penalty"],
    "presence-penalty": ["--presence-penalty"],
    "frequency-penalty": ["--frequency-penalty"],
    "dry-multiplier": ["--dry-multiplier"],
    "dry-base": ["--dry-base"],
    "dry-allowed-length": ["--dry-allowed-length"],
    "dry-penalty-last-n": ["--dry-penalty-last-n"],
    "dry-sequence-breaker": ["--dry-sequence-breaker"],
    "dynatemp-range": ["--dynatemp-range"],
    "dynatemp-exp": ["--dynatemp-exp"],
    "mirostat": ["--mirostat"],
    "mirostat-lr": ["--mirostat-lr"],
    "mirostat-ent": ["--mirostat-ent"],
    "logit-bias": ["-l", "--logit-bias"],
    "grammar": ["--grammar"],
    "grammar-file": ["--grammar-file"],
    "json-schema": ["-j", "--json-schema"],
    "no-context-shift": ["--no-context-shift"],
    "special": ["-sp", "--special"],
    "no-warmup": ["--no-warmup"],
    "spm-infill": ["--spm-infill"],
    "pooling": ["--pooling"],
    "cont-batching": ["-cb", "--cont-batching"],
    "no-cont-batching": ["-nocb", "--no-cont-batching"],
    "alias": ["-a", "--alias"],
    "host": ["--host"],
    "port": ["--port"],
    "path": ["--path"],
    "no-webui": ["--no-webui"],
    "embedding": ["--embedding", "--embeddings"],
    "reranking": ["--reranking", "--rerank"],
    "api-key": ["--api-key"],
    "api-key-file": ["--api-key-file"],
    "ssl-key-file": ["--ssl-key-file"],
    "ssl-cert-file": ["--ssl-cert-file"],
    "timeout": ["-to", "--timeout"],
    "threads-http": ["--threads-http"],
    "cache-reuse": ["--cache-reuse"],
    "metrics": ["--metrics"],
    "slots": ["--slots"],
    "props": ["--props"],
    "no-slots": ["--no-slots"],
    "slot-save-path": ["--slot-save-path"],
    "jinja": ["--jinja"],
    "reasoning-format": ["--reasoning-format"],
    "chat-template": ["--chat-template"],
    "chat-template-file": ["--chat-template-file"],
    "slot-prompt-similarity": ["-sps", "--slot-prompt-similarity"],
    "lora-init-without-apply": ["--lora-init-without-apply"],
    "draft-max": ["--draft-max", "--draft", "--draft-n"],
    "draft-min": ["--draft-min", "--draft-n-min"],
    "draft-p-min": ["--draft-p-min"],
    "ctx-size-draft": ["-cd", "--ctx-size-draft"],
    "device-draft": ["-devd", "--device-draft"],
    "n_gpu_layers_draft": ["-ngld", "--gpu-layers-draft", "--n-gpu-layers-draft"],
    "model-draft": ["-md", "--model-draft"],
    "model-vocoder": ["-mv", "--model-vocoder"],
    "tts-use-guide-tokens": ["--tts-use-guide-tokens"],
    "embd-bge-small-en-default": ["--embd-bge-small-en-default"],
    "embd-e5-small-en-default": ["--embd-e5-small-en-default"],
    "embd-gte-small-default": ["--embd-gte-small-default"],
    "mmproj": ["--mmproj"],
    "no-mmproj-offload": ["--no-mmproj-offload"],
}

class LlamaServerGUI:
    def __init__(self, root):
        self.root = root
        # 绑定窗口关闭事件到 save_app_config 方法
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.title("Llama.cpp Llama-Server 简单启动器")
        # 设置窗口图标
        module_name = os.path.splitext(os.path.basename(__file__))[0]
        icon_path = f"{module_name}.png"
        if os.path.exists(icon_path):
            try:
                icon = Image.open(icon_path)
                photo = ImageTk.PhotoImage(icon)
                self.root.tk.call('wm', 'iconphoto', self.root._w, photo)
            except Exception as e:
                print(f"设置窗口图标时出错: {e}")

        # 配置文件路径和 llama-server 路径配置
        self.config_dir = "config" # 配置文件目录
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        self.app_config_file = os.path.join(self.config_dir, "app_config.json")
        self.app_config = self.load_app_config() # 加载应用配置

        # 加载窗口大小配置
        width = self.app_config.get('window_width')
        height = self.app_config.get('window_height')
        if width and height:
            self.root.geometry(f"{width}x{height}")
        else:
            # 如果没有保存的窗口大小，设置默认大小
            width = 800
            height = 600
            self.root.geometry(f"{width}x{height}")

        # 设置窗口居中
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        #  修改关闭窗口协议为最小化到托盘
        #self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        self.root.bind("<Unmap>", self.on_minimize) # 绑定窗口最小化事件
        # 创建并启动托盘图标
        self.create_system_tray_icon()
        if self.tray_icon:
            tray_thread = threading.Thread(target=self.tray_icon.run)
            tray_thread.daemon = True
            tray_thread.start()

        self.models_dir_var = tk.StringVar(value=self.app_config.get("models_dir", "models")) # 默认模型目录
        self.llama_server_path_var = tk.StringVar(value=self.app_config.get("llama_server_path", "llama-server.exe")) # 默认 llama-server.exe 路径

        self.default_params = DEFAULT_PARAMS
        self.current_params = {} # 当前参数配置
        self.selected_model = None # 当前选中的模型
        self.process = None # 用于存储 llama-server 进程对象

        self.model_list_var = tk.StringVar(value=self.scan_models())
        self.param_widgets = {} # 存储参数编辑部件

        # 界面美化 - 使用 ttk 主题
        ttk.Style().theme_use('clam') #  'clam', 'alt', 'default', 'classic', 'vista', 'xpnative'

        self.create_widgets()

        # 在UI启动后创建线程执行日志输出函数
        threading.Thread(target=self._log_system_info, daemon=True).start()

    def on_close(self):
        # 保存应用程序配置
        self.exit_application()

    def on_minimize(self, event):
        """窗口最小化事件处理"""
        if self.root.state() == 'iconic': #  检查窗口是否被最小化 (iconic 状态)
            self.minimize_to_tray() # 最小化到托盘

    def load_app_config(self):
        """加载应用程序配置"""
        if os.path.exists(self.app_config_file):
            try:
                with open(self.app_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                messagebox.showerror("配置错误", f"应用程序配置文件 {self.app_config_file} 解析失败，将使用默认配置")
                return {}
        return {} # 如果配置文件不存在，返回空字典，使用默认值

    def save_app_config(self):
        """保存应用程序配置"""
        config_data = {
            "models_dir": self.models_dir_var.get(),
            "llama_server_path": self.llama_server_path_var.get(),
            "window_width": self.root.winfo_width(),
            "window_height": self.root.winfo_height()
        }
        try:
            with open(self.app_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            messagebox.showerror("配置保存失败", f"保存应用程序配置文件失败: {e}")

    def create_widgets(self):
        # 顶部菜单 - 配置文件路径和 llama-server 路径配置
        settings_frame = ttk.LabelFrame(self.root, text="设置")
        settings_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        ttk.Label(settings_frame, text="模型目录:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        models_dir_entry = ttk.Entry(settings_frame, textvariable=self.models_dir_var, width=50)
        models_dir_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        models_dir_entry.bind("<FocusOut>", self.on_path_config_change) # 路径修改后保存配置

        ttk.Label(settings_frame, text="llama-server 路径:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        llama_server_path_entry = ttk.Entry(settings_frame, textvariable=self.llama_server_path_var, width=50)
        llama_server_path_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        llama_server_path_entry.bind("<FocusOut>", self.on_path_config_change) # 路径修改后保存配置

        settings_frame.columnconfigure(1, weight=1) # 让路径输入框可以扩展

        # 模型选择框架
        model_frame = ttk.LabelFrame(self.root, text="模型选择")
        model_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nwse")

        self.model_listbox = tk.Listbox(model_frame, listvariable=self.model_list_var, height=10, width=40)
        self.model_listbox.pack(padx=5, pady=5, fill="both", expand=True)
        self.model_listbox.bind("<Double-Button-1>", self.load_model_config) # 双击加载模型配置
        self.model_listbox.bind("<Button-1>", self.select_model_no_load) # 单击只选中模型，不加载配置

        # 参数配置框架
        param_frame = ttk.LabelFrame(self.root, text="参数配置")
        param_frame.grid(row=1, column=1, padx=10, pady=5, sticky="nwse")

        # 获取 param_frame 的背景颜色
        style = ttk.Style()
        param_config_bg_color = style.lookup('TLabelframe', 'background')

        # self.param_canvas = tk.Canvas(param_frame, bd=0, highlightthickness=0) # 创建 Canvas
        self.param_canvas = tk.Canvas(param_frame, bd=0, highlightthickness=0, background=param_config_bg_color, relief=tk.SUNKEN) # 创建 Canvas
        self.param_scrollbar = ttk.Scrollbar(param_frame, orient=tk.VERTICAL, command=self.param_canvas.yview) # 创建 Scrollbar
        self.param_config_area = ttk.Frame(self.param_canvas) #  参数配置区域 Frame 放在 Canvas 上
        self.param_config_area.pack(padx=5, pady=5, fill="both", expand=True)

  
        self.param_scrollbar.pack(side=tk.RIGHT, fill=tk.Y) # Scrollbar 靠右
        self.param_canvas.config(yscrollcommand=self.param_scrollbar.set) # Canvas 关联 Scrollbar

        self.param_canvas_window = self.param_canvas.create_window((0, 0), window=self.param_config_area, anchor=tk.NW) # Frame 放入 Canvas
        self.param_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True) # Canvas 填充 param_frame 剩余空间

        self.param_config_area.bind("<Configure>", self.on_param_frame_configure) # 绑定 Frame 的 Configure 事件

        # 实时日志显示区域
        log_frame = ttk.LabelFrame(self.root, text="运行日志")
        log_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="newse")

        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, wrap=tk.WORD, state=tk.DISABLED) # 禁用编辑
        self.log_text.pack(padx=5, pady=5, fill="both", expand=True)

        # 启动控制框架
        control_frame = ttk.Frame(self.root)
        control_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        self.save_button = ttk.Button(control_frame, text="保存参数", command=self.save_config)
        self.save_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.save_button = ttk.Button(control_frame, text="恢复参数", command=self.restore_config)
        self.save_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.launch_button = ttk.Button(control_frame, text="启动 Llama-Server", command=self.launch_server)
        self.launch_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.stop_button = ttk.Button(control_frame, text="停止 Llama-Server", command=self.stop_server, state=tk.DISABLED) # 停止按钮，初始禁用
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.select_llama_cpp_path_button = ttk.Button(control_frame, text="选择llama.cpp路径", command=self.select_llama_cpp_path)
        self.select_llama_cpp_path_button.pack(side=tk.LEFT) # 靠左排列

        self.status_label = ttk.Label(control_frame, text="")
        self.status_label.pack(side=tk.LEFT, padx=5, pady=5)

        self.root.columnconfigure(1, weight=1) # 让参数配置和日志区域可以水平扩展
        self.root.rowconfigure(1, weight=1) # 让参数配置和模型列表可以垂直扩展
        log_frame.rowconfigure(0, weight=1) # 让日志区域可以垂直扩展
        log_frame.columnconfigure(0, weight=1) # 让日志区域可以水平扩展

    def on_param_frame_configure(self, event):
        """当参数配置框架大小改变时，更新 Canvas 的滚动区域和窗口项宽度"""
        self.param_canvas.configure(scrollregion=self.param_canvas.bbox("all")) # 更新滚动区域
        self.param_canvas.itemconfigure(self.param_canvas_window, width=event.width) # 更新窗口项宽度

    def create_system_tray_icon(self):
        """创建系统托盘图标"""
        # 加载托盘图标图片，请替换 'your_icon.png' 为您的图标文件路径
        module_name = os.path.splitext(os.path.basename(__file__))[0]
        try:
            # 尝试加载 PNG 图标，如果失败则加载 ICO
            icon_image = Image.open(f"{module_name}.png") # 优先尝试 PNG
        except FileNotFoundError:
            try:
                icon_image = Image.open(f"{module_name}.ico") # 备选 ICO 图标
            except FileNotFoundError:
                messagebox.showerror("错误", f"找不到托盘图标文件 '{module_name}.png' 或 '{module_name}.ico'，请确保图标文件存在并放在正确的位置。")
                return None  # 如果图标文件找不到，则不创建托盘图标并返回 None

        def toggle_window_visibility(icon, item):
            """从托盘菜单恢复窗口 (也用作单击图标的动作)"""
            if self.root.state() == 'iconic' or self.root.state() == 'withdrawn':  # 检查窗口是否最小化
                self.root.after(0, self.show_window)  # 确保在 Tkinter 主线程中操作
            else:
                self.root.after(0, self.minimize_to_tray)  # 若未最小化则最小化窗口

        def exit_application_from_tray(icon, item):
            """从托盘菜单退出应用"""
            icon.stop() # 停止托盘图标
            self.root.after(0, self.exit_application) # 确保在 Tkinter 主线程中操作
        # 创建托盘菜单
        tray_menu = pystray.Menu(
            pystray.MenuItem("显示或隐藏", toggle_window_visibility, default=True), # 恢复窗口菜单项，设置为默认项
            pystray.MenuItem("退出", exit_application_from_tray)  # 退出应用菜单项
        )

        # 创建托盘图标
        self.tray_icon = pystray.Icon(
            "llama-server-tray-icon",
            icon_image,
            "Llama Server",
            tray_menu,
        )
        return self.tray_icon

    def show_window(self):
        """显示主窗口并移除托盘图标 (如果存在)"""
        self.root.deiconify()  # 显示窗口

    def hide_window(self):
        """隐藏主窗口并显示托盘图标"""
        self.root.withdraw()  # 隐藏窗口
        if not hasattr(self, 'tray_icon') or not self.tray_icon: # 如果托盘图标还未创建，则创建
            self.create_system_tray_icon()

    def minimize_to_tray(self):
        """最小化到托盘"""
        self.hide_window()
        #messagebox.showinfo("程序已最小化到托盘", "程序已最小化到系统托盘。\n\n您可以通过系统托盘图标恢复或退出程序。")

    def exit_application(self):
        self.save_app_config()
        """安全退出应用程序，包括停止 llama-server 和托盘图标"""
        if self.process and self.process.poll() is None:
            self.stop_server() #  先停止 llama-server

        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.stop() # 确保托盘图标被停止

        self.root.destroy()     #  销毁 Tkinter 窗口，退出主循环

    def on_path_config_change(self, event=None):
        """路径配置更改后保存配置"""
        self.save_app_config()
        self.model_list_var.set(self.scan_models()) # 重新扫描模型列表

    def select_llama_cpp_path(self):
        """打开目录选择对话框，选择 llama-server.exe 路径"""
        # 获取当前路径
        current_path = self.llama_server_path_var.get()
        if current_path:
            # 将当前路径转换为绝对路径
            absolute_path = os.path.abspath(current_path)
            # 获取绝对路径的目录名
            initial_dir = os.path.dirname(absolute_path)
        else:
            # 如果当前路径为空，使用用户的主目录
            initial_dir = os.path.expanduser("~")

        folder_path = filedialog.askdirectory(
            title="选择 llama-server.exe 所在目录",
            initialdir=initial_dir
        )
        if folder_path:
            # 这里假设 llama-server.exe 文件名固定，并位于所选目录
            llama_server_exe_path = os.path.join(folder_path, "llama-server.exe")  #  请根据实际情况修改 llama-server.exe 的文件名
            if os.path.exists(llama_server_exe_path):
                try:
                    # 尝试将路径转换为相对路径
                    relative_path = os.path.relpath(llama_server_exe_path, start=os.getcwd())
                    # 检查转换后的相对路径是否更短，如果是则使用相对路径
                    if len(relative_path) < len(llama_server_exe_path):
                        self.llama_server_path_var.set(relative_path)
                    else:
                        self.llama_server_path_var.set(llama_server_exe_path)
                except ValueError:
                    # 如果无法转换为相对路径，使用原始绝对路径
                    self.llama_server_path_var.set(llama_server_exe_path)
                self.save_app_config()  # 选择路径后保存配置
            else:
                messagebox.showerror("错误", f"在所选目录 '{folder_path}' 中未找到 llama-server.exe，请选择包含 llama-server.exe 的目录。")

    def scan_models(self):
        """扫描模型目录下的 .gguf 文件"""
        models_dir = self.models_dir_var.get()
        models = []
        if not os.path.exists(models_dir):
            try:
                os.makedirs(models_dir) # 如果模型目录不存在则创建
            except OSError as e:
                messagebox.showerror("目录错误", f"无法创建模型目录 '{models_dir}': {e}")
                return [] # 目录创建失败，返回空列表
        if os.path.isdir(models_dir): # 确保模型目录是一个目录
            for filename in os.listdir(models_dir):
                if filename.endswith(".gguf") and not filename.startswith("mmproj-"):
                    models.append(filename)
        else:
            messagebox.showerror("目录错误", f"模型目录 '{models_dir}' 不是一个有效的目录")
        return models

    def select_model_no_load(self, event):
        """单击模型列表，仅选中模型，不加载配置"""
        selected_index = self.model_listbox.curselection()
        if selected_index:
            self.selected_model = self.model_listbox.get(selected_index[0])
            self.status_label.config(text=f"已选择模型: {self.selected_model}, 双击加载参数配置")

    def load_model_config(self, event=None):
        """加载选定模型的配置 (从 .json 文件或默认参数)"""
        selected_index = self.model_listbox.curselection()
        if selected_index:
            self.selected_model = self.model_listbox.get(selected_index[0])
            model_name_without_ext = self.selected_model[:-5] # 去除 ".gguf" 扩展名
            config_file = os.path.join(self.models_dir_var.get(), f"{model_name_without_ext}.json")

            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        self.current_params = json.load(f)
                    self.status_label.config(text=f"加载配置文件: {config_file}")
                except json.JSONDecodeError as e:
                    self.current_params = self.default_params.copy() # 加载失败，使用默认参数
                    self.status_label.config(text=f"配置文件 {config_file} 解析失败, 加载默认参数", foreground="red") # 错误信息用红色
                    messagebox.showerror("配置错误", f"配置文件 {config_file} JSON 解析失败: {e}, 已加载默认参数")
            else:
                self.current_params = self.default_params.copy() # 没有配置文件，使用默认参数
                self.status_label.config(text=f"未找到配置文件 {config_file}, 加载默认参数")

            # 设置模型路径参数, 更新 default 值
            self.current_params["m"]["default"] = os.path.join(self.models_dir_var.get(), self.selected_model) # 设置模型路径参数, 更新default值
            # 设置模型路径参数，设置 current 值
            self.current_params["m"]["current"] = os.path.join(self.models_dir_var.get(), self.selected_model) # 设置模型路径参数，设置current值

            self.display_params() # 显示参数到界面

    def display_params(self):
        """在参数配置区域显示当前参数, 使用更丰富的参数类型"""
        # 清空之前的参数部件
        for widget in self.param_config_area.winfo_children():
            widget.destroy()
        self.param_widgets = {} # 清空部件字典

        row_num = 0
        for param_name, param_config in self.default_params.items(): # 遍历参数配置
            if param_name == "m": # 模型路径参数不需要用户编辑，但显示出来
                label = ttk.Label(self.param_config_area, text=f"{param_config['desc']} ({param_name}):")
                label.grid(row=row_num, column=0, sticky="w", padx=5, pady=5)
                path_label_value = ttk.Label(self.param_config_area, text=self.current_params["m"]["current"], wraplength=300) # 使用Label显示路径，可以wrap
                path_label_value.grid(row=row_num, column=1, sticky="ew", padx=5, pady=5)
                row_num += 1
                continue # 跳过后续处理

            label = ttk.Label(self.param_config_area, text=f"{param_config['desc']} ({param_name}):") # 显示参数描述
            label.grid(row=row_num, column=0, sticky="w", padx=5, pady=5)

            param_type = param_config.get("type", "string") # 默认类型为 string
            default_value = param_config["default"]
            current_param_config = self.current_params.get(param_name, None) # 从 current_params 获取，没有则用默认值
            if current_param_config and "current" in current_param_config: # 如果有配置，使用配置的值
                current_value = current_param_config.get("current", default_value) # 从配置中获取默认值
            else:
                current_value = default_value # 没有配置，使用默认值
            is_multiple_string = param_config.get("is_multiple", False) #  新增: 检测 "is_multiple" 属性, 默认为 False

            if param_type == "integer":
                # 使用 Spinbox 进行整数参数输入
                widget = tk.Spinbox(self.param_config_area, from_=-65535, to=65535) #  设置合理的范围
                widget.delete(0, "end") # 清空默认值
                widget.insert(0, current_value)
            elif param_type == "float":
                # 使用 Spinbox 进行浮点数参数输入
                widget = tk.Spinbox(self.param_config_area, from_=-10000.0, to=10000.0, increment=0.1)  # 设置合理的范围和步长
                widget.delete(0, "end")  # 清空默认值
                widget.insert(0, current_value)
            elif param_type == "boolean":
                # 使用 Checkbutton 进行布尔类型参数输入
                var = tk.BooleanVar()
                var.set(current_value)
                widget = ttk.Checkbutton(self.param_config_area, variable=var)
            elif param_type == "string" and is_multiple_string: # 新增: 类型为 string 且 is_multiple 为 true 时
                widget = scrolledtext.ScrolledText(self.param_config_area, height=5, wrap=tk.WORD) # 使用 ScrolledText 多行文本框
                widget.insert(tk.END, current_value)
            else: # 默认使用 Entry
                widget = ttk.Entry(self.param_config_area)
                widget.insert(0, current_value)

            widget.grid(row=row_num, column=1, sticky="ew", padx=5, pady=5)
            self.param_widgets[param_name] = widget # 存储部件，方便后续获取值
            row_num += 1

        self.param_config_area.columnconfigure(1, weight=1) # 让第二列可以扩展

    def restore_config(self):
        """恢复默认参数配置"""
        self.current_params = self.default_params.copy() # 恢复默认参数
        self.display_params() # 显示参数到界面

    def save_config(self, config_dict=None):
        """保存当前参数配置到 .json 文件, 参数验证"""
        if not self.selected_model:
            messagebox.showerror("错误", "请先选择一个模型")
            return False

        config_data = {}
        config_data["m"] ={"current": os.path.join(self.models_dir_var.get(), self.selected_model)} # 保存模型路径

        for param_name, widget in self.param_widgets.items():
            # 检查 widget 类型
            if isinstance(widget, scrolledtext.ScrolledText):
                param_value_str = widget.get('1.0', tk.END).strip()  # 获取完整文本并去除首尾空格
            elif isinstance(widget, tk.Spinbox):
                param_value_str = widget.get()
                param_type = self.default_params[param_name].get("type")
                if param_type == "float":
                    try:
                        param_value = float(param_value_str)
                    except ValueError:
                        messagebox.showerror("参数错误", f"参数 '{self.default_params[param_name]['desc']} ({param_name})' 必须是浮点数")
                        self.status_label.config(text=f"参数 '{param_name}' 错误: 必须是浮点数", foreground="red")
                        return False
                elif param_type == "integer":
                    try:
                        param_value = int(param_value_str)
                    except ValueError:
                        messagebox.showerror("参数错误", f"参数 '{self.default_params[param_name]['desc']} ({param_name})' 必须是整数")
                        self.status_label.config(text=f"参数 '{param_name}' 错误: 必须是整数", foreground="red")
                        return False
            elif isinstance(widget, ttk.Checkbutton):
                param_type = self.default_params[param_name].get("type")
                if param_type == "boolean":
                    param_value = widget.instate(['selected'])
                else:
                    param_value_str = widget.get()
            else:
                param_value_str = widget.get()

            param_config = self.default_params[param_name] # 获取参数配置信息
            validation_rules = param_config.get("validation")
            config_data[param_name] = {}

            if validation_rules: # 进行参数验证
                validation_type = validation_rules.get("type")
                if validation_type == "integer":
                    try:
                        param_value = int(param_value_str) # 尝试转换为整数
                        min_val = validation_rules.get("min")
                        max_val = validation_rules.get("max")
                        if min_val is not None and param_value < min_val:
                            messagebox.showerror("参数错误", f"参数 '{param_config['desc']} ({param_name})' 必须不小于 {min_val}")
                            self.status_label.config(text=f"参数 '{param_name}' 错误: 值过小", foreground="red")
                            return False # 验证失败
                        if max_val is not None and param_value > max_val:
                            messagebox.showerror("参数错误", f"参数 '{param_config['desc']} ({param_name})' 必须不大于 {max_val}")
                            self.status_label.config(text=f"参数 '{param_name}' 错误: 值过大", foreground="red")
                            return False # 验证失败
                        config_data[param_name]["current"] = param_value # 保存整数值
                    except ValueError:
                        messagebox.showerror("参数错误", f"参数 '{param_config['desc']} ({param_name})' 必须是整数")
                        self.status_label.config(text=f"参数 '{param_name}' 错误: 必须是整数", foreground="red")
                        return False # 验证失败
                elif validation_type == "float":
                    try:
                        param_value = float(param_value_str)  # 尝试转换为浮点数
                        min_val = validation_rules.get("min")
                        max_val = validation_rules.get("max")
                        if min_val is not None and param_value < min_val:
                            messagebox.showerror("参数错误", f"参数 '{param_config['desc']} ({param_name})' 必须不小于 {min_val}")
                            self.status_label.config(text=f"参数 '{param_name}' 错误: 值过小", foreground="red")
                            return False  # 验证失败
                        if max_val is not None and param_value > max_val:
                            messagebox.showerror("参数错误", f"参数 '{param_config['desc']} ({param_name})' 必须不大于 {max_val}")
                            self.status_label.config(text=f"参数 '{param_name}' 错误: 值过大", foreground="red")
                            return False  # 验证失败
                        config_data[param_name]["current"] = param_value  # 保存浮点数值
                    except ValueError:
                        messagebox.showerror("参数错误", f"参数 '{param_config['desc']} ({param_name})' 必须是浮点数")
                        self.status_label.config(text=f"参数 '{param_name}' 错误: 必须是浮点数", foreground="red")
                        return False  # 验证失败
                elif validation_type == "boolean":
                    if not isinstance(param_value, bool):
                        messagebox.showerror("参数错误", f"参数 '{param_config['desc']} ({param_name})' 必须是布尔值")
                        self.status_label.config(text=f"参数 '{param_name}' 错误: 必须是布尔值", foreground="red")
                        return False  # 验证失败
                    config_data[param_name]["current"] = param_value  # 保存布尔值
                else: # 其他验证类型可以继续添加
                    config_data[param_name]["current"] = param_value_str # 默认保存字符串值 (没有验证规则或验证类型不匹配)
            else:
                # 当 validation 为空时，根据 param_type 保存正确的值
                param_type = self.default_params[param_name].get("type")
                if param_type == "float":
                    try:
                        param_value = float(param_value_str)
                        config_data[param_name]["current"] = param_value
                    except ValueError:
                        messagebox.showerror("参数错误", f"参数 '{param_config['desc']} ({param_name})' 必须是浮点数")
                        self.status_label.config(text=f"参数 '{param_name}' 错误: 必须是浮点数", foreground="red")
                        return False
                elif param_type == "integer":
                    try:
                        param_value = int(param_value_str)
                        config_data[param_name]["current"] = param_value
                    except ValueError:
                        messagebox.showerror("参数错误", f"参数 '{param_config['desc']} ({param_name})' 必须是整数")
                        self.status_label.config(text=f"参数 '{param_name}' 错误: 必须是整数", foreground="red")
                        return False
                elif param_type == "boolean":
                    if not isinstance(param_value, bool):
                        messagebox.showerror("参数错误", f"参数 '{param_config['desc']} ({param_name})' 必须是布尔值")
                        self.status_label.config(text=f"参数 '{param_name}' 错误: 必须是布尔值", foreground="red")
                        return False
                    config_data[param_name]["current"] = param_value
                else:
                    config_data[param_name]["current"] = param_value_str

            # 保存到传入的字典中
            if config_dict is not None:
                if param_type != "string": # 非字符串类型的参数，保存 current 值
                    config_dict[param_name] = param_value
                else: # 字符串类型的参数，保存 current 值
                    config_dict[param_name] = param_value_str

        model_name_without_ext = self.selected_model[:-5]
        config_file = os.path.join(self.models_dir_var.get(), f"{model_name_without_ext}.json")

        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4) # 格式化 JSON 输出
            self.status_label.config(text=f"参数已保存到: {config_file}", foreground="green") # 成功信息用绿色
            #messagebox.showinfo("成功", f"参数已保存到: {config_file}")
            return True # 保存成功
        except Exception as e:
            messagebox.showerror("保存失败", f"保存配置文件失败: {e}")
            self.status_label.config(text=f"保存失败: {e}", foreground="red") # 错误信息用红色
            return False # 保存失败

    def launch_server(self):
        """启动 llama-server.exe, 实时日志显示 (使用线程避免UI冻结)"""
        if not self.selected_model:
            messagebox.showerror("错误", "请先选择一个模型")
            return
        if self.process and self.process.poll() is None: # 检查进程是否已经在运行
            messagebox.showinfo("提示", "llama-server 已经在运行中，请先停止")
            return

        config_dict = {}
        if not self.save_config(config_dict): # 启动前先保存配置，如果保存失败则不启动
            return
        
        # print( "config_dict:", config_dict) # 打印 config_dict，方便调试

        command = [self.llama_server_path_var.get()] # 从配置获取 llama-server 路径

        # 添加参数
        for param_name, param_value in config_dict.items():
            # print("param_name:", param_name) # 打印参数名，方便调试
            # print("param_value:", param_value) # 打印参数值，方便调试
            # 忽略模型备注信息
            if param_name == "model_remark":
                continue
            normalized_param_name = re.sub(r'_', '-', param_name)  # 规范化参数名称 (保持不变)

            param_options = PARAM_PREFIX_MAP.get(normalized_param_name)  #  直接获取参数字符串列表，不再使用默认值 "--"
            param_type = DEFAULT_PARAMS.get(param_name, {}).get("type")
            if param_options:  # 确保参数在映射表中存在
                param_string = param_options[0]  # 选择列表中的第一个参数字符串，例如 "-t" 或 "--help"  (通常短参数更常用)
                if param_type == "boolean":
                    if param_value:
                        command.append(param_string)  # 布尔类型仅在值为 True 时添加参数名
                else:
                    command.extend([param_string, str(param_value)])  #  直接使用参数字符串，并将值添加到命令列表中
            else:
                #  如果参数名没有在 param_prefix_map 中找到，则使用默认的 "--" + 规范化参数名 (作为 Fallback 机制，虽然正常情况下不应该发生)
                if param_type == "boolean":
                    if param_value:
                        command.append(f"--{normalized_param_name}")  # 布尔类型仅在值为 True 时添加参数名
                else:
                    command.extend([f"--{normalized_param_name}", str(param_value)])

        # 添加模型路径参数
        command.extend(["-m", os.path.join(self.models_dir_var.get(), self.selected_model)]) # 添加模型路径参数

        print("启动命令:", command) # 打印启动命令，方便调试

        try:
            self.status_label.config(text="Llama-Server 正在启动...", foreground="blue") # 启动中信息用蓝色
            self.log_text.config(state=tk.NORMAL) # 允许编辑日志文本框
            self.log_text.delete("1.0", tk.END) # 清空日志
            self.log_text.config(state=tk.DISABLED) # 重新禁用编辑
            self.launch_button.config(state=tk.DISABLED) # 启动后禁用启动按钮
            self.stop_button.config(state=tk.NORMAL) # 启动后启用停止按钮

            # 创建并启动后台线程执行 _run_llama_server 函数
            thread = threading.Thread(target=self._run_llama_server, args=(command,))
            thread.daemon = True # 设置为守护线程，主线程退出时自动退出
            thread.start()

        except FileNotFoundError:
            messagebox.showerror("错误", f"找不到 llama-server.exe, 请确认 '{self.llama_server_path_var.get()}' 路径是否正确")
            self.status_label.config(text="启动失败: 找不到 llama-server.exe", foreground="red") # 错误信息用红色
        except Exception as e:
            messagebox.showerror("启动错误", f"启动 Llama-Server 失败: {e}")
            self.status_label.config(text=f"启动失败: {e}", foreground="red") # 错误信息用红色
            self.append_log(f"启动异常: {e}", "red") # 记录异常信息到日志

    def _run_llama_server(self, command):
        """后台线程执行 llama-server.exe 和日志更新 (使用线程轮询读取)"""
        try:
            self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace',
                                            creationflags=subprocess.CREATE_NO_WINDOW) # 捕获输出, 创建进程对象,  **添加 encoding 和 errors 参数**

            #  创建两个独立的线程分别读取 stdout 和 stderr
            stdout_thread = threading.Thread(target=self._read_stream, args=(self.process.stdout, "stdout"))
            stderr_thread = threading.Thread(target=self._read_stream, args=(self.process.stderr, "stderr"))
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()


        except Exception as e: # 捕捉线程内部异常，并使用 root.after 更新 UI
            self.root.after(0, self._handle_thread_exception, e) # 调度到主线程处理线程异常

    def _read_stream(self, stream, output_type):
        """后台线程中轮询读取数据流 (stdout 或 stderr)"""
        while True:
            if not self.process or self.process.poll() is not None: # 进程已结束
                break  # 退出线程
            try:
                line = stream.readline() #  使用 readline()，此处虽然是阻塞的，但在线程中，且会频繁检查进程状态
                if line:
                    log_method = self.append_log if output_type == "stdout" else lambda text: self.append_log(text, "red") #  根据输出类型选择不同的日志方法
                    self.root.after(0, log_method, line) # 调度到主线程更新日志
                else: #  readline 返回空字符串表示 EOF 或非阻塞模式下无数据可读 (对于 PIPE,  通常是 EOF)
                    time.sleep(0.01) #  短暂休眠，降低 CPU 占用,  但不要过度休眠，影响实时性
            except ValueError as e: #  捕捉 stream.readline() 可能出现的 ValueError (例如 stream closed)
                print(f"Stream read error ({output_type}): {e}") # 打印错误信息到控制台 (用于调试)
                break # 退出线程
            except Exception as e: #  捕捉其他可能出现的异常，并使用 root.after 报告到主线程
                self.root.after(0, self._handle_thread_exception, f"Stream read error ({output_type}): {e}") # 调度到主线程处理异常
                break # 退出线程

    def _server_process_finished(self):
        """在主线程中处理 llama-server.exe 进程结束事件"""
        if not self.process:
            return # 进程对象为空，可能在异常处理中被清空

        return_code = self.process.returncode # 获取返回码
        self.launch_button.config(state=tk.NORMAL) # 进程结束后启用启动按钮
        self.stop_button.config(state=tk.DISABLED) # 进程结束后禁用停止按钮
        process = self.process #  临时保存 process 对象，避免在设置 self.process = None 之后立即被其他地方访问导致错误
        self.process = None # 清空进程对象

        if return_code == 0:
            self.status_label.config(text="Llama-Server 启动成功并已退出", foreground="green") # 成功信息用绿色
            self.append_log(f"Llama-Server exited with code: {return_code}", "green")
        else:
            self.status_label.config(text=f"Llama-Server 启动失败, 返回码: {return_code}", foreground="red") # 错误信息用红色
            self.append_log(f"Llama-Server exited with code: {return_code}", "red")
            error_output = process.stderr.read() # 读取剩余的错误输出 (虽然 readline 已经读取了，但保险起见)
            if error_output:
                self.append_log(f"[stderr - Full Output on Exit]\n{error_output}", "red")

    def _handle_thread_exception(self, e):
        """在主线程中处理后台线程中发生的异常"""
        messagebox.showerror("线程错误", f"后台线程发生异常: {e}")
        self.status_label.config(text=f"后台线程异常: {e}", foreground="red") # 错误信息用红色
        self.append_log(f"后台线程异常: {e}", "red")
        self.launch_button.config(state=tk.NORMAL) # 启用启动按钮
        self.stop_button.config(state=tk.DISABLED) # 禁用停止按钮
        self.process = None # 清空进程对象

    def stop_server(self):
        """停止 llama-server.exe 进程"""
        if self.process and self.process.poll() is None: # 检查进程是否正在运行
            self.process.terminate() # 发送 SIGTERM 信号
            self.process = None # 清空进程对象 (重要: 在终止进程后清空)
            self.launch_button.config(state=tk.NORMAL) # 停止后启用启动按钮
            self.stop_button.config(state=tk.DISABLED) # 停止后禁用停止按钮
            self.status_label.config(text="Llama-Server 已停止", foreground="black") # 恢复默认颜色
            self.append_log("Llama-Server 停止命令已发送", "orange") #  停止操作用橙色显示
        else:
            messagebox.showinfo("提示", "Llama-Server 没有运行")

    def append_log(self, message, color="black"):
        """追加日志信息到日志文本框"""
        self.log_text.config(state=tk.NORMAL) # 允许编辑
        current_line_count = int(self.log_text.index('end - 1 line').split('.')[0]) # 获取当前行数
        if current_line_count > 2000: # 如果超过 2000 行
            self.log_text.delete("1.0", f"{1000}.end") # 删除前 1000 行 (1.0 到 1000.end)
        self.log_text.tag_config(color, foreground=color) # 配置 tag 颜色
        self.log_text.insert(tk.END, message, color) # 插入带 tag 的文本
        self.log_text.see(tk.END) # 滚动到末尾
        self.log_text.config(state=tk.DISABLED) # 重新禁用编辑

    def _log_system_info(self):
        """在后台线程中输出系统信息到日志"""
        self.append_log("------ Application Configuration ------\n", "blue")
        self.append_log(f"Models Directory: {self.app_config.get('models_dir')}\n")
        self.append_log(f"Llama Server Path: {self.app_config.get('llama_server_path')}\n")
        self.append_log("------------------------------------\n", "blue")

        self.append_log("------ System Information ------\n", "blue")

        try:
            nvidia_smi_output = subprocess.run(["nvidia-smi"], capture_output=True, text=True, check=False)
            if nvidia_smi_output.returncode == 0:
                self.append_log("nvidia-smi Output:\n", "blue")
                self.append_log(nvidia_smi_output.stdout, "green")
            else:
                self.append_log("nvidia-smi 命令执行失败或未安装。\n", "orange")
                self.append_log(f"[stderr] {nvidia_smi_output.stderr}", "red")
        except FileNotFoundError:
            self.append_log("nvidia-smi 命令未找到，请确保已安装 NVIDIA 驱动。\n", "orange")
        except Exception as e:
            self.append_log(f"执行 nvidia-smi 命令时发生异常: {e}\n", "red")

        try:
            nvcc_version_output = subprocess.run(["nvcc", "--version"], capture_output=True, text=True, check=False)
            if nvcc_version_output.returncode == 0:
                self.append_log("nvcc --version Output:\n", "blue")
                self.append_log(nvcc_version_output.stdout, "green")
            else:
                self.append_log("nvcc --version 命令执行失败或未安装。\n", "orange")
                self.append_log(f"[stderr] {nvcc_version_output.stderr}", "red")
        except FileNotFoundError:
            self.append_log("nvcc 命令未找到，请确保已安装 CUDA Toolkit。\n", "orange")
        except Exception as e:
            self.append_log(f"执行 nvcc --version 命令时发生异常: {e}\n", "red")

        self.append_log("----------------------------\n", "blue")

if __name__ == "__main__":
    root = tk.Tk()
    gui = LlamaServerGUI(root)
    root.mainloop()