# AI-Diary-Tool

<div align="center">

[简体中文](#zh-cn) | [繁體中文](#zh-tw) | [English](#english) | [Français](#francais)

</div>

<a id="zh-cn"></a>
## 简体中文

AI-Diary-Tool 是一个本地桌面工具，用来把原始日记素材整理成结构化的 LaTeX 日记，并按需编译为 PDF。

它适合这样的流程：

- 先写下零散想法或语音转写内容
- 再让工具整理成更适合长期保存的正式日记
- 最后输出 `.tex`，并可选编译为 `.pdf`

这个项目使用本机的 `codex` 工作流生成正文，不依赖 Gemini。

### 主要功能

- 支持直接粘贴原始文本生成日记
- 支持导入音频并先转写，再生成日记
- 优先使用本地 `faster-whisper` 转写，失败时回退到 OpenAI 在线转写
- 自动生成完整 LaTeX 文档，而不是只生成正文片段
- 可选调用 `XeLaTeX` 编译 PDF
- 提供图形界面，适合日常个人使用

### 实际工作流

1. 输入日期
2. 选择简体或繁体输出
3. 设定最低页数
4. 设定 `Codex comment` 的插入密度
5. 粘贴原始内容，或导入音频文件
6. 可在“额外要求”中补充风格或格式偏好
7. 点击“开始生成”
8. 工具保存 `.tex`，并可选继续生成 `.pdf`

### 依赖要求

- Python 3.12+
- 本机可用的 `codex.cmd`
- 可读取的 `~/.codex/auth.json`
- 如果要编译 PDF，需要本机可用的 `xelatex`
- 如果要用本地 Whisper 转写，建议系统中可用 `ffmpeg`
- 如果要打包 Windows 可执行文件，需要 `PyInstaller`

Python 依赖见 [requirements.txt](requirements.txt)：

```text
openai>=2.30.0
faster-whisper>=1.2.1
```

安装示例：

```powershell
pip install -r requirements.txt
```

### 认证与模型

程序会从下面的位置读取 OpenAI API Key：

```text
~/.codex/auth.json
```

需要存在字段：

```json
{
  "OPENAI_API_KEY": "..."
}
```

代码中当前使用的模型策略：

- 日记生成模型：`gpt-5.4`
- 在线转写模型：`gpt-4o-mini-transcribe`
- 本地 Whisper 默认模型：`base`

可通过环境变量覆盖本地 Whisper 模型：

```powershell
$env:CODEX_DIARY_WHISPER_MODEL="small"
python app.py
```

如果你需要镜像源，也可以设置：

```powershell
$env:HF_ENDPOINT="https://hf-mirror.com"
```

### 运行方式

直接双击：

`run_ai_diary_tool.bat`

或者命令行运行：

```powershell
python app.py
```

### 输出位置

程序优先尝试把输出写到：

```text
H:\OneDrive\Desktop\日記
```

如果这个目录不可用，则自动回退到项目目录下的：

```text
outputs/
```

常见输出文件包括：

- `transcript_*.txt`
- `*.tex`
- `*.pdf`

### 内置排版特点

- 文档类固定为 `ctexart`
- 编译器目标是 `XeLaTeX`
- 中文主字体为 `STXingkai`
- 英文字体为 `Times New Roman`
- 页边距固定为左右 `2.5cm`、上下 `3cm`
- 行距固定为 `1.5`
- 页眉页脚中包含日期与页码
- 标题和正文会被重组为更清晰的大纲结构
- 末尾保留一个较小字号的总结模块

### 构建 Windows 可执行文件

项目内已经包含：

`build_windows_release.bat`

运行后会生成：

```text
dist/
  AI-Diary-Tool/
    AI-Diary-Tool.exe
    outputs/
    ...
```

当前使用 `--onedir` 模式打包，以减少 GUI、Whisper 相关依赖造成的不稳定问题。

### 项目结构

```text
AI-Diary-Tool/
  app.py
  requirements.txt
  run_ai_diary_tool.bat
  build_windows_release.bat
  README.md
```

### 常见问题

#### 1. 启动后提示找不到 Codex

请确认本机命令行中可以直接运行：

```powershell
codex.cmd --help
```

#### 2. 提示缺少 `OPENAI_API_KEY`

请确认 `~/.codex/auth.json` 存在，且包含 `OPENAI_API_KEY`。

#### 3. PDF 编译失败

请确认本机已安装 `xelatex`，并且命令行可直接调用。

#### 4. 音频转写失败

程序会先尝试本地 `faster-whisper`，失败后再回退到 OpenAI 在线转写。
如果本地模式不稳定，通常与模型下载、网络镜像或 `ffmpeg` 环境有关。

#### 5. 输出目录不在项目文件夹里

这是当前代码的设计行为：优先输出到 `H:\OneDrive\Desktop\日記`，只有该目录不可用时才回退到项目目录下的 `outputs/`。

---

<a id="zh-tw"></a>
## 繁體中文

AI-Diary-Tool 是一個本地桌面工具，用來把原始日記素材整理成結構化的 LaTeX 日記，並按需編譯成 PDF。

它適合這樣的流程：

- 先記下零散想法或語音轉寫內容
- 再把內容整理成更適合長期保存的正式日記
- 最後輸出 `.tex`，並可選擇編譯成 `.pdf`

這個專案使用本機的 `codex` 工作流生成正文，不依賴 Gemini。

### 主要功能

- 支援直接貼上原始文字生成日記
- 支援匯入音訊並先轉寫，再生成日記
- 優先使用本地 `faster-whisper` 轉寫，失敗時回退到 OpenAI 線上轉寫
- 自動生成完整 LaTeX 文件，而不是只生成正文片段
- 可選呼叫 `XeLaTeX` 編譯 PDF
- 提供圖形介面，適合日常個人使用

### 實際工作流

1. 輸入日期
2. 選擇簡體或繁體輸出
3. 設定最低頁數
4. 設定 `Codex comment` 的插入密度
5. 貼上原始內容，或匯入音訊檔
6. 可在「額外要求」中補充風格或格式偏好
7. 點擊「開始生成」
8. 工具保存 `.tex`，並可選繼續生成 `.pdf`

### 依賴需求

- Python 3.12+
- 本機可用的 `codex.cmd`
- 可讀取的 `~/.codex/auth.json`
- 若要編譯 PDF，需要本機可用的 `xelatex`
- 若要使用本地 Whisper 轉寫，建議系統中可用 `ffmpeg`
- 若要打包 Windows 可執行檔，需要 `PyInstaller`

Python 依賴見 [requirements.txt](requirements.txt)：

```text
openai>=2.30.0
faster-whisper>=1.2.1
```

安裝示例：

```powershell
pip install -r requirements.txt
```

### 認證與模型

程式會從下面的位置讀取 OpenAI API Key：

```text
~/.codex/auth.json
```

需要存在字段：

```json
{
  "OPENAI_API_KEY": "..."
}
```

目前程式中的模型策略：

- 日記生成模型：`gpt-5.4`
- 線上轉寫模型：`gpt-4o-mini-transcribe`
- 本地 Whisper 預設模型：`base`

可透過環境變數覆寫本地 Whisper 模型：

```powershell
$env:CODEX_DIARY_WHISPER_MODEL="small"
python app.py
```

如果需要鏡像源，也可以設定：

```powershell
$env:HF_ENDPOINT="https://hf-mirror.com"
```

### 執行方式

直接雙擊：

`run_ai_diary_tool.bat`

或用命令列執行：

```powershell
python app.py
```

### 輸出位置

程式會優先嘗試把輸出寫到：

```text
H:\OneDrive\Desktop\日記
```

如果這個目錄不可用，則會自動回退到專案目錄下的：

```text
outputs/
```

常見輸出檔包括：

- `transcript_*.txt`
- `*.tex`
- `*.pdf`

### 內建排版特點

- 文件類固定為 `ctexart`
- 編譯器目標是 `XeLaTeX`
- 中文主字體為 `STXingkai`
- 英文字體為 `Times New Roman`
- 頁邊距固定為左右 `2.5cm`、上下 `3cm`
- 行距固定為 `1.5`
- 頁眉頁腳中包含日期與頁碼
- 標題和正文會被重組成更清晰的大綱結構
- 文末保留一個較小字號的總結模組

### 建置 Windows 可執行檔

專案內已包含：

`build_windows_release.bat`

執行後會生成：

```text
dist/
  AI-Diary-Tool/
    AI-Diary-Tool.exe
    outputs/
    ...
```

目前使用 `--onedir` 模式打包，以降低 GUI 與 Whisper 相關依賴造成的不穩定問題。

### 專案結構

```text
AI-Diary-Tool/
  app.py
  requirements.txt
  run_ai_diary_tool.bat
  build_windows_release.bat
  README.md
```

### 常見問題

#### 1. 啟動後提示找不到 Codex

請確認本機命令列中可以直接執行：

```powershell
codex.cmd --help
```

#### 2. 提示缺少 `OPENAI_API_KEY`

請確認 `~/.codex/auth.json` 存在，且包含 `OPENAI_API_KEY`。

#### 3. PDF 編譯失敗

請確認本機已安裝 `xelatex`，並且命令列可直接呼叫。

#### 4. 音訊轉寫失敗

程式會先嘗試本地 `faster-whisper`，失敗後再回退到 OpenAI 線上轉寫。
如果本地模式不穩定，通常與模型下載、網路鏡像或 `ffmpeg` 環境有關。

#### 5. 輸出目錄不在專案資料夾裡

這是目前程式的設計行為：優先輸出到 `H:\OneDrive\Desktop\日記`，只有該目錄不可用時才回退到專案目錄下的 `outputs/`。

---

<a id="english"></a>
## English

AI-Diary-Tool is a local desktop app for turning rough diary material into structured LaTeX diary entries, with optional PDF compilation.

It is designed for a workflow like this:

- capture raw thoughts or a voice memo
- clean and structure the content into a proper diary entry
- save the result as `.tex`
- optionally compile it into `.pdf`

This project uses the local `codex` workflow available on your machine. It does not use Gemini.

### Features

- Paste raw text and generate a diary entry directly
- Import an audio file and transcribe it before generation
- Prefer local `faster-whisper` transcription, with OpenAI fallback if local transcription fails
- Generate a complete LaTeX document instead of only body text
- Optionally compile the result with `XeLaTeX`
- Provide a desktop GUI for daily personal use

### Actual Workflow

1. Enter the date
2. Choose simplified or traditional Chinese output
3. Set the minimum page count
4. Set the density of `Codex comment` blocks
5. Paste raw content or import an audio file
6. Add extra stylistic or formatting requirements if needed
7. Click the generate button
8. Save the result as `.tex`, with optional `.pdf` output

### Requirements

- Python 3.12+
- A working local `codex.cmd`
- A readable `~/.codex/auth.json`
- A working local `xelatex` if you want PDF output
- `ffmpeg` is recommended for local Whisper transcription
- `PyInstaller` is required if you want to rebuild the Windows executable

Python dependencies are listed in [requirements.txt](requirements.txt):

```text
openai>=2.30.0
faster-whisper>=1.2.1
```

Install example:

```powershell
pip install -r requirements.txt
```

### Authentication and Models

The app loads the OpenAI API key from:

```text
~/.codex/auth.json
```

It expects:

```json
{
  "OPENAI_API_KEY": "..."
}
```

Current model choices in the code:

- diary generation: `gpt-5.4`
- online transcription: `gpt-4o-mini-transcribe`
- default local Whisper model: `base`

You can override the local Whisper model with:

```powershell
$env:CODEX_DIARY_WHISPER_MODEL="small"
python app.py
```

If you need a Hugging Face mirror:

```powershell
$env:HF_ENDPOINT="https://hf-mirror.com"
```

### Run

Double-click:

`run_ai_diary_tool.bat`

Or run from the command line:

```powershell
python app.py
```

### Output Location

The app first tries to write output into:

```text
H:\OneDrive\Desktop\日記
```

If that directory is unavailable, it falls back to:

```text
outputs/
```

Common outputs include:

- `transcript_*.txt`
- `*.tex`
- `*.pdf`

### Built-in Formatting Behavior

- document class: `ctexart`
- target compiler: `XeLaTeX`
- Chinese main font: `STXingkai`
- English font: `Times New Roman`
- margins: `2.5cm` left/right and `3cm` top/bottom
- line spacing: `1.5`
- headers and footers include date and page number
- the generated diary is reorganized into a clearer outline structure
- a smaller summary block is kept at the end

### Build a Windows Executable

The project already includes:

`build_windows_release.bat`

It generates:

```text
dist/
  AI-Diary-Tool/
    AI-Diary-Tool.exe
    outputs/
    ...
```

The current build uses `--onedir` mode to reduce instability around the GUI and Whisper-related dependencies.

### Project Structure

```text
AI-Diary-Tool/
  app.py
  requirements.txt
  run_ai_diary_tool.bat
  build_windows_release.bat
  README.md
```

### Troubleshooting

#### 1. Codex is not found

Make sure this works on your machine:

```powershell
codex.cmd --help
```

#### 2. `OPENAI_API_KEY` is missing

Make sure `~/.codex/auth.json` exists and contains `OPENAI_API_KEY`.

#### 3. PDF compilation fails

Make sure `xelatex` is installed and callable from the command line.

#### 4. Audio transcription fails

The app tries local `faster-whisper` first, then falls back to OpenAI transcription.
If local transcription is unstable, the problem is often related to model download, mirror settings, or `ffmpeg`.

#### 5. Output does not go into the repo folder

This is the current code behavior: it prefers `H:\OneDrive\Desktop\日記` and only falls back to the local `outputs/` folder when that path is unavailable.

---

<a id="francais"></a>
## Français

AI-Diary-Tool est une application de bureau locale qui transforme des notes de journal brutes en entrées structurées en LaTeX, avec compilation PDF en option.

Le flux visé est le suivant :

- capturer des idées brutes ou une note vocale
- restructurer le contenu en une vraie entrée de journal
- enregistrer le résultat en `.tex`
- compiler éventuellement en `.pdf`

Ce projet utilise le flux `codex` disponible sur votre machine. Il n'utilise pas Gemini.

### Fonctionnalités

- Coller un texte brut et générer directement une entrée de journal
- Importer un fichier audio puis le transcrire avant génération
- Utiliser en priorité `faster-whisper` en local, avec repli vers OpenAI si l'étape locale échoue
- Générer un document LaTeX complet, et non un simple fragment de texte
- Compiler le résultat avec `XeLaTeX` en option
- Fournir une interface graphique adaptée à un usage personnel quotidien

### Flux réel d'utilisation

1. Saisir la date
2. Choisir une sortie en chinois simplifié ou traditionnel
3. Définir un nombre minimum de pages
4. Régler la densité des blocs `Codex comment`
5. Coller le contenu brut ou importer un fichier audio
6. Ajouter des contraintes de style ou de format si nécessaire
7. Cliquer sur le bouton de génération
8. Enregistrer le résultat en `.tex`, avec sortie `.pdf` en option

### Dépendances

- Python 3.12+
- Un `codex.cmd` fonctionnel en local
- Un fichier `~/.codex/auth.json` lisible
- Un `xelatex` fonctionnel si vous souhaitez produire un PDF
- `ffmpeg` est recommandé pour la transcription locale via Whisper
- `PyInstaller` est requis pour reconstruire l'exécutable Windows

Les dépendances Python sont listées dans [requirements.txt](requirements.txt) :

```text
openai>=2.30.0
faster-whisper>=1.2.1
```

Exemple d'installation :

```powershell
pip install -r requirements.txt
```

### Authentification et modèles

L'application lit la clé API OpenAI depuis :

```text
~/.codex/auth.json
```

Elle attend :

```json
{
  "OPENAI_API_KEY": "..."
}
```

Choix actuels des modèles dans le code :

- génération du journal : `gpt-5.4`
- transcription en ligne : `gpt-4o-mini-transcribe`
- modèle Whisper local par défaut : `base`

Vous pouvez remplacer le modèle Whisper local avec :

```powershell
$env:CODEX_DIARY_WHISPER_MODEL="small"
python app.py
```

Si vous avez besoin d'un miroir Hugging Face :

```powershell
$env:HF_ENDPOINT="https://hf-mirror.com"
```

### Exécution

Double-cliquez sur :

`run_ai_diary_tool.bat`

Ou lancez :

```powershell
python app.py
```

### Emplacement de sortie

L'application essaie d'abord d'écrire les fichiers dans :

```text
H:\OneDrive\Desktop\日記
```

Si ce dossier n'est pas disponible, elle se replie vers :

```text
outputs/
```

Les sorties typiques comprennent :

- `transcript_*.txt`
- `*.tex`
- `*.pdf`

### Comportement de mise en forme

- classe du document : `ctexart`
- compilateur visé : `XeLaTeX`
- police chinoise principale : `STXingkai`
- police anglaise : `Times New Roman`
- marges : `2.5cm` à gauche/droite et `3cm` en haut/bas
- interligne : `1.5`
- en-têtes et pieds de page avec date et numéro de page
- réorganisation du journal en un plan plus lisible
- présence d'un bloc final de synthèse en plus petit corps

### Construction de l'exécutable Windows

Le projet contient déjà :

`build_windows_release.bat`

Ce script génère :

```text
dist/
  AI-Diary-Tool/
    AI-Diary-Tool.exe
    outputs/
    ...
```

Le mode actuel est `--onedir`, afin de limiter les problèmes liés à l'interface graphique et aux dépendances de Whisper.

### Structure du projet

```text
AI-Diary-Tool/
  app.py
  requirements.txt
  run_ai_diary_tool.bat
  build_windows_release.bat
  README.md
```

### Dépannage

#### 1. Codex est introuvable

Vérifiez que ceci fonctionne :

```powershell
codex.cmd --help
```

#### 2. `OPENAI_API_KEY` est manquant

Vérifiez que `~/.codex/auth.json` existe et contient bien `OPENAI_API_KEY`.

#### 3. La compilation PDF échoue

Vérifiez que `xelatex` est installé et accessible en ligne de commande.

#### 4. La transcription audio échoue

L'application essaie d'abord `faster-whisper` en local, puis se replie vers OpenAI.
Si le mode local est instable, le problème vient souvent du téléchargement du modèle, du miroir réseau ou de `ffmpeg`.

#### 5. Les fichiers ne sortent pas dans le dossier du projet

C'est le comportement actuel du code : il privilégie `H:\OneDrive\Desktop\日記` et ne revient à `outputs/` que si ce chemin n'est pas disponible.
