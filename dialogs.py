import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import json


class SettingsDialog(tk.Toplevel):
    """Settings dialog for app configuration."""

    def __init__(self, parent, config, llm_assistant, app_callback=None):
        super().__init__(parent)
        self.title("Ρυθμίσεις")
        self.geometry("500x450")
        self.config_manager = config
        self.llm_assistant = llm_assistant
        self.app_callback = app_callback
        self.result = None

        self._build_ui()

    def _build_ui(self):
        """Build settings UI."""
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        # Theme
        ttk.Label(frame, text="Θέμα:").pack(anchor=tk.W, pady=(0, 5))
        self.theme_var = tk.StringVar(value=self.config_manager.get("theme", "dark"))
        theme_combo = ttk.Combobox(
            frame,
            textvariable=self.theme_var,
            values=["dark", "light"],
            state="readonly",
            width=20,
        )
        theme_combo.pack(anchor=tk.W, pady=(0, 15))

        # Font Size
        ttk.Label(frame, text="Μέγεθος γραμματοσειράς:").pack(anchor=tk.W, pady=(0, 5))
        self.font_size_var = tk.IntVar(value=self.config_manager.get("font_size", 11))
        font_spin = ttk.Spinbox(
            frame,
            from_=8,
            to=24,
            textvariable=self.font_size_var,
            width=10,
        )
        font_spin.pack(anchor=tk.W, pady=(0, 15))

        # Default Tone
        ttk.Label(frame, text="Προεπιλεγμένος τόνος:").pack(anchor=tk.W, pady=(0, 5))
        self.tone_var = tk.StringVar(value=self.config_manager.get("default_tone", "Μόνο διόρθωση γραμματικής"))
        tone_combo = ttk.Combobox(
            frame,
            textvariable=self.tone_var,
            values=[
                "Επαγγελματικός αλλά φιλικός",
                "Επίσημος",
                "Περιστασιακός",
                "Ακαδημαϊκός",
                "Πειστικός",
                "Μόνο διόρθωση γραμματικής",
            ],
            state="readonly",
            width=30,
        )
        tone_combo.pack(anchor=tk.W, pady=(0, 15))

        # LLM Endpoint
        ttk.Label(frame, text="LLM Endpoint:").pack(anchor=tk.W, pady=(0, 5))
        self.endpoint_var = tk.StringVar(value=self.config_manager.get("llm_endpoint", "http://localhost:1234/v1"))
        endpoint_entry = ttk.Entry(frame, textvariable=self.endpoint_var, width=40)
        endpoint_entry.pack(anchor=tk.W, pady=(0, 15))

        # LLM Model
        ttk.Label(frame, text="LLM Model:").pack(anchor=tk.W, pady=(0, 5))
        self.model_var = tk.StringVar(value=self.config_manager.get("llm_model", "llm_model"))
        model_entry = ttk.Entry(frame, textvariable=self.model_var, width=40)
        model_entry.pack(anchor=tk.W, pady=(0, 20))

        # Checkboxes
        self.auto_convert_var = tk.BooleanVar(value=self.config_manager.get("auto_convert", True))
        ttk.Checkbutton(frame, text="Αυτόματη μετατροπή Greeklish", variable=self.auto_convert_var).pack(
            anchor=tk.W, pady=(0, 5)
        )

        self.auto_tonify_var = tk.BooleanVar(value=self.config_manager.get("auto_tonify", False))
        ttk.Checkbutton(frame, text="Αυτόματη προσθήκη τόνων (5 δευτερόλεπτα)", variable=self.auto_tonify_var).pack(
            anchor=tk.W, pady=(0, 20)
        )

        # Test Connection Button
        ttk.Button(frame, text="Δοκιμάστε σύνδεση", command=self._test_connection).pack(anchor=tk.W, pady=(0, 10))

        # Buttons frame at bottom
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(fill=tk.X, pady=(20, 0))
        ttk.Button(buttons_frame, text="Αποθήκευση", command=self._save).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="Άκυρο", command=self.destroy).pack(side=tk.LEFT)

    def _test_connection(self):
        """Test LLM connection."""
        try:
            self.llm_assistant.OPENAI_BASE_URL = self.endpoint_var.get()
            self.llm_assistant.OPENAI_MODEL = self.model_var.get()
            result = self.llm_assistant._invoke("Say 'OK' only.", "Test")
            if "OK" in result:
                messagebox.showinfo("Σύνδεση", "✅ Σύνδεση επιτυχής!")
            else:
                messagebox.showinfo("Σύνδεση", f"Απάντηση: {result[:50]}")
        except Exception as exc:
            messagebox.showerror("Σφάλμα σύνδεσης", f"❌ Σφάλμα: {exc}")

    def _save(self):
        """Save settings and close."""
        self.config_manager.set("theme", self.theme_var.get())
        self.config_manager.set("font_size", self.font_size_var.get())
        self.config_manager.set("default_tone", self.tone_var.get())
        self.config_manager.set("llm_endpoint", self.endpoint_var.get())
        self.config_manager.set("llm_model", self.model_var.get())
        self.config_manager.set("auto_convert", self.auto_convert_var.get())
        self.config_manager.set("auto_tonify", self.auto_tonify_var.get())
        self.config_manager.save()
        
        # Apply theme change immediately if app callback is provided
        if self.app_callback:
            if self.app_callback.theme_name != self.theme_var.get():
                self.app_callback.theme_name = self.theme_var.get()
                self.app_callback._apply_theme()
        
        self.result = True
        self.destroy()


class ToneExamplesDialog(tk.Toplevel):
    """Show examples of each tone."""

    TONES = {
        "Επαγγελματικός αλλά φιλικός": "professional but friendly",
        "Επίσημος": "formal",
        "Περιστασιακός": "casual",
        "Ακαδημαϊκός": "academic",
        "Πειστικός": "persuasive",
        "Μόνο διόρθωση γραμματικής": "correct grammar only",
    }

    def __init__(self, parent, llm_assistant):
        super().__init__(parent)
        self.title("Παραδείγματα τόνων")
        self.geometry("700x500")
        self.llm_assistant = llm_assistant
        self.examples = {}

        self._build_ui()
        self._load_examples()

    def _build_ui(self):
        """Build UI with tone selector."""
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(top, text="Τόνος:").pack(side=tk.LEFT, padx=(0, 10))
        self.tone_var = tk.StringVar(value=list(self.TONES.keys())[0])
        tone_combo = ttk.Combobox(
            top,
            textvariable=self.tone_var,
            values=list(self.TONES.keys()),
            state="readonly",
            width=30,
        )
        tone_combo.pack(side=tk.LEFT)
        tone_combo.bind("<<ComboboxSelected>>", lambda _: self._show_example())

        ttk.Button(top, text="Φόρτωση παραδείγματος", command=lambda: self._fetch_example(self.tone_var.get())).pack(
            side=tk.LEFT, padx=10
        )

        # Text display
        self.text = tk.Text(self, wrap=tk.WORD, height=20, width=80)
        self.text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.text.config(state=tk.DISABLED)

        self._show_example()

    def _load_examples(self):
        """Load cached examples or mark for fetching."""
        for tone in self.TONES.keys():
            self.examples[tone] = "Κάντε κλικ 'Φόρτωση παραδείγματος' για παράδειγμα..."

    def _show_example(self):
        """Display current example."""
        tone = self.tone_var.get()
        self.text.config(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", self.examples.get(tone, "Φόρτωση..."))
        self.text.config(state=tk.DISABLED)

    def _fetch_example(self, tone):
        """Fetch tone example from LLM."""
        sample_text = "Γεια σας, θα ήθελα να συζητήσω το νέο πρόγραμμα που ξεκίνησε πρόσφατα."
        tone_en = self.TONES[tone]
        try:
            self.text.config(state=tk.NORMAL)
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", "⏳ Φόρτωση...")
            self.text.config(state=tk.DISABLED)
            self.update()

            result = self.llm_assistant._invoke(
                f"Rewrite the following in a {tone_en} style. Return ONLY the rewritten text:\n{sample_text}",
                "",
            )
            self.examples[tone] = result
            self._show_example()
        except Exception as exc:
            messagebox.showerror("Σφάλμα", f"Δεν ήταν δυνατό να φορτωθεί το παράδειγμα: {exc}")
