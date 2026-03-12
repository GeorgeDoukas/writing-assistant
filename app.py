import ctypes
import platform
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox, ttk

_SYSTEM = platform.system()

import converter
from config import ConfigManager
from converter import greeklish_to_greek
from dialogs import SettingsDialog, ToneExamplesDialog
from greeklish_editor import GreeklishProfileEditor
from llm import LLMAssistant
from themes import THEMES, TONE_MAPPING, TONE_LABELS


class WritingAssistantApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Ελληνικός Βοηθός Γραφής")
        
        # Load configuration
        self.config = ConfigManager()
        
        # Apply saved window size
        width = self.config.get("window_width", 1380)
        height = self.config.get("window_height", 690)
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(1430, 690)
        
        # Initialize LLM with config values
        self.llm = LLMAssistant()
        self.llm.OPENAI_BASE_URL = self.config.get("llm_endpoint", "http://localhost:1234/v1")
        self.llm.OPENAI_MODEL = self.config.get("llm_model", "llm_model")
        self.llm.OPENAI_API_KEY = self.config.get("llm_api_key", "random-api-key")
        
        # Initialize variables from config
        self.theme_name = self.config.get("theme", "dark")
        self.auto_convert_var = tk.BooleanVar(value=self.config.get("auto_convert", True))
        self.auto_tonify_var = tk.BooleanVar(value=self.config.get("auto_tonify", False))
        self.auto_switch_var = tk.BooleanVar(value=self.config.get("auto_switch_window", False))
        self.auto_switch_var.trace_add("write", lambda *_: self.config.set("auto_switch_window", self.auto_switch_var.get()))
        self._tonify_timer = None
        self._llm_running = False

        self.tone_var = tk.StringVar(value=self.config.get("default_tone", "Μόνο διόρθωση γραμματικής και ορθογραφίας"))
        self.target_lang_var = tk.StringVar(value=self.config.get("last_language", "English"))
        
        # Load custom greeklish profile
        self.greeklish_profile = self.config.load_greeklish_profile(
            self.config.get("active_greeklish_profile", "default")
        )
        if self.greeklish_profile:
            converter.GREEKLISH_MULTI = self.greeklish_profile.get("multi", converter.GREEKLISH_MULTI)
            converter.GREEKLISH_SINGLE = self.greeklish_profile.get("single", converter.GREEKLISH_SINGLE)
        
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

        ttk.Checkbutton(top, text="Εναλλαγή παραθύρου (Ctrl+Shift+C)", variable=self.auto_switch_var, style="Card.TCheckbutton").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(top, text="Αυτόματη μετατροπή", variable=self.auto_convert_var, style="Card.TCheckbutton").pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(top, text="Αυτόματη Βελτίωση", variable=self.auto_tonify_var, style="Card.TCheckbutton").pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(top, text="Εναλλαγή θέματος (Ctrl+D)", command=self.toggle_theme).pack(side=tk.RIGHT, padx=(0, 8))
        ttk.Button(top, text="Ρυθμίσεις", command=self._open_settings).pack(side=tk.RIGHT, padx=(0, 8))
        ttk.Button(top, text="Παραδείγματα διαφορετικών τόνων", command=self._open_tone_examples).pack(side=tk.RIGHT, padx=(0, 8))
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
            text="`word`: passthrough  |  Ctrl+I: βελτίωση  |  Ctrl+L: κατάργηση  |  Ctrl+Shift+C: αντιγραφή  |  Ctrl+D: θέμα",
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
            values=TONE_LABELS,
            state="readonly",
            width=45,
            style="Card.TCombobox",
        )
        tone_combo.pack(side=tk.LEFT, padx=(4, 0))

        self.llm_btn = ttk.Button(actions, text="LLM: Βελτίωση (Ctrl+I)", command=self.improve_with_llm)
        self.llm_btn.pack(side=tk.LEFT, padx=8)

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

    # ── Clipboard / clear ────────────────────────────────────────────────────
    def _copy_output(self):
        text = self.output_text.get("1.0", tk.END).rstrip("\n")
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self._set_status("Αντιγράφηκε στο πρόχειρο.")
            if self.auto_switch_var.get():
                self.root.after(100, self._switch_to_previous_window)

    def _switch_to_previous_window(self):
        if _SYSTEM == "Windows":
            self._switch_previous_windows()
        elif _SYSTEM == "Linux":
            self._switch_previous_linux()

    def _switch_previous_windows(self):
        user32 = ctypes.windll.user32
        GW_HWNDNEXT = 2
        our_hwnd = user32.GetForegroundWindow()
        prev_hwnd = user32.GetWindow(our_hwnd, GW_HWNDNEXT)
        while prev_hwnd:
            if user32.IsWindowVisible(prev_hwnd):
                break
            prev_hwnd = user32.GetWindow(prev_hwnd, GW_HWNDNEXT)
        if prev_hwnd:
            if user32.IsIconic(prev_hwnd):   # only restore if minimized, never touch maximized
                user32.ShowWindow(prev_hwnd, 9)  # SW_RESTORE
            user32.SetForegroundWindow(prev_hwnd)

    def _switch_previous_linux(self):
        try:
            # _NET_CLIENT_LIST_STACKING: bottom→top; last entry is our (topmost) window
            raw = subprocess.check_output(
                ["xprop", "-root", "_NET_CLIENT_LIST_STACKING"], text=True
            )
            ids_str = raw.split("#", 1)[1]
            win_ids = [int(x.strip().rstrip(","), 16) for x in ids_str.split() if x.strip().rstrip(",")]
            if len(win_ids) >= 2:
                subprocess.run(["xdotool", "windowactivate", "--sync", str(win_ids[-2])], check=False)
        except Exception:
            pass

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
            self.convert_text(source=text)
        # 5-second debounce for auto-tonify
        if self._tonify_timer is not None:
            self.root.after_cancel(self._tonify_timer)
            self._tonify_timer = None
        if self.auto_tonify_var.get():
            self._tonify_timer = self.root.after(5000, self._auto_tonify_fire)

    def _auto_tonify_fire(self):
        self._tonify_timer = None
        if self.auto_tonify_var.get() and not self._llm_running:
            self.improve_with_llm()

    def convert_text(self, source: str | None = None):
        if source is None:
            source = self.input_text.get("1.0", tk.END).rstrip("\n")
        converted = greeklish_to_greek(source)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", converted)

    # ── LLM helpers (threaded) ───────────────────────────────────────────────
    def _set_llm_buttons_state(self, state: str):
        for btn in (self.llm_btn, self.translate_btn):
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
        """Improve text with tone, grammar, and orthography. Grammar-only mode skips tone changes."""
        text = self.output_text.get("1.0", tk.END).rstrip("\n") or self.input_text.get("1.0", tk.END).rstrip("\n")
        if not text.strip():
            return
        greek_tone = self.tone_var.get()
        tone = TONE_MAPPING.get(greek_tone, "professional but friendly")
        # Always use improve_tone_grammar_orthography - it handles both tone and grammar-only modes
        self._llm_action(lambda: self.llm.improve_tone_grammar_orthography(text=text, tone=tone))

    def improve_tone_grammar(self):
        """Deprecated: use improve_with_llm() instead."""
        self.improve_with_llm()

    def translate_text(self):
        text = self.output_text.get("1.0", tk.END).rstrip("\n") or self.input_text.get("1.0", tk.END).rstrip("\n")
        target_lang = self.target_lang_var.get()
        self._llm_action(lambda: self.llm.translate(text=text, source_lang="Greek", target_lang=target_lang))

    def _open_settings(self):
        """Open the Settings dialog."""
        SettingsDialog(self.root, self.config, self.llm, self)

    def _open_tone_examples(self):
        """Open the Tone Examples dialog with current text."""
        current_text = self.output_text.get("1.0", tk.END).strip()
        ToneExamplesDialog(self.root, self.llm, current_text)

    def _open_greeklish_editor(self):
        """Open the Greeklish Profile Editor dialog."""
        GreeklishProfileEditor(self.root, self.config, self)

    def _check_connection(self):
        """Check if LLM is available and update connection status indicator."""
        def check():
            try:
                self.llm.check_connection()
                status = "[Online]"
                self.root.after(0, lambda: self.connection_status_label.configure(text=status, foreground="#4CAF50"))
            except Exception:
                status = "[Offline]"
                self.root.after(0, lambda: self.connection_status_label.configure(text=status, foreground="#F44336"))

        threading.Thread(target=check, daemon=True).start()

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
