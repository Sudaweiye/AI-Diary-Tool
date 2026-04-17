import json
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from openai import OpenAI

try:
    from faster_whisper import WhisperModel
except ImportError:  # pragma: no cover - optional dependency
    WhisperModel = None


if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
else:
    APP_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = Path(r"H:\OneDrive\Desktop\日記")
try:
    OUTPUT_DIR = DEFAULT_OUTPUT_DIR
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    OUTPUT_DIR = APP_DIR / "outputs"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


TRANSCRIPTION_MODEL = "gpt-4o-mini-transcribe"
CODEX_MODEL = "gpt-5.4"
LOCAL_WHISPER_MODEL = os.getenv("CODEX_DIARY_WHISPER_MODEL", "base")
HF_MIRROR = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")


def load_codex_api_key() -> str:
    auth_path = Path.home() / ".codex" / "auth.json"
    if not auth_path.exists():
        raise FileNotFoundError(f"Missing Codex auth file: {auth_path}")
    data = json.loads(auth_path.read_text(encoding="utf-8"))
    api_key = data.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY was not found in ~/.codex/auth.json")
    return api_key


def cleanup_codex_output(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:latex)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = re.sub(r"\[cite:[^\]]+\]", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace("\ufffd", "")
    return cleaned.strip()


def make_filename_slug(text: str) -> str:
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "", text)
    safe = safe.replace(" ", "_").strip("._")
    return safe or "diary"


def sanitize_source_text(text: str) -> str:
    cleaned = text.replace("\ufeff", "")
    cleaned = cleaned.replace("\ufffd", "�")
    cleaned = re.sub(r"�{2,}", "[乱码]", cleaned)
    cleaned = re.sub(r"(?<=[\u4e00-\u9fff])�(?=[\u4e00-\u9fff])", "[乱码]", cleaned)
    cleaned = cleaned.replace("�", "")
    cleaned = re.sub(r"\r\n?", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def format_date_with_weekday(raw_date: str) -> tuple[str, str]:
    raw_date = raw_date.strip()
    weekday_names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    try:
        parsed = datetime.strptime(raw_date, "%Y-%m-%d")
    except ValueError:
        return raw_date, ""
    display_date = f"{parsed.year} 年 {parsed.month} 月 {parsed.day} 日"
    weekday = weekday_names[parsed.weekday()]
    return display_date, weekday


def normalize_generated_latex(latex: str, request: "DiaryRequest") -> str:
    title_prefix = "日记： " if request.script == "simplified" else "日記： "
    header_date = request.display_date
    date_line = request.display_date
    if request.weekday_text:
        date_line = f"{request.display_date} \\quad {request.weekday_text}"

    def fix_title(match: re.Match[str]) -> str:
        title = match.group(1).strip()
        if title.startswith("日记："):
            title = "日记： " + title[len("日记：") :].lstrip()
        elif title.startswith("日記："):
            title = "日記： " + title[len("日記：") :].lstrip()
        else:
            title = title_prefix + title
        return "{\\LARGE \\textbf{" + title + "}} \\\\"

    latex = re.sub(
        r"\{\\LARGE\s+\\textbf\{(.*?)\}\}\s*\\\\",
        fix_title,
        latex,
        count=1,
        flags=re.DOTALL,
    )
    latex = re.sub(r"\\rhead\{.*?\}", lambda _match: f"\\rhead{{{header_date}}}", latex, count=1)
    latex = re.sub(
        r"\{\\large\s+.*?\}",
        lambda _match: f"{{\\large {date_line}}}",
        latex,
        count=1,
        flags=re.DOTALL,
    )
    return latex


def build_prompt(data: "DiaryRequest") -> str:
    script_name = "简体中文" if data.script == "simplified" else "繁体中文"
    title_prefix = "日记： " if data.script == "simplified" else "日記： "
    comment_mode_text = {
        "none": "不要在正文中加入额外评论模块。",
        "some": "可以在正文中少量加入明显标注的 `Codex comment:` 段落，点到为止。",
        "more": "在正文中加入较多、但仍然自然且服务于内容推进的 `Codex comment:` 段落。",
    }[data.comment_mode]

    summary_label = "Codex近日总结："
    comment_label = "Codex comment:"

    transcript_block = data.transcript.strip()

    return f"""
你要把用户提供的日记原始内容整理成一份可直接编译的、完整的 LaTeX 代码。

硬性要求：
1. 只输出 LaTeX 源码，不要输出解释，不要加 Markdown 代码块。
2. 必须输出完整文档，包含 \\documentclass 到 \\end{{document}}。
3. 使用 XeLaTeX 可编译的配置。
4. 文档类固定为 ctexart。
5. 页面设置固定：
   - A4
   - 左右边距 2.5cm
   - 上下边距 3cm
6. 行距固定为 1.5 倍。
7. 英文字体固定为 Times New Roman。
8. 中文字体固定为 STXingkai，并使用 \\setCJKmainfont[AutoFakeBold=true]{{STXingkai}}。
9. 页眉页脚固定：
   - 左上：个人日记
   - 右上：{data.display_date}
   - 页脚中间：页码
10. 主标题必须以 `{title_prefix}` 开头，冒号后必须保留一个空格；标题不能空泛，必须概括这一天最核心的矛盾、事件或反思。
11. 语言统一使用：{script_name}。
12. 文风要求：
   - 理性、克制、工科生式反思
   - 不矫情、不装可爱、不刻意卖萌
   - 尽量保留原意和原本的思维路径
   - 去掉明显口语赘词、重复、语音识别噪音
   - 可以适度润色，但不要改写成完全不像原作者
   - 不要虚构原文中没有出现的具体事件、数字、人物或背景细节
13. 必须去掉所有类似 [cite: 1]、[cite: 11] 的标记。
14. 文末必须保留一个较小字号的总结模块，标题固定写成：{summary_label}
15. {comment_mode_text}
16. 如果正文中加入评论段落，标签固定写成：{comment_label}
17. 最低长度要求：不少于 {data.min_pages} 页。
18. 重点优先遵守用户在原文中已经稳定表达出的格式偏好。
19. 不要把正文写成一整篇无分层的大散文，必须做清晰的大纲化组织。
20. 每一个重点都必须有独立的小节标题和独立段落。
21. comments 只在你认为确实有必要的地方插入，不要机械地每节都加。
22. comments 应该紧跟相关段落之后，起到点明、提炼或提醒作用，而不是喧宾夺主。
23. 整体应比之前那种过度扩写、长段连续推进的写法更清晰、更利于回看。
24. 日期行必须明确写出星期几，不能缺失。
25. 如果输入日期可解析，正文标题下的日期行固定写成：`{data.display_date} \\quad {data.weekday_text}`。
26. 如果原始内容中出现类似 `���`、`�`、乱码占位符或明显损坏字符，不要原样保留，应结合上下文谨慎清理；无法安全还原时，宁可删除坏字符，也不要把乱码写进最终稿。
27. 页眉右上角日期与标题下日期行，都必须使用带空格的中文日期格式，例如：`2026 年 4 月 15 日`，不要写成 `2026年4月15日`。
28. 中文与英文、数字、缩写混排时，该有空格的地方要有空格，尽量参考用户给出的样例排版；例如 `CS50 AI`、`API`、`Bug`、`FedDrop` 等前后与中文衔接时应自然留白。
29. 总体版式应尽量接近用户示例：标题为 `日记： 主题` 或 `日記： 主題`，日期行单独居中显示，星期几不可缺失。

排版模板必须接近下面这些固定结构：
- 使用 geometry、setspace、fontspec、fancyhdr
- 标题居中，日期单独一行
- 日期单独一行时必须带星期几
- 正文后有一条横线
- 总结部分用 \\small 并适度缩小行距
- 正文主体请优先使用 `\\section*{{一、...}}`、`\\section*{{二、...}}` 这样的层级结构
- 如有必要，可在某一节内部再用 `\\subsection*{{...}}`，但不要过度切碎
- 标题下日期行请使用 `{data.display_date} \\quad {data.weekday_text}` 这一视觉风格

写作目标：
- 让成品像“自己会保存的正式日记”
- 逻辑要清晰，段落过渡自然
- 如果原文本身比较碎，请主动重组结构
- 如果原文内容比较少，但用户要求页数较长，可以在不背离原意的前提下深度扩写、补充分析与反思
- 但即使扩写，也必须优先保证结构感，而不是单纯拉长篇幅
- 扩写时只能沿着原文已经出现的主题、判断和情绪展开，不能自行编造新事实

推荐结构：
1. 开头只用 1 到 2 段，简明交代当天背景与总感受
2. 正文拆成 3 到 6 个重点小节
3. 每个小节围绕一个明确主题展开
4. 每个小节通常控制在 2 到 4 段
5. 如果某一节特别重要，可以更长，但不要让全文失去层次
6. 文末收束，再进入 {summary_label}

额外风格要求：
- 不要生成过长的 LaTeX 冗余结构
- 不要加入太多无关宏包，前导区尽量简洁
- 不要把 comments 写得比正文更抢戏
- comments 的数量应控制，通常 1 到 3 处即可，除非用户明确要求多一些
- 小节标题要概括性强，能一眼看出该段重点
- 各小节之间应尽量避免内容重复
- 如果原文本身已经有几个明确主题，请优先沿着那些主题组织大纲

用户参数：
- 日期：{data.display_date}
- 星期：{data.weekday_text or "未提供"}
- 页数要求：不少于 {data.min_pages} 页
- 正文字内评论模式：{data.comment_mode}
- 额外补充要求：{data.extra_requirements or "无"}

下面是需要整理的原始内容，请据此生成最终 LaTeX：

{transcript_block}
""".strip()


@dataclass
class DiaryRequest:
    display_date: str
    weekday_text: str
    script: str
    min_pages: int
    comment_mode: str
    extra_requirements: str
    transcript: str


class DiaryGenerator:
    def __init__(self) -> None:
        self.api_key = load_codex_api_key()
        self.openai_client = OpenAI(api_key=self.api_key, timeout=120.0)
        self._whisper_model = None
        self.last_transcription_backend = "unknown"

    def _get_local_whisper(self):
        if WhisperModel is None:
            raise RuntimeError("faster-whisper is not installed.")
        if self._whisper_model is None:
            os.environ.setdefault("HF_ENDPOINT", HF_MIRROR)
            os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
            self._whisper_model = WhisperModel(
                LOCAL_WHISPER_MODEL,
                device="cpu",
                compute_type="int8",
            )
        return self._whisper_model

    def _transcribe_audio_locally(self, audio_path: Path) -> str:
        model = self._get_local_whisper()
        segments, _info = model.transcribe(str(audio_path), beam_size=5)
        text = "".join(segment.text for segment in segments).strip()
        if not text:
            raise RuntimeError("Local Whisper returned empty text.")
        return text

    def transcribe_audio(self, audio_path: Path) -> str:
        try:
            text = self._transcribe_audio_locally(audio_path)
            self.last_transcription_backend = f"local-whisper:{LOCAL_WHISPER_MODEL}"
            return text
        except Exception as local_exc:
            with audio_path.open("rb") as f:
                result = self.openai_client.audio.transcriptions.create(
                    model=TRANSCRIPTION_MODEL,
                    file=f,
                )
            text = getattr(result, "text", None)
            if not text:
                raise RuntimeError(
                    "Audio transcription failed locally and online returned empty text. "
                    f"Local error: {local_exc}"
                )
            self.last_transcription_backend = "online-openai"
            return text.strip()

    def generate_latex(self, request: DiaryRequest, logger) -> str:
        prompt = build_prompt(request)
        with tempfile.TemporaryDirectory(prefix="codex-diary-") as temp_dir:
            out_file = Path(temp_dir) / "last_message.txt"
            command = [
                "codex.cmd",
                "exec",
                "--skip-git-repo-check",
                "--color",
                "never",
                "--model",
                CODEX_MODEL,
                "--sandbox",
                "read-only",
                "--cd",
                temp_dir,
                "--output-last-message",
                str(out_file),
                "-",
            ]
            logger("正在调用 Codex 生成 LaTeX ...")
            result = subprocess.run(
                command,
                input=prompt,
                text=True,
                capture_output=True,
                encoding="utf-8",
            )
            if result.returncode != 0:
                raise RuntimeError(
                    "Codex 生成失败。\n\nSTDOUT:\n"
                    + result.stdout
                    + "\n\nSTDERR:\n"
                    + result.stderr
                )
            if not out_file.exists():
                raise RuntimeError("Codex 已执行，但没有找到输出文件。")
            latex = cleanup_codex_output(out_file.read_text(encoding="utf-8"))
            latex = normalize_generated_latex(latex, request)
            if "\\documentclass" not in latex or "\\end{document}" not in latex:
                raise RuntimeError("Codex 返回的内容不是完整的 LaTeX 文档。")
            return latex

    def compile_pdf(self, tex_path: Path, logger) -> Path:
        logger("正在使用 XeLaTeX 编译 PDF ...")
        command = [
            "xelatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-output-directory={tex_path.parent}",
            str(tex_path),
        ]
        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            encoding="utf-8",
        )
        if result.returncode != 0:
            raise RuntimeError(
                "XeLaTeX 编译失败。\n\nSTDOUT:\n"
                + result.stdout
                + "\n\nSTDERR:\n"
                + result.stderr
            )
        pdf_path = tex_path.with_suffix(".pdf")
        if not pdf_path.exists():
            raise RuntimeError("编译命令已执行，但未生成 PDF。")
        return pdf_path


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("AI-Diary-Tool")
        self.root.geometry("1380x900")

        self.generator = DiaryGenerator()
        self.log_queue: "queue.Queue[str]" = queue.Queue()
        self.worker: threading.Thread | None = None

        self.date_var = tk.StringVar(value=str(date.today()))
        self.script_var = tk.StringVar(value="simplified")
        self.pages_var = tk.IntVar(value=4)
        self.comment_var = tk.StringVar(value="some")
        self.audio_var = tk.StringVar(value="")
        self.compile_pdf_var = tk.BooleanVar(value=True)

        self._build_ui()
        self._poll_logs()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main = ttk.Frame(self.root, padding=12)
        main.grid(sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(2, weight=1)
        main.rowconfigure(4, weight=1)

        top = ttk.LabelFrame(main, text="日记参数", padding=10)
        top.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        for i in range(6):
            top.columnconfigure(i, weight=1)

        ttk.Label(top, text="日期 (YYYY-MM-DD)").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.date_var).grid(row=1, column=0, sticky="ew", padx=(0, 8))

        ttk.Label(top, text="文字").grid(row=0, column=1, sticky="w")
        script_box = ttk.Combobox(
            top,
            textvariable=self.script_var,
            state="readonly",
            values=["simplified", "traditional"],
        )
        script_box.grid(row=1, column=1, sticky="ew", padx=(0, 8))

        ttk.Label(top, text="最低页数").grid(row=0, column=2, sticky="w")
        ttk.Spinbox(top, from_=1, to=20, textvariable=self.pages_var, width=6).grid(
            row=1, column=2, sticky="ew", padx=(0, 8)
        )

        ttk.Label(top, text="正文评论").grid(row=0, column=3, sticky="w")
        comment_box = ttk.Combobox(
            top,
            textvariable=self.comment_var,
            state="readonly",
            values=["none", "some", "more"],
        )
        comment_box.grid(row=1, column=3, sticky="ew", padx=(0, 8))

        ttk.Checkbutton(top, text="生成后自动编译 PDF", variable=self.compile_pdf_var).grid(
            row=1, column=4, sticky="w", padx=(8, 8)
        )

        ttk.Button(top, text="开始生成", command=self.start_generation).grid(
            row=1, column=5, sticky="ew"
        )

        audio_frame = ttk.LabelFrame(main, text="音频输入（可选）", padding=10)
        audio_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        audio_frame.columnconfigure(1, weight=1)
        ttk.Button(audio_frame, text="选择音频文件", command=self.pick_audio).grid(
            row=0, column=0, sticky="w", padx=(0, 8)
        )
        ttk.Entry(audio_frame, textvariable=self.audio_var).grid(row=0, column=1, sticky="ew")
        ttk.Button(audio_frame, text="仅转写音频", command=self.start_transcription_only).grid(
            row=0, column=2, sticky="e", padx=(8, 0)
        )

        transcript_frame = ttk.LabelFrame(main, text="原始内容 / 转写文本", padding=10)
        transcript_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 6), pady=(0, 10))
        transcript_frame.rowconfigure(0, weight=1)
        transcript_frame.columnconfigure(0, weight=1)
        self.transcript_text = scrolledtext.ScrolledText(transcript_frame, wrap=tk.WORD, font=("Consolas", 10))
        self.transcript_text.grid(row=0, column=0, sticky="nsew")

        extra_frame = ttk.LabelFrame(main, text="额外要求", padding=10)
        extra_frame.grid(row=2, column=1, sticky="nsew", padx=(6, 0), pady=(0, 10))
        extra_frame.rowconfigure(0, weight=1)
        extra_frame.columnconfigure(0, weight=1)
        self.extra_text = scrolledtext.ScrolledText(extra_frame, wrap=tk.WORD, font=("Consolas", 10))
        self.extra_text.insert(
            "1.0",
            "可在这里补充要求，例如：繁体、多一些 Codex comment、不少于七页、标题更有概括性等。",
        )
        self.extra_text.grid(row=0, column=0, sticky="nsew")

        output_frame = ttk.LabelFrame(main, text="生成结果（LaTeX）", padding=10)
        output_frame.grid(row=4, column=0, sticky="nsew", padx=(0, 6))
        output_frame.rowconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, font=("Consolas", 10))
        self.output_text.grid(row=0, column=0, sticky="nsew")

        log_frame = ttk.LabelFrame(main, text="运行日志", padding=10)
        log_frame.grid(row=4, column=1, sticky="nsew", padx=(6, 0))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=12, font=("Consolas", 10))
        self.log_text.grid(row=0, column=0, sticky="nsew")

        actions = ttk.Frame(main)
        actions.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)
        actions.columnconfigure(2, weight=1)
        ttk.Button(actions, text="保存当前 LaTeX 为 .tex", command=self.save_current_tex).grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        ttk.Button(actions, text="打开输出目录", command=self.open_output_dir).grid(
            row=0, column=1, sticky="ew", padx=8
        )
        ttk.Button(actions, text="清空日志", command=lambda: self.log_text.delete("1.0", tk.END)).grid(
            row=0, column=2, sticky="ew", padx=(8, 0)
        )

    def log(self, message: str) -> None:
        self.log_queue.put(message)

    def _poll_logs(self) -> None:
        while True:
            try:
                message = self.log_queue.get_nowait()
            except queue.Empty:
                break
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
        self.root.after(150, self._poll_logs)

    def pick_audio(self) -> None:
        file_path = filedialog.askopenfilename(
            title="选择音频文件",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.webm"),
                ("All Files", "*.*"),
            ],
        )
        if file_path:
            self.audio_var.set(file_path)

    def start_transcription_only(self) -> None:
        audio_path = self.audio_var.get().strip()
        if not audio_path:
            messagebox.showwarning("缺少音频", "请先选择一个音频文件。")
            return
        self._run_in_thread(self._transcribe_only_worker)

    def start_generation(self) -> None:
        transcript = self.transcript_text.get("1.0", tk.END).strip()
        audio_path = self.audio_var.get().strip()
        if not transcript and not audio_path:
            messagebox.showwarning("缺少内容", "请粘贴原始文本，或选择一个音频文件。")
            return
        self._run_in_thread(self._generate_worker)

    def _run_in_thread(self, target) -> None:
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("任务进行中", "当前已经有任务在运行，请稍等。")
            return
        self.worker = threading.Thread(target=target, daemon=True)
        self.worker.start()

    def _build_request(self, transcript: str) -> DiaryRequest:
        display_date, weekday_text = format_date_with_weekday(self.date_var.get())
        return DiaryRequest(
            display_date=display_date,
            weekday_text=weekday_text,
            script=self.script_var.get().strip(),
            min_pages=int(self.pages_var.get()),
            comment_mode=self.comment_var.get().strip(),
            extra_requirements=self.extra_text.get("1.0", tk.END).strip(),
            transcript=sanitize_source_text(transcript),
        )

    def _transcribe_if_needed(self) -> str:
        transcript = self.transcript_text.get("1.0", tk.END).strip()
        audio_path_str = self.audio_var.get().strip()
        if transcript:
            return sanitize_source_text(transcript)
        if not audio_path_str:
            return ""
        audio_path = Path(audio_path_str)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        self.log(f"正在转写音频：{audio_path}")
        transcript = self.generator.transcribe_audio(audio_path)
        transcript = sanitize_source_text(transcript)
        self.log(f"转写后端：{self.generator.last_transcription_backend}")
        self.root.after(0, self._replace_transcript_text, transcript)
        out_path = OUTPUT_DIR / f"transcript_{make_filename_slug(self.date_var.get())}.txt"
        out_path.write_text(transcript, encoding="utf-8")
        self.log(f"转写完成，已保存：{out_path}")
        return transcript

    def _replace_transcript_text(self, text: str) -> None:
        self.transcript_text.delete("1.0", tk.END)
        self.transcript_text.insert("1.0", text)

    def _set_output_text(self, text: str) -> None:
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", text)

    def _transcribe_only_worker(self) -> None:
        try:
            transcript = self._transcribe_if_needed()
            if not transcript:
                raise RuntimeError("没有拿到转写结果。")
            self.log("音频转写完成。")
        except Exception as exc:
            self.log(f"[错误] {exc}")
            self.root.after(0, lambda: messagebox.showerror("转写失败", str(exc)))

    def _generate_worker(self) -> None:
        try:
            transcript = self._transcribe_if_needed()
            if not transcript:
                raise RuntimeError("没有可用于生成的原始内容。")

            request = self._build_request(transcript)
            latex = self.generator.generate_latex(request, self.log)
            self.root.after(0, self._set_output_text, latex)

            base_name = f"{request.display_date}_{make_filename_slug(request.display_date)}"
            tex_path = OUTPUT_DIR / f"{base_name}.tex"
            tex_path.write_text(latex, encoding="utf-8")
            self.log(f"LaTeX 已保存：{tex_path}")

            if self.compile_pdf_var.get():
                pdf_path = self.generator.compile_pdf(tex_path, self.log)
                self.log(f"PDF 已生成：{pdf_path}")

            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "完成",
                    f"日记已生成。\n\nLaTeX: {tex_path}"
                    + (
                        f"\nPDF: {tex_path.with_suffix('.pdf')}"
                        if self.compile_pdf_var.get()
                        else ""
                    ),
                ),
            )
        except Exception as exc:
            self.log(f"[错误] {exc}")
            self.root.after(0, lambda: messagebox.showerror("生成失败", str(exc)))

    def save_current_tex(self) -> None:
        text = self.output_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo("没有内容", "当前还没有生成任何 LaTeX 内容。")
            return
        file_path = filedialog.asksaveasfilename(
            title="保存 LaTeX 文件",
            defaultextension=".tex",
            filetypes=[("TeX files", "*.tex"), ("All Files", "*.*")],
            initialdir=str(OUTPUT_DIR),
            initialfile=f"{make_filename_slug(self.date_var.get())}.tex",
        )
        if not file_path:
            return
        Path(file_path).write_text(text, encoding="utf-8")
        self.log(f"已手动保存：{file_path}")

    def open_output_dir(self) -> None:
        os.startfile(str(OUTPUT_DIR))


def main() -> None:
    root = tk.Tk()
    style = ttk.Style()
    if "vista" in style.theme_names():
        style.theme_use("vista")
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
