# Codex Diary Tool

一个面向个人日记工作流的本地桌面工具。

它把你的录音或原始转写，整理成一份可以直接保存、编译、归档的中文 LaTeX 日记，并且不再依赖 Gemini，而是直接调用本机已经登录好的 `codex`。

## 功能概览

- 粘贴原始文本，直接生成完整 LaTeX 日记
- 导入音频文件，优先使用本地 `faster-whisper` 转写
- 固化日记模板与文风要求
- 自动调用本机 `codex` 生成正文
- 可选自动调用 `XeLaTeX` 编译 PDF
- 统一输出到本地 `outputs/` 目录

## 内置的日记模板约束

工具已经把下面这些规则写死进生成提示词里：

- 文档类：`ctexart`
- 编译器：`XeLaTeX`
- 中文字体：`STXingkai`
- 英文字体：`Times New Roman`
- 页边距：左右 `2.5cm`，上下 `3cm`
- 行距：`1.5`
- 页眉页脚：
  - 左上 `个人日记`
  - 右上为日期
  - 页脚中间为页码
- 标题需要概括当天核心主题
- 正文采用更清晰的大纲式结构
- 每个重点有独立标题与独立段落
- 在必要处插入少量 `Codex comment:`
- 文风保持理性、克制、工科生式反思
- 自动去除 `cite` 之类的噪音标记
- 文末保留较小字号的 `Codex近日总结：`

## 运行方式

### 方式 1：双击启动

直接运行：

`run_codex_diary_tool.bat`

### 方式 2：命令行启动

```powershell
python app.py
```

## 打包为 Windows 可执行文件

项目已经包含打包脚本：

`build_windows_release.bat`

双击运行后，会调用 `PyInstaller` 生成一个更适合分发的 Windows 成品目录：

```text
dist/
  CodexDiaryTool/
    CodexDiaryTool.exe
    outputs/
    ...
```

当前采用的是 `--onedir` 方案，而不是 `--onefile`。

这样做的原因是：

- GUI 启动更稳定
- 对 `faster-whisper` 这类依赖更友好
- 出问题时更容易排查
- 更适合后续继续加入资源文件和图标

## 使用步骤

1. 填写日期
2. 选择简体或繁体
3. 设置最低页数
4. 设置正文中的 `Codex comment` 密度
5. 选择输入方式：
   - 直接粘贴原始转写文本
   - 导入音频文件后先转写
6. 如有额外要求，写到“额外要求”输入框
7. 点击“开始生成”
8. 结果会保存为 `.tex`，并可选自动生成 `.pdf`

## 技术实现

### 文本生成

- 使用本机 `codex exec`
- 默认模型：`gpt-5.4`
- 不通过聊天网页复制粘贴，而是直接由本地程序调用

### 音频转写

- 优先走本地 `faster-whisper`
- 默认使用 `base` 模型
- 自动设置 `HF_ENDPOINT=https://hf-mirror.com`，提升模型下载可用性
- 如果本地转写失败，会退回到在线转写

### PDF 编译

- 使用本机 `xelatex`
- 编译后的 PDF 与 `.tex` 放在同一输出目录

## 依赖环境

- Python 3.12+
- 本机可用的 `codex`
- 本机可用的 `xelatex`
- Windows 环境下建议已安装 `ffmpeg`
- 如果要打包，需要本机安装 `PyInstaller`

Python 依赖见：

`requirements.txt`

## 目录结构

```text
codex-diary-tool/
  app.py
  run_codex_diary_tool.bat
  requirements.txt
  README.md
  outputs/
```

## 输出说明

生成后的文件会放在：

`outputs/`

常见产物包括：

- 转写文本 `.txt`
- 日记源文件 `.tex`
- 编译结果 `.pdf`

## 可定制项

如果你以后想继续调整风格，可以修改 `app.py` 里的 `build_prompt()`，比如：

- 把 `Codex comment:` 改成别的标签
- 把 `Codex近日总结：` 改成你想要的标题
- 加强或减弱扩写力度
- 改成只输出简体或只输出繁体

## 备注

这个工具的目标不是“泛用写作助手”，而是把一套已经稳定下来的个人日记工作流本地化、固化、可重复运行。
