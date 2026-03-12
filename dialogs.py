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
    """Show examples of each tone with selectable results."""

    TONES = {
        "Μόνο διόρθωση γραμματικής και ορθογραφίας": "correct grammar and spelling only, no tone changes",
        "Επαγγελματικός αλλά φιλικός": "professional but friendly",
        "Επίσημος": "formal",
        "Χαλαρός": "casual",
        "Ακαδημαϊκός": "academic",
        "Πειστικός": "persuasive",
    }

    def __init__(self, parent, llm_assistant, initial_text=""):
        super().__init__(parent)
        self.title("Παραδείγματα τόνων")
        self.geometry("1000x700")
        self.llm_assistant = llm_assistant
        self.examples = {}
        self.selected_tone = tk.StringVar()
        self.input_text = initial_text

        self._build_ui()

    def _build_ui(self):
        """Build UI with input and tone examples."""
        # Top frame: Input text
        input_frame = ttk.LabelFrame(self, text="Κείμενο προς βελτίωση", padding=10)
        input_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=10)

        self.text_input = tk.Text(input_frame, wrap=tk.WORD, height=3, font=("Arial", 10))
        self.text_input.pack(fill=tk.BOTH, expand=True)
        if self.input_text:
            self.text_input.insert("1.0", self.input_text)

        # Button frame
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(button_frame, text="Δημιουργία παραδειγμάτων", command=self._generate_examples).pack(side=tk.LEFT)
        
        # Status label
        self.status_label = ttk.Label(button_frame, text="", font=("Arial", 9, "italic"), foreground="blue")
        self.status_label.pack(side=tk.LEFT, padx=(20, 0))

        # Main content frame
        content_frame = ttk.Frame(self)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tones list on the left
        left_frame = ttk.LabelFrame(content_frame, text="Διαθέσιμοι τόνοι", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))

        self.tone_var = tk.StringVar()
        for tone in self.TONES.keys():
            rb = ttk.Radiobutton(
                left_frame,
                text=tone,
                variable=self.tone_var,
                value=tone,
                command=self._show_selected_example
            )
            rb.pack(anchor=tk.W, pady=5)
        
        # Set first tone as selected
        if self.TONES.keys():
            self.tone_var.set(list(self.TONES.keys())[0])

        # Examples on the right
        right_frame = ttk.LabelFrame(content_frame, text="Β Όταν κάνετε κλικ στον τόνο δείχνει το αποτέλεσμα", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.example_text = tk.Text(right_frame, wrap=tk.WORD, height=15, width=60, font=("Arial", 10))
        self.example_text.pack(fill=tk.BOTH, expand=True)
        self.example_text.config(state=tk.DISABLED)

        # Button frame at bottom
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(bottom_frame, text="Αντιγραφή επιλογής", command=self._copy_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(bottom_frame, text="Κλείσιμο", command=self.destroy).pack(side=tk.LEFT)

    def _generate_examples(self):
        """Generate tone examples for the input text."""
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            self.status_label.config(text="❌ Παρακαλώ εισάγετε κείμενο", foreground="red")
            return
        
        self.examples.clear()
        self.status_label.config(text="⏳ Δημιουργία παραδειγμάτων...", foreground="blue")
        self.update()

        thread = threading.Thread(target=self._fetch_examples_for_text, args=(text,), daemon=True)
        thread.start()

    def _fetch_examples_for_text(self, text):
        """Fetch improved versions in parallel using threads."""
        import threading
        
        tones_list = list(self.TONES.keys())
        threads = []
        completed_count = [0]  # Use list to allow modification in nested function
        
        def fetch_single_tone(tone):
            """Fetch a single tone example."""
            try:
                result = self.llm_assistant.improve_tone_grammar_orthography(text, tone)
                self.examples[tone] = result.strip()
            except Exception as exc:
                self.examples[tone] = f"❌ Σφάλμα: {str(exc)[:50]}"
            
            # Update progress
            completed_count[0] += 1
            self.after(0, self._update_progress, completed_count[0], len(tones_list))
        
        # Start all threads in parallel
        for tone in tones_list:
            thread = threading.Thread(target=fetch_single_tone, args=(tone,), daemon=True)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete, then show final status
        def wait_and_finish():
            for thread in threads:
                thread.join()
            self.after(0, self._update_ui_after_generation)
        
        completion_thread = threading.Thread(target=wait_and_finish, daemon=True)
        completion_thread.start()
    
    def _update_progress(self, completed, total):
        """Update progress counter."""
        self.status_label.config(
            text=f"⏳ Φόρτωση: {completed}/{total} παραδείγματα...",
            foreground="blue"
        )
        # Show example as soon as first one completes
        if completed == 1:
            self._show_selected_example()

    def _update_ui_after_generation(self):
        """Update UI after examples are generated."""
        self.status_label.config(text="✅ Έτοιμα! Επιλέξτε έναν τόνο", foreground="green")
        self._show_selected_example()

    def _show_selected_example(self):
        """Display the selected tone's example."""
        tone = self.tone_var.get()
        if not tone:
            return
        
        example = self.examples.get(tone, "Δεν έχει παράδειγμα")
        self.example_text.config(state=tk.NORMAL)
        self.example_text.delete("1.0", tk.END)
        self.example_text.insert("1.0", example)
        self.example_text.config(state=tk.DISABLED)

    def _copy_selected(self):
        """Copy the selected example to clipboard."""
        tone = self.tone_var.get()
        if not tone or tone not in self.examples:
            messagebox.showwarning("Προσοχή", "Δεν υπάρχει επιλεγμένο παράδειγμα")
            return
        
        example = self.examples[tone]
        self.clipboard_clear()
        self.clipboard_append(example)
        messagebox.showinfo("Αντιγραφή", "✅ Το παράδειγμα αντιγράφηκε!")


