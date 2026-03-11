import json
import os
import re
import threading
import tkinter as tk
import urllib.error
import urllib.request
from tkinter import messagebox, ttk


GREEKLISH_MULTI = {
    "ps": "ψ",
    "ou": "ου",
    "ai": "αι",
    "ei": "ει",
    "oi": "οι",
    "au": "αυ",
    "eu": "ευ",
    "mp": "μπ",
    "nt": "ντ",
    "gk": "γκ",
    "gg": "γγ",
}

GREEKLISH_SINGLE = {
    "a": "α",
    "b": "β",
    "v": "β",
    "g": "γ",
    "d": "δ",
    "e": "ε",
    "z": "ζ",
    "h": "η",
    "8": "θ",
    "i": "ι",
    "k": "κ",
    "l": "λ",
    "m": "μ",
    "n": "ν",
    "3": "ξ",
    "o": "ο",
    "p": "π",
    "r": "ρ",
    "s": "σ",
    "t": "τ",
    "u": "υ",
    "y": "υ",
    "f": "φ",
    "x": "χ",
    "w": "ω",
    "?": ";"
}


def _preserve_case(source: str, target: str) -> str:
    if source.isupper():
        return target.upper()
    if source[:1].isupper():
        return target[:1].upper() + target[1:]
    return target


def greeklish_to_greek(text: str) -> str:
    out = []
    i = 0
    while i < len(text):
        matched = False
        for size in (2,):
            chunk = text[i : i + size]
            lower = chunk.lower()
            if lower in GREEKLISH_MULTI:
                out.append(_preserve_case(chunk, GREEKLISH_MULTI[lower]))
                i += size
                matched = True
                break
        if matched:
            continue
        ch = text[i]
        lower = ch.lower()
        if lower in GREEKLISH_SINGLE:
            out.append(_preserve_case(ch, GREEKLISH_SINGLE[lower]))
        else:
            out.append(ch)
        i += 1
    return second_pass_corrections("".join(out))


def second_pass_corrections(text: str) -> str:
    corrected = text
    corrected = re.sub(r"\bσ\b", "ς", corrected)
    corrected = re.sub(r"σ([,.!?;:)\]»\s]|$)", r"ς\1", corrected)
    corrected = re.sub(r"\bντε\b", "ντε", corrected)
    corrected = corrected.replace(";;", ";")
    return corrected


# LM Studio / OpenAI-compatible endpoint — override with env vars if needed
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:1234/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "google/gemma-3n-e4b")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "lm-studio")  # LM Studio ignores the key


class LLMAssistant:
    def _invoke(self, system_prompt: str, user_text: str) -> str:
        payload = json.dumps({
            "model": OPENAI_MODEL,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
        }).encode()
        req = urllib.request.Request(
            f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_API_KEY}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Cannot reach LLM endpoint ({OPENAI_BASE_URL}).\n"
                "Make sure LM Studio is running and a model is loaded, or set "
                "OPENAI_BASE_URL / OPENAI_API_KEY / OPENAI_MODEL."
            ) from exc
        return data["choices"][0]["message"]["content"].strip()

    def improve_greek(self, text: str, tone: str) -> str:
        return self._invoke(
            f"Improve grammar and clarity in Greek. Keep meaning and output only Greek text with {tone} tone.",
            text,
        )

    def tonify(self, text: str) -> str:
        return self._invoke(
            "You are a Greek orthography assistant. Add the correct accent mark (τόνος) to every Greek word that needs one. "
            "Return ONLY the corrected Greek text — no explanations, no extra lines, no markdown.",
            text,
        )

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        return self._invoke(
            f"Translate from {source_lang} to {target_lang}. Return only translated text.",
            text,
        )


THEMES = {
    "dark": {
        "bg": "#121212",
        "card": "#1E1E1E",
        "fg": "#EDEDED",
        "muted": "#9AA0A6",
        "accent": "#90CAF9",
    },
    "light": {
        "bg": "#F4F6F8",
        "card": "#FFFFFF",
        "fg": "#1F1F1F",
        "muted": "#555555",
        "accent": "#1976D2",
    },
}


class WritingAssistantApp:
    _FONT_SIZES = [10, 12, 14, 16, 18, 20]

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Writing Assistant")
        self.root.geometry("1000x700")
        self.theme_name = "dark"
        self.llm = LLMAssistant()
        self.auto_convert_var = tk.BooleanVar(value=True)
        self.auto_tonify_var = tk.BooleanVar(value=False)
        self._tonify_timer = None
        self.font_size = 11
        self._llm_running = False

        self.tone_var = tk.StringVar(value="professional but friendly")
        self.style = ttk.Style()
        self.style.theme_use("clam")  # allows full bg/fg overrides on Windows
        self._build_ui()
        self._apply_theme()
        self.root.bind("<Control-l>", lambda _e: self._clear_input())
        self.root.bind("<Control-d>", lambda _e: self.toggle_theme())
        self.root.bind("<Control-Return>", lambda _e: self.convert_text())
        self.root.bind("<Control-Shift-c>", lambda _e: self._copy_output())
        self.root.bind("<Control-Shift-C>", lambda _e: self._copy_output())
        self.root.bind("<Control-t>", lambda _e: self.tonify_text())
        self.root.bind("<Control-T>", lambda _e: self.tonify_text())

    def _build_ui(self):
        self.container = ttk.Frame(self.root, padding=14)
        self.container.pack(fill=tk.BOTH, expand=True)

        # ── Top bar ─────────────────────────────────────────────────────────
        top = ttk.Frame(self.container)
        top.pack(fill=tk.X)

        title = ttk.Label(top, text="Greek Writing Assistant", font=("Segoe UI", 14, "bold"))
        title.pack(side=tk.LEFT)

        ttk.Checkbutton(top, text="Auto convert", variable=self.auto_convert_var, style="Card.TCheckbutton").pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(top, text="Auto-tonify (5s)", variable=self.auto_tonify_var, style="Card.TCheckbutton").pack(side=tk.LEFT, padx=(0, 10))

        # Font size
        font_frame = ttk.Frame(top)
        font_frame.pack(side=tk.LEFT, padx=6)
        ttk.Label(font_frame, text="Font:").pack(side=tk.LEFT)
        ttk.Button(font_frame, text="−", width=2, command=self._font_decrease).pack(side=tk.LEFT)
        self.font_size_label = ttk.Label(font_frame, text=str(self.font_size), width=3, anchor="center")
        self.font_size_label.pack(side=tk.LEFT)
        ttk.Button(font_frame, text="+", width=2, command=self._font_increase).pack(side=tk.LEFT)

        ttk.Button(top, text="Toggle Theme (Ctrl+D)", command=self.toggle_theme).pack(side=tk.RIGHT)

        # ── Panes ────────────────────────────────────────────────────────────
        panes = ttk.Panedwindow(self.container, orient=tk.HORIZONTAL)
        panes.pack(fill=tk.BOTH, expand=True, pady=(12, 8))

        left = ttk.Frame(panes, padding=8)
        right = ttk.Frame(panes, padding=8)
        panes.add(left, weight=1)
        panes.add(right, weight=1)

        # Input side
        input_header = ttk.Frame(left)
        input_header.pack(fill=tk.X)
        ttk.Label(input_header, text="Greeklish Input").pack(side=tk.LEFT)
        ttk.Button(input_header, text="Clear (Ctrl+L)", command=self._clear_input).pack(side=tk.RIGHT)

        self.input_text = tk.Text(left, wrap=tk.WORD, height=24, undo=True)
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        # Output side
        output_header = ttk.Frame(right)
        output_header.pack(fill=tk.X)
        ttk.Label(output_header, text="Greek Output").pack(side=tk.LEFT)
        ttk.Button(output_header, text="Copy (Ctrl+Shift+C)", command=self._copy_output).pack(side=tk.RIGHT)

        self.output_text = tk.Text(right, wrap=tk.WORD, height=24, undo=True)
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        # ── Action bar ───────────────────────────────────────────────────────
        actions = ttk.Frame(self.container)
        actions.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(actions, text="Convert (Ctrl+↵)", command=self.convert_text).pack(side=tk.LEFT)

        tone_frame = ttk.Frame(actions)
        tone_frame.pack(side=tk.LEFT, padx=8)
        ttk.Label(tone_frame, text="Tone:").pack(side=tk.LEFT)
        tone_combo = ttk.Combobox(
            tone_frame,
            textvariable=self.tone_var,
            values=[
                "professional but friendly",
                "formal",
                "casual",
                "academic",
                "persuasive",
            ],
            state="readonly",
            width=22,
            style="Card.TCombobox",
        )
        tone_combo.pack(side=tk.LEFT, padx=(4, 0))

        self.llm_btn = ttk.Button(actions, text="LLM: Improve Tone", command=self.improve_with_llm)
        self.llm_btn.pack(side=tk.LEFT, padx=8)
        self.tonify_btn = ttk.Button(actions, text="Add Tones (Ctrl+T)", command=self.tonify_text)
        self.tonify_btn.pack(side=tk.LEFT, padx=4)
        self.translate_en_el_btn = ttk.Button(actions, text="Translate EN → EL", command=self.translate_en_el)
        self.translate_en_el_btn.pack(side=tk.LEFT, padx=4)
        self.translate_el_en_btn = ttk.Button(actions, text="Translate EL → EN", command=self.translate_el_en)
        self.translate_el_en_btn.pack(side=tk.LEFT, padx=4)

        ttk.Label(
            actions,
            text="Ctrl+T: tones  |  Ctrl+L: clear  |  Ctrl+Shift+C: copy  |  Ctrl+D: theme",
            font=("Segoe UI", 9),
        ).pack(side=tk.RIGHT)

        # ── Status bar ───────────────────────────────────────────────────────
        status_bar = ttk.Frame(self.container)
        status_bar.pack(fill=tk.X, pady=(6, 0))
        self.status_label = ttk.Label(status_bar, text="Ready", font=("Segoe UI", 9))
        self.status_label.pack(side=tk.LEFT)
        self.word_count_label = ttk.Label(status_bar, text="", font=("Segoe UI", 9))
        self.word_count_label.pack(side=tk.RIGHT)

        self.input_text.bind("<KeyRelease>", self._on_input_change)
        self._update_text_font()

    def _apply_theme(self):
        theme = THEMES[self.theme_name]
        self.root.configure(bg=theme["bg"])
        self.style.configure("TFrame", background=theme["bg"])
        self.style.configure("TLabel", background=theme["bg"], foreground=theme["fg"])
        self.style.configure(
            "TButton",
            background=theme["card"],
            foreground=theme["fg"],
            bordercolor=theme["muted"],
            darkcolor=theme["card"],
            lightcolor=theme["card"],
            relief="flat",
            padding=(8, 4),
        )
        self.style.map(
            "TButton",
            background=[("active", theme["accent"]), ("disabled", theme["bg"])],
            foreground=[("active", theme["bg"]), ("disabled", theme["muted"])],
        )
        self.style.configure("TCheckbutton", background=theme["bg"], foreground=theme["fg"])
        # Checkbutton that sits on a card/button row — same bg as buttons
        self.style.configure(
            "Card.TCheckbutton",
            background=theme["card"],
            foreground=theme["fg"],
            indicatorbackground=theme["bg"],
            indicatorforeground=theme["accent"],
        )
        self.style.map(
            "Card.TCheckbutton",
            background=[("active", theme["card"])],
            foreground=[("active", theme["fg"])],
        )
        # Combobox styled to match buttons
        self.style.configure(
            "Card.TCombobox",
            fieldbackground=theme["card"],
            background=theme["card"],
            foreground=theme["fg"],
            arrowcolor=theme["fg"],
            bordercolor=theme["muted"],
            selectbackground=theme["accent"],
            selectforeground=theme["bg"],
            padding=(6, 4),
        )
        self.style.map(
            "Card.TCombobox",
            fieldbackground=[("readonly", theme["card"])],
            foreground=[("readonly", theme["fg"])],
            background=[("active", theme["card"]), ("readonly", theme["card"])],
        )
        self.style.configure("TPanedwindow", background=theme["bg"])
        self.input_text.configure(
            bg=theme["card"],
            fg=theme["fg"],
            insertbackground=theme["accent"],
            relief=tk.FLAT,
            padx=10,
            pady=10,
        )
        self.output_text.configure(
            bg=theme["card"],
            fg=theme["fg"],
            insertbackground=theme["accent"],
            relief=tk.FLAT,
            padx=10,
            pady=10,
        )

    def toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self._apply_theme()

    # ── Font helpers ─────────────────────────────────────────────────────────
    def _update_text_font(self):
        font = ("Segoe UI", self.font_size)
        self.input_text.configure(font=font)
        self.output_text.configure(font=font)
        self.font_size_label.configure(text=str(self.font_size))

    def _font_increase(self):
        sizes = self._FONT_SIZES
        if self.font_size < sizes[-1]:
            self.font_size = sizes[sizes.index(self.font_size) + 1] if self.font_size in sizes else self.font_size + 2
        self._update_text_font()

    def _font_decrease(self):
        sizes = self._FONT_SIZES
        if self.font_size > sizes[0]:
            self.font_size = sizes[sizes.index(self.font_size) - 1] if self.font_size in sizes else self.font_size - 2
        self._update_text_font()

    # ── Clipboard / clear ────────────────────────────────────────────────────
    def _copy_output(self):
        text = self.output_text.get("1.0", tk.END).rstrip("\n")
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self._set_status("Output copied to clipboard.")

    def _clear_input(self):
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self._update_word_count("")
        self._set_status("Cleared.")

    # ── Status bar ───────────────────────────────────────────────────────────
    def _set_status(self, message: str, after_ms: int = 3000):
        self.status_label.configure(text=message)
        if after_ms:
            self.root.after(after_ms, lambda: self.status_label.configure(text="Ready"))

    def _update_word_count(self, text: str):
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        self.word_count_label.configure(text=f"{words} words  {chars} chars")

    # ── Input change ─────────────────────────────────────────────────────────
    def _on_input_change(self, _event=None):
        text = self.input_text.get("1.0", tk.END).rstrip("\n")
        self._update_word_count(text)
        if self.auto_convert_var.get():
            self.convert_text()
        # 5-second debounce for auto-tonify
        if self._tonify_timer is not None:
            self.root.after_cancel(self._tonify_timer)
            self._tonify_timer = None
        if self.auto_tonify_var.get():
            self._tonify_timer = self.root.after(5000, self._auto_tonify_fire)

    def _auto_tonify_fire(self):
        self._tonify_timer = None
        if self.auto_tonify_var.get() and not self._llm_running:
            self.tonify_text()

    def convert_text(self):
        source = self.input_text.get("1.0", tk.END).rstrip("\n")
        converted = greeklish_to_greek(source)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", converted)

    # ── LLM helpers (threaded) ───────────────────────────────────────────────
    def _set_llm_buttons_state(self, state: str):
        for btn in (self.llm_btn, self.tonify_btn, self.translate_en_el_btn, self.translate_el_en_btn):
            btn.configure(state=state)

    def _llm_action(self, action):
        if self._llm_running:
            return
        self._llm_running = True
        self._set_llm_buttons_state("disabled")
        self._set_status("⏳ LLM working…", after_ms=0)

        def _run():
            try:
                result = action()
                self.root.after(0, lambda: self._llm_done(result))
            except Exception as exc:  # noqa: BLE001
                self.root.after(0, lambda: self._llm_error(exc))

        threading.Thread(target=_run, daemon=True).start()

    def _llm_done(self, result: str):
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", result)
        self._llm_running = False
        self._set_llm_buttons_state("normal")
        self._set_status("Done.")

    def _llm_error(self, exc: Exception):
        self._llm_running = False
        self._set_llm_buttons_state("normal")
        self._set_status("LLM error — see dialog.")
        messagebox.showerror(
            "LLM unavailable",
            f"{exc}\n\nMake sure LM Studio is running and a model is loaded.\n"
            f"Endpoint: {OPENAI_BASE_URL}\n\n"
            "Override with env vars: OPENAI_BASE_URL, OPENAI_API_KEY, OPENAI_MODEL.",
        )

    def tonify_text(self):
        text = self.output_text.get("1.0", tk.END).rstrip("\n") or self.input_text.get("1.0", tk.END).rstrip("\n")
        if not text.strip():
            return
        self._llm_action(lambda: self.llm.tonify(text=text))

    def improve_with_llm(self):
        text = self.output_text.get("1.0", tk.END).rstrip("\n") or self.input_text.get("1.0", tk.END).rstrip("\n")
        tone = self.tone_var.get()
        self._llm_action(lambda: self.llm.improve_greek(text=text, tone=tone))

    def translate_en_el(self):
        text = self.input_text.get("1.0", tk.END).rstrip("\n")
        self._llm_action(lambda: self.llm.translate(text=text, source_lang="English", target_lang="Greek"))

    def translate_el_en(self):
        text = self.output_text.get("1.0", tk.END).rstrip("\n") or self.input_text.get("1.0", tk.END).rstrip("\n")
        self._llm_action(lambda: self.llm.translate(text=text, source_lang="Greek", target_lang="English"))


def main():
    root = tk.Tk()
    app = WritingAssistantApp(root)
    app.input_text.focus_set()
    root.mainloop()


if __name__ == "__main__":
    main()
