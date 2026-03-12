import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import json
import threading


class SettingsDialog(tk.Toplevel):
    """Settings dialog for app configuration."""

    def __init__(self, parent, config, llm_assistant, app_callback=None):
        super().__init__(parent)
        self.title("Ρυθμίσεις")
        self.geometry("350x500")
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
        self.tone_var = tk.StringVar(value=self.config_manager.get("default_tone", "Μόνο διόρθωση γραμματικής και ορθογραφίας"))
        tone_combo = ttk.Combobox(
            frame,
            textvariable=self.tone_var,
            values=[
                "Μόνο διόρθωση γραμματικής και ορθογραφίας",
                "Επαγγελματικός αλλά φιλικός",
                "Επίσημος",
                "Χαλαρός",
                "Ακαδημαϊκός",
                "Πειστικός",
            ],
            state="readonly",
            width=45,
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
        ttk.Checkbutton(frame, text="Αυτόματη μετατροπή", variable=self.auto_convert_var).pack(
            anchor=tk.W, pady=(0, 5)
        )

        self.auto_tonify_var = tk.BooleanVar(value=self.config_manager.get("auto_tonify", False))
        ttk.Checkbutton(frame, text="Αυτόματη Βελτίωση (5 δευτερόλεπτα)", variable=self.auto_tonify_var).pack(
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
        try:
            self.config_manager.set("theme", self.theme_var.get())
            self.config_manager.set("font_size", self.font_size_var.get())
            self.config_manager.set("default_tone", self.tone_var.get())
            self.config_manager.set("llm_endpoint", self.endpoint_var.get())
            self.config_manager.set("llm_model", self.model_var.get())
            self.config_manager.set("llm_api_key", self.config_manager.get("llm_api_key", "random-api-key"))
            self.config_manager.set("auto_convert", self.auto_convert_var.get())
            self.config_manager.set("auto_tonify", self.auto_tonify_var.get())
            self.config_manager.save()
            
            # Update LLM settings
            self.llm_assistant.OPENAI_BASE_URL = self.endpoint_var.get()
            self.llm_assistant.OPENAI_MODEL = self.model_var.get()
            self.llm_assistant.OPENAI_API_KEY = self.config_manager.get("llm_api_key", "random-api-key")
            # Apply theme change immediately if app callback is provided
            if self.app_callback:
                if self.app_callback.theme_name != self.theme_var.get():
                    self.app_callback.theme_name = self.theme_var.get()
                    self.app_callback._apply_theme()
                # Refresh connection status with new endpoint
                self.app_callback._check_connection()
            
            messagebox.showinfo("Αποθήκευση", "✅ Ρυθμίσεις αποθηκεύτηκαν με επιτυχία!")
            self.result = True
            self.destroy()
        except Exception as exc:
            messagebox.showerror("Σφάλμα", f"❌ Αποτυχία αποθήκευσης: {exc}")


class ToneExamplesDialog(tk.Toplevel):
    """Show examples of each tone."""

    TONES = {
        "Μόνο διόρθωση γραμματικής και ορθογραφίας": "correct grammar and spelling only, no tone changes",
        "Επαγγελματικός αλλά φιλικός": "professional but friendly",
        "Επίσημος": "formal",
        "Χαλαρός": "casual",
        "Ακαδημαϊκός": "academic",
        "Πειστικός": "persuasive",
    }

    def __init__(self, parent, llm_assistant):
        super().__init__(parent)
        self.title("Παραδείγματα τόνων")
        self.geometry("900x550")
        self.llm_assistant = llm_assistant
        self.examples = {}
        self.loading = set()

        self._build_ui()
        self._auto_load_all_examples()

    def _build_ui(self):
        """Build UI with tone list and example display."""
        # Left panel: tone list
        left_frame = ttk.Frame(self)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=10, pady=10)

        ttk.Label(left_frame, text="Διαθέσιμοι τόνοι:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))

        # Listbox with scrollbar
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tone_listbox = tk.Listbox(list_frame, width=25, yscrollcommand=scrollbar.set, font=("Arial", 9))
        self.tone_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tone_listbox.yview)

        # Add tones to listbox
        for tone in self.TONES.keys():
            self.tone_listbox.insert(tk.END, tone)
            self.examples[tone] = "⏳ Φόρτωση..."

        self.tone_listbox.bind("<<ListboxSelect>>", self._on_tone_select)
        self.tone_listbox.select_set(0)

        # Right panel: example display
        right_frame = ttk.Frame(self)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(right_frame, text="Παράδειγμα:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))

        self.text = tk.Text(right_frame, wrap=tk.WORD, height=25, width=60, font=("Arial", 9))
        self.text.pack(fill=tk.BOTH, expand=True)
        self.text.config(state=tk.DISABLED)

        # Display first tone
        self._show_example()

    def _load_examples(self):
        """Load cached examples or mark for fetching."""
        for tone in self.TONES.keys():
            self.examples[tone] = "Κάντε κλικ για παράδειγμα..."

    def _on_tone_select(self, event):
        """Handle tone selection from listbox."""
        selection = self.tone_listbox.curselection()
        if selection:
            self._show_example()

    def _show_example(self):
        """Display current example."""
        selection = self.tone_listbox.curselection()
        if not selection:
            return
        tone = self.tone_listbox.get(selection[0])
        self.text.config(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", self.examples.get(tone, "Φόρτωση..."))
        self.text.config(state=tk.DISABLED)

    def _auto_load_all_examples(self):
        """Automatically load all tone examples in background thread."""
        thread = threading.Thread(target=self._fetch_all_examples_batch, daemon=True)
        thread.start()

    def _fetch_all_examples_batch(self):
        """Fetch all tone examples in one LLM call for speed."""
        sample_text = "Γεία σας, θα ήθελα να συζητήσω το νέο πρόγραμμα που ξεκίνησε πρόσφατα."
        
        # Create batch request for all tones
        prompt = f"""Rewrite this text in 6 different styles. Return ONLY the rewrites with these exact prefixes:

professional_but_friendly: [rewrite]
formal: [rewrite]
casual: [rewrite]
academic: [rewrite]
persuasive: [rewrite]
grammar_only: [rewrite]

Text: "{sample_text}" """

        try:
            result = self.llm_assistant._invoke(prompt, "")
            self._parse_batch_response(result)
        except Exception as exc:
            for tone in self.TONES.keys():
                self.examples[tone] = f"❌ Σφάλμα: {str(exc)[:40]}"
            self._show_example()

    def _parse_batch_response(self, response):
        """Parse batch response and update examples."""
        tone_keys = {
            "professional_but_friendly": "Επαγγελματικός αλλά φιλικός",
            "formal": "Επίσημος",
            "casual": "Περιστασιακός",
            "academic": "Ακαδημαϊκός",
            "persuasive": "Πειστικός",
            "grammar_only": "Μόνο διόρθωση γραμματικής",
        }
        
        try:
            lines = response.strip().split('\n')
            current_key = None
            current_text = []
            
            for line in lines:
                line_stripped = line.strip()
                
                # Check if this line starts with a key
                found_key = False
                for key in tone_keys.keys():
                    if line_stripped.lower().startswith(key + ":"):
                        # Save previous key if any
                        if current_key and current_key in tone_keys:
                            text_content = ' '.join(current_text).strip()
                            if text_content:
                                self.examples[tone_keys[current_key]] = text_content
                        
                        # Start new key
                        current_key = key
                        # Extract text after the colon
                        rest = line_stripped[len(key)+1:].strip()
                        current_text = [rest] if rest else []
                        found_key = True
                        break
                
                # If not a new key, append to current text
                if not found_key and current_key and line_stripped:
                    current_text.append(line_stripped)
            
            # Save last key
            if current_key and current_key in tone_keys:
                text_content = ' '.join(current_text).strip()
                if text_content:
                    self.examples[tone_keys[current_key]] = text_content
        except Exception as e:
            pass
        
        # Fill any missing with placeholder
        for gr_tone in self.TONES.keys():
            if gr_tone not in self.examples or not self.examples[gr_tone]:
                self.examples[gr_tone] = "⏳ Φόρτωση..."
        
        # Refresh display
        self.loading.clear()
        self._show_example()
