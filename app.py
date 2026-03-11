import json
import os
import re
import threading
import tkinter as tk
import urllib.error
import urllib.request
from tkinter import messagebox, ttk

from config import ConfigManager
from dialogs import SettingsDialog, ToneExamplesDialog
from greeklish_editor import GreeklishProfileEditor


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

TONE_MAPPING = {
    "Επαγγελματικός αλλά φιλικός": "professional but friendly",
    "Επίσημος": "formal",
    "Χαλαρός": "casual",
    "Ακαδημαϊκός": "academic",
    "Πειστικός": "persuasive",
    "Μόνο διόρθωση γραμματικής": "correct grammar only, no tone changes",
}


def _preserve_case(source: str, target: str) -> str:
    if source.isupper():
        return target.upper()
    if source[:1].isupper():
        return target[:1].upper() + target[1:]
    return target


def greeklish_to_greek(text: str) -> str:
    # Backtick escape: `word` passes through as-is (backticks are stripped)
    # e.g. "pws paei to `deployment` sto `cloud`" → "πώς πάει το deployment στο cloud"
    PLACEHOLDER_PREFIX = "\x00PASSTHROUGH"
    passthroughs: list[str] = []

    def _stash(m: re.Match) -> str:
        passthroughs.append(m.group(1))
        return f"{PLACEHOLDER_PREFIX}{len(passthroughs) - 1}\x00"

    escaped = re.sub(r"`([^`]*)`", _stash, text)

    out = []
    i = 0
    while i < len(escaped):
        # Restore placeholder
        if escaped[i] == "\x00" and escaped[i:].startswith(PLACEHOLDER_PREFIX):
            end = escaped.index("\x00", i + 1)
            idx = int(escaped[i + len(PLACEHOLDER_PREFIX):end])
            out.append(passthroughs[idx])
            i = end + 1
            continue
        matched = False
        for size in (2,):
            chunk = escaped[i : i + size]
            lower = chunk.lower()
            if lower in GREEKLISH_MULTI:
                out.append(_preserve_case(chunk, GREEKLISH_MULTI[lower]))
                i += size
                matched = True
                break
        if matched:
            continue
        ch = escaped[i]
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




class LLMAssistant:
    def __init__(self):
        self.OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:1234/v1")
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "llm_model")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "random-api-key")

    def _invoke(self, system_prompt: str, user_text: str) -> str:
        payload = json.dumps({
            "model": self.OPENAI_MODEL,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
        }).encode()
        req = urllib.request.Request(
            f"{self.OPENAI_BASE_URL.rstrip('/')}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.OPENAI_API_KEY}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Cannot reach LLM endpoint ({self.OPENAI_BASE_URL}).\n"
                "Make sure LM Studio is running and a model is loaded, or set "
                "OPENAI_BASE_URL / OPENAI_API_KEY / OPENAI_MODEL."
            ) from exc
        return data["choices"][0]["message"]["content"].strip()

    def improve_greek(self, text: str, tone: str) -> str:
        return self._invoke(
            f"You are a professional Greek text editor. "
            f"Fix grammar, syntax, and clarity while strictly preserving the original meaning. "
            f"Apply a '{tone}' tone throughout. "
            f"Return ONLY the corrected Greek text — no explanations, no markdown, no introductory phrases.",
            text,
        )

    def improve_tone_grammar_orthography(self, text: str, tone: str) -> str:
        return self._invoke(
            f"You are a professional Greek text editor and orthography specialist. "
            f"1. Fix grammar, syntax, and clarity while strictly preserving the original meaning. "
            f"2. Apply a '{tone}' tone throughout. "
            f"3. Add correct accent marks (tonifies) to every word that requires one, following the modern monotonic system. "
            f"Return ONLY the improved Greek text — no explanations, no markdown, no introductory phrases.",
            text,
        )

    def tonify(self, text: str) -> str:
        return self._invoke(
            "You are a Greek orthography specialist. "
            "Add the correct accent marks to every word that requires one, "
            "following the modern monotonic system. "
            "Do NOT change any word, word order, or punctuation — only add or correct accents. "
            "Return ONLY the accented text — no explanations, no markdown.",
            text,
        )

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        return self._invoke(
            f"You are a professional translator. "
            f"Translate the following text from {source_lang} to {target_lang}. "
            f"Preserve the style, tone, and structure of the original as closely as possible. "
            f"Return ONLY the translation — no explanations, no markdown, no introductory phrases.",
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
        self.root.title("Ελληνικός Βοηθός Γραφής")
        
        # Load configuration
        self.config = ConfigManager()
        
        # Apply saved window size
        width = self.config.get("window_width", 1380)
        height = self.config.get("window_height", 690)
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(1380, 690)
        
        # Initialize LLM with config values
        self.llm = LLMAssistant()
        self.llm.OPENAI_BASE_URL = self.config.get("llm_endpoint", "http://localhost:1234/v1")
        self.llm.OPENAI_MODEL = self.config.get("llm_model", "llm_model")
        self.llm.OPENAI_API_KEY = self.config.get("llm_api_key", "random-api-key")
        
        # Initialize variables from config
        self.theme_name = self.config.get("theme", "dark")
        self.auto_convert_var = tk.BooleanVar(value=self.config.get("auto_convert", True))
        self.auto_tonify_var = tk.BooleanVar(value=self.config.get("auto_tonify", False))
        self._tonify_timer = None
        self.font_size = self.config.get("font_size", 11)
        self._llm_running = False

        self.tone_var = tk.StringVar(value=self.config.get("default_tone", "Μόνο διόρθωση γραμματικής"))
        self.target_lang_var = tk.StringVar(value=self.config.get("last_language", "English"))
        
        # Load custom greeklish profile
        self.greeklish_profile = self.config.load_greeklish_profile(
            self.config.get("active_greeklish_profile", "default")
        )
        if self.greeklish_profile:
            global GREEKLISH_MULTI, GREEKLISH_SINGLE
            GREEKLISH_MULTI = self.greeklish_profile.get("multi", GREEKLISH_MULTI)
            GREEKLISH_SINGLE = self.greeklish_profile.get("single", GREEKLISH_SINGLE)
        
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self._build_ui()
        self._apply_theme()
        
        # Keyboard shortcuts
        self.root.bind("<Control-l>", lambda _e: self._clear_input())
        self.root.bind("<Control-d>", lambda _e: self.toggle_theme())
        self.root.bind("<Control-Return>", lambda _e: self.convert_text())
        self.root.bind("<Control-Shift-c>", lambda _e: self._copy_output())
        self.root.bind("<Control-Shift-C>", lambda _e: self._copy_output())
        self.root.bind("<Control-t>", lambda _e: self.tonify_text())
        self.root.bind("<Control-T>", lambda _e: self.tonify_text())
        self.root.bind("<Control-i>", lambda _e: self.improve_with_llm())
        self.root.bind("<Control-I>", lambda _e: self.improve_with_llm())
        self.root.bind("<Configure>", self._on_window_resize)
        
        # Save window size on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Test LLM connection on startup
        self.root.after(500, self._check_connection)

    def _build_ui(self):
        self.container = ttk.Frame(self.root, padding=14)
        self.container.pack(fill=tk.BOTH, expand=True)

        # ── Top bar ─────────────────────────────────────────────────────────
        top = ttk.Frame(self.container)
        top.pack(fill=tk.X, side=tk.TOP)

        title = ttk.Label(top, text="Ελληνικός Βοηθός Γραφής", font=("Segoe UI", 14, "bold"))
        title.pack(side=tk.LEFT)

        ttk.Checkbutton(top, text="Αυτόματη μετατροπή", variable=self.auto_convert_var, style="Card.TCheckbutton").pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(top, text="Αυτόματη τονικότητα (5δ)", variable=self.auto_tonify_var, style="Card.TCheckbutton").pack(side=tk.LEFT, padx=(0, 10))

        # Font size
        font_frame = ttk.Frame(top)
        font_frame.pack(side=tk.LEFT, padx=6)
        ttk.Label(font_frame, text="Γραμματοσειρά:").pack(side=tk.LEFT)
        ttk.Button(font_frame, text="−", width=2, command=self._font_decrease).pack(side=tk.LEFT)
        self.font_size_label = ttk.Label(font_frame, text=str(self.font_size), width=3, anchor="center")
        self.font_size_label.pack(side=tk.LEFT)
        ttk.Button(font_frame, text="+", width=2, command=self._font_increase).pack(side=tk.LEFT)

        ttk.Button(top, text="Εναλλαγή θέματος (Ctrl+D)", command=self.toggle_theme).pack(side=tk.RIGHT, padx=(0, 8))
        ttk.Button(top, text="Ρυθμίσεις", command=self._open_settings).pack(side=tk.RIGHT, padx=(0, 8))
        ttk.Button(top, text="Παραδείγματα τόνων", command=self._open_tone_examples).pack(side=tk.RIGHT, padx=(0, 8))
        ttk.Button(top, text="Προφίλ Greeklish", command=self._open_greeklish_editor).pack(side=tk.RIGHT, padx=(0, 8))

        # ── Middle frame (expands to fill space) ──────────────────────────────
        middle = ttk.Frame(self.container)
        middle.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        # ── Panes ────────────────────────────────────────────────────────────
        panes = ttk.Panedwindow(middle, orient=tk.HORIZONTAL)
        panes.pack(fill=tk.BOTH, expand=True, pady=(12, 8))

        left = ttk.Frame(panes, padding=8)
        right = ttk.Frame(panes, padding=8)
        panes.add(left, weight=1)
        panes.add(right, weight=1)

        # Input side
        input_header = ttk.Frame(left)
        input_header.pack(fill=tk.X)
        ttk.Label(input_header, text="Είσοδος Greeklish").pack(side=tk.LEFT)
        ttk.Button(input_header, text="Κατάργηση (Ctrl+L)", command=self._clear_input).pack(side=tk.RIGHT)

        self.input_text = tk.Text(left, wrap=tk.WORD, undo=True)
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
        self.input_text.bind("<Button-3>", lambda e: self._show_context_menu(e, self.input_text))

        # Output side
        output_header = ttk.Frame(right)
        output_header.pack(fill=tk.X)
        ttk.Label(output_header, text="Ελληνική έξοδος").pack(side=tk.LEFT)
        ttk.Button(output_header, text="Αντιγραφή (Ctrl+Shift+C)", command=self._copy_output).pack(side=tk.RIGHT)

        self.output_text = tk.Text(right, wrap=tk.WORD, undo=True)
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
        self.output_text.bind("<Button-3>", lambda e: self._show_context_menu(e, self.output_text))

        # ── Footer (status + shortcuts) ────────────────────────────────────────
        footer = ttk.Frame(self.container)
        footer.pack(fill=tk.X, pady=(6, 0), side=tk.BOTTOM)
        
        self.status_label = ttk.Label(footer, text="Έτοιμο", font=("Segoe UI", 9))
        self.status_label.pack(side=tk.LEFT)
        
        self.word_count_label = ttk.Label(footer, text="", font=("Segoe UI", 9))
        self.word_count_label.pack(side=tk.LEFT, padx=(12, 0))
        
        self.connection_status_label = ttk.Label(footer, text="[Checking...]", font=("Segoe UI", 9))
        self.connection_status_label.pack(side=tk.LEFT, padx=(12, 0))
        
        shortcuts_label = ttk.Label(
            footer,
            text="`word`: passthrough  |  Ctrl+I: βελτίωση  |  Ctrl+T: τόνοι  |  Ctrl+L: κατάργηση  |  Ctrl+Shift+C: αντιγραφή  |  Ctrl+D: θέμα",
            font=("Segoe UI", 9),
        )
        shortcuts_label.pack(side=tk.RIGHT, padx=(8, 0))

        # ── Action bar ───────────────────────────────────────────────────────
        actions = ttk.Frame(self.container)
        actions.pack(fill=tk.X, pady=(6, 0), side=tk.BOTTOM)
        ttk.Button(actions, text="Μετατροπή (Ctrl+↵)", command=self.convert_text).pack(side=tk.LEFT)

        tone_frame = ttk.Frame(actions)
        tone_frame.pack(side=tk.LEFT, padx=8)
        ttk.Label(tone_frame, text="Τόνος:").pack(side=tk.LEFT)
        tone_combo = ttk.Combobox(
            tone_frame,
            textvariable=self.tone_var,
            values=[
                "Μόνο διόρθωση γραμματικής",
                "Επαγγελματικός αλλά φιλικός",
                "Επίσημος",
                "Χαλαρός",
                "Ακαδημαϊκός",
                "Πειστικός",
            ],
            state="readonly",
            width=32,
            style="Card.TCombobox",
        )
        tone_combo.pack(side=tk.LEFT, padx=(4, 0))

        self.llm_btn = ttk.Button(actions, text="LLM: Βελτίωση τόνου (Ctrl+I)", command=self.improve_with_llm)
        self.llm_btn.pack(side=tk.LEFT, padx=8)
        self.tone_grammar_btn = ttk.Button(actions, text="Τόνος + Γραμματική", command=self.improve_tone_grammar)
        self.tone_grammar_btn.pack(side=tk.LEFT, padx=4)
        self.tonify_btn = ttk.Button(actions, text="Προσθήκη τόνων (Ctrl+T)", command=self.tonify_text)
        self.tonify_btn.pack(side=tk.LEFT, padx=4)

        lang_frame = ttk.Frame(actions)
        lang_frame.pack(side=tk.LEFT, padx=8)
        ttk.Label(lang_frame, text="Μετάφραση:").pack(side=tk.LEFT)
        lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.target_lang_var,
            values=[
                "English",
                "French",
                "German",
                "Spanish",
                "Italian",
                "Portuguese",
                "Dutch",
                "Swedish",
                "Japanese",
                "Chinese",
                "Russian",
            ],
            state="readonly",
            width=13,
            style="Card.TCombobox",
        )
        lang_combo.pack(side=tk.LEFT, padx=(4, 0))
        self.translate_btn = ttk.Button(actions, text="Μετάφραση", command=self.translate_text)
        self.translate_btn.pack(side=tk.LEFT, padx=4)

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

    def _on_window_resize(self, event):
        pass

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
            self._set_status("Αντιγράφηκε στο πρόχειρο.")

    def _clear_input(self):
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self._update_word_count("")
        self._set_status("Καταργήθηκε.")

    # ── Status bar ───────────────────────────────────────────────────────────
    def _set_status(self, message: str, after_ms: int = 3000):
        self.status_label.configure(text=message)
        if after_ms:
            self.root.after(after_ms, lambda: self.status_label.configure(text="Έτοιμο"))

    def _update_word_count(self, text: str):
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        self.word_count_label.configure(text=f"{words} λέξεις  {chars} χαρακτήρες")

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
        for btn in (self.llm_btn, self.tone_grammar_btn, self.tonify_btn, self.translate_btn):
            btn.configure(state=state)

    def _llm_action(self, action):
        if self._llm_running:
            return
        self._llm_running = True
        self._set_llm_buttons_state("disabled")
        self._set_status("⏳ Το LLM εργάζεται...", after_ms=0)

        def _run():
            try:
                result = action()
                self.root.after(0, lambda: self._llm_done(result))
            except Exception as exc:  # noqa: BLE001
                self.root.after(0, lambda e=exc: self._llm_error(e))

        threading.Thread(target=_run, daemon=True).start()

    def _llm_done(self, result: str):
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", result)
        self._llm_running = False
        self._set_llm_buttons_state("normal")
        self._set_status("Ολοκλήρωθη.")

    def _llm_error(self, exc: Exception):
        self._llm_running = False
        self._set_llm_buttons_state("normal")
        self._set_status("Σφάλμα LLM — δείτε το παράθυρο.")
        messagebox.showerror(
            "LLM μη διαθέσιμο",
            f"{exc}\n\nΒεβαιωθείτε ότι το OpenAI endpoint είναι σωστό.\n"
            f"Endpoint: {self.llm.OPENAI_BASE_URL}\n\n"
            "Αντικαταστήστε με μεταβλητές περιβάλλοντος: OPENAI_BASE_URL, OPENAI_API_KEY, OPENAI_MODEL.",
        )

    def tonify_text(self):
        text = self.output_text.get("1.0", tk.END).rstrip("\n") or self.input_text.get("1.0", tk.END).rstrip("\n")
        if not text.strip():
            return
        self._llm_action(lambda: self.llm.tonify(text=text))

    def improve_with_llm(self):
        text = self.output_text.get("1.0", tk.END).rstrip("\n") or self.input_text.get("1.0", tk.END).rstrip("\n")
        greek_tone = self.tone_var.get()
        tone = TONE_MAPPING.get(greek_tone, "professional but friendly")
        self._llm_action(lambda: self.llm.improve_greek(text=text, tone=tone))

    def improve_tone_grammar(self):
        """Improve text with tone, grammar, and orthography."""
        text = self.output_text.get("1.0", tk.END).rstrip("\n") or self.input_text.get("1.0", tk.END).rstrip("\n")
        greek_tone = self.tone_var.get()
        tone = TONE_MAPPING.get(greek_tone, "professional but friendly")
        self._llm_action(lambda: self.llm.improve_tone_grammar_orthography(text=text, tone=tone))

    def translate_text(self):
        text = self.output_text.get("1.0", tk.END).rstrip("\n") or self.input_text.get("1.0", tk.END).rstrip("\n")
        target_lang = self.target_lang_var.get()
        self._llm_action(lambda: self.llm.translate(text=text, source_lang="Greek", target_lang=target_lang))

    def _open_settings(self):
        """Open the Settings dialog."""
        SettingsDialog(self.root, self.config, self.llm, self)

    def _open_tone_examples(self):
        """Open the Tone Examples dialog."""
        ToneExamplesDialog(self.root, self.llm)

    def _open_greeklish_editor(self):
        """Open the Greeklish Profile Editor dialog."""
        GreeklishProfileEditor(self.root, self.config, self)

    def _check_connection(self):
        """Check if LLM is available and update connection status indicator."""
        def check():
            try:
                self.llm._invoke("You are a helpful assistant.", "Hi")
                status = "[Online]"
                self.root.after(0, lambda: self.connection_status_label.configure(text=status, foreground="#4CAF50"))
            except Exception:
                status = "[Offline]"
                self.root.after(0, lambda: self.connection_status_label.configure(text=status, foreground="#F44336"))
        
        thread = threading.Thread(target=check, daemon=True)
        thread.start()

    def _on_closing(self):
        """Save window geometry and close the app."""
        self.config.set("window_width", self.root.winfo_width())
        self.config.set("window_height", self.root.winfo_height())
        self.config.save()
        self.root.destroy()

    def _show_context_menu(self, event, text_widget):
        """Show right-click context menu."""
        menu = tk.Menu(self.root, tearoff=False)
        menu.add_command(label="Αντιγραφή", command=lambda: self._copy_text(text_widget))
        menu.add_command(label="Επικόλληση", command=lambda: self._paste_text(text_widget))
        menu.add_separator()
        menu.add_command(label="Διαγραφή", command=lambda: self._clear_text(text_widget))
        menu.post(event.x_root, event.y_root)

    def _copy_text(self, text_widget):
        """Copy selected text or all text."""
        try:
            text = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            text = text_widget.get("1.0", tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def _paste_text(self, text_widget):
        """Paste text from clipboard."""
        try:
            text = self.root.clipboard_get()
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", text)
        except tk.TclError:
            pass

    def _clear_text(self, text_widget):
        """Clear all text from widget."""
        text_widget.delete("1.0", tk.END)


def main():
    root = tk.Tk()
    app = WritingAssistantApp(root)
    app.input_text.focus_set()
    root.mainloop()


if __name__ == "__main__":
    main()
