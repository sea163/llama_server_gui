# Llama.cpp Llama-Server 简单启动器

## 简介

本项目提供一个简单的图形界面，用于启动和管理 Llama.cpp 的 Llama-Server。
它通过 gemini 和 MarsCode AI 快速完成开发

## 功能

-   扫描指定目录下的 .gguf 模型文件，并显示在列表框中。
-   支持双击加载模型配置。
-   根据默认参数显示参数配置界面，支持多种类型参数输入和校验。
-   启动和停止 Llama-Server 进程。
-   实时显示 Llama-Server 的输出日志，支持不同颜色显示。
-   支持最小化到系统托盘。
-   支持将用户配置保存到 json 文件，并从 json 文件加载配置。

## 安装

1.  安装 Python 依赖：

    ```bash
    pip install tkinter pystray pillow
    ```

2.  下载本项目代码。

3.  将 Llama-Server (llama-server.exe) 放到任意目录下，并在本程序中配置路径。

## 使用方法

1.  运行 `llama_server_gui.py`。
2.  在“设置”中配置模型目录和 Llama-Server 路径。
3.  在“模型选择”中选择模型，双击加载配置。
4.  在“参数配置”中修改参数。
5.  点击“启动 Llama-Server”启动服务。
6.  点击“停止 Llama-Server”停止服务。

## 注意事项

-   请确保已安装 Llama.cpp 和 Llama-Server。
-   模型文件 (.gguf) 应放在配置的“模型目录”下。
-   配置文件将保存在 `config` 目录下。

## 改进建议

-   更全面的参数校验。
-   更细致的错误处理。
-   增加日志级别过滤、搜索等功能。
-   使用更美观的 GUI 框架。
-   支持自定义 Llama-Server 文件名。
-   使用更专业的配置管理库。

## 更新

### 2025-05-25

1. **新增功能**  
   - 添加对多模态投影模型路径(`--mmproj`)的支持  
   - 添加对禁用投影加载到GPU(`--no-mmproj-offload`)参数的支持  

2. **参数映射更新**  
   - 在参数映射表中添加对应的命令行参数映射  

3. **功能优化**  
   - 改进模型扫描功能，自动过滤以`mmproj-`开头的文件  


## 作者

本项目作者为 github id: sea163。

## 许可证

本项目使用 GUN AGPLv3 许可证。