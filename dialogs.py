import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import json
import threading
from themes import THEMES


class UnifiedSettingsDialog(tk.Toplevel):
    """Unified settings dialog with tabs for General and Greeklish settings."""

    def __init__(self, parent, config, llm_assistant, app_callback=None, theme_name="dark"):
        super().__init__(parent)
        self.title("Ρυθμίσεις")
        self.geometry("600x700")
        self.config_manager = config
        self.llm_assistant = llm_assistant
        self.app_callback = app_callback
        self.result = None
        self.theme_name = theme_name
        self.style = ttk.Style()

        self._apply_theme()
        self._build_ui()

    def _apply_theme(self):
        """Apply the current theme to the dialog."""
        theme = THEMES[self.theme_name]
        self.configure(bg=theme["bg"])
        self.style.configure("TFrame", background=theme["bg"])
        self.style.configure("TLabel", background=theme["bg"], foreground=theme["fg"])
        self.style.configure("TLabelFrame", background=theme["bg"], foreground=theme["fg"])
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
        self.style.configure("TCombobox", fieldbackground=theme["card"], background=theme["card"], foreground=theme["fg"])
        self.style.map("TCombobox", fieldbackground=[("readonly", theme["card"])])


    def _build_ui(self):
        """Build the tabbed settings UI."""
        # Create main notebook for tabs
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # General tab
        general_frame = ttk.Frame(notebook, padding=15)
        notebook.add(general_frame, text="Γενικά")
        self._build_general_tab(general_frame)

        # Greeklish tab
        greeklish_frame = ttk.Frame(notebook)
        notebook.add(greeklish_frame, text="Greeklish")
        self._build_greeklish_tab(greeklish_frame)

        # Shortcuts tab
        shortcuts_frame = ttk.Frame(notebook, padding=15)
        notebook.add(shortcuts_frame, text="Συντομεύσεις")
        self._build_shortcuts_tab(shortcuts_frame)

        # Buttons frame at bottom
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(buttons_frame, text="Αποθήκευση", command=self._save).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="Επαναφορά στις προεπιλογές", command=self._reset_to_defaults).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="Άκυρο", command=self.destroy).pack(side=tk.LEFT)

    def _build_general_tab(self, parent):
        """Build the General settings tab."""
        # Theme
        ttk.Label(parent, text="Θέμα:").pack(anchor=tk.W, pady=(0, 5))
        self.theme_var = tk.StringVar(value=self.config_manager.get("theme", "dark"))
        theme_combo = ttk.Combobox(
            parent,
            textvariable=self.theme_var,
            values=["dark", "light"],
            state="readonly",
            width=20,
        )
        theme_combo.pack(anchor=tk.W, pady=(0, 15))

        # Default Tone
        ttk.Label(parent, text="Προεπιλεγμένος τόνος:").pack(anchor=tk.W, pady=(0, 5))
        self.tone_var = tk.StringVar(value=self.config_manager.get("default_tone", "Μόνο διόρθωση γραμματικής και ορθογραφίας"))
        tone_combo = ttk.Combobox(
            parent,
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
        ttk.Label(parent, text="LLM Endpoint:").pack(anchor=tk.W, pady=(0, 5))
        self.endpoint_var = tk.StringVar(value=self.config_manager.get("llm_endpoint", "http://localhost:1234/v1"))
        endpoint_entry = ttk.Entry(parent, textvariable=self.endpoint_var, width=40)
        endpoint_entry.pack(anchor=tk.W, pady=(0, 15))

        # LLM Model
        ttk.Label(parent, text="LLM Model:").pack(anchor=tk.W, pady=(0, 5))
        self.model_var = tk.StringVar(value=self.config_manager.get("llm_model", "llm_model"))
        model_entry = ttk.Entry(parent, textvariable=self.model_var, width=40)
        model_entry.pack(anchor=tk.W, pady=(0, 15))

        # LLM API Key
        ttk.Label(parent, text="LLM API Key:").pack(anchor=tk.W, pady=(0, 5))
        self.api_key_var = tk.StringVar(value=self.config_manager.get("llm_api_key", ""))
        api_key_entry = ttk.Entry(parent, textvariable=self.api_key_var, width=40, show="*")
        api_key_entry.pack(anchor=tk.W, pady=(0, 20))

        # Test Connection Button
        ttk.Button(parent, text="Δοκιμάστε σύνδεση", command=self._test_connection).pack(anchor=tk.W, pady=(0, 10))

    def _build_greeklish_tab(self, parent):
        """Build the Greeklish profile editor tab."""
        self.greeklish_config_manager = self.config_manager
        self.current_greeklish_profile = self.config_manager.get("active_greeklish_profile", "default")
        self.greeklish_mappings = self._load_greeklish_profile()
        
        # Initialize defaults from converter
        from converter import GREEKLISH_MULTI, GREEKLISH_SINGLE
        self.default_greeklish_multi = GREEKLISH_MULTI.copy()
        self.default_greeklish_single = GREEKLISH_SINGLE.copy()
        
        # Top bar with profile selection
        top = ttk.Frame(parent)
        top.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(top, text="Προφίλ:").pack(side=tk.LEFT, padx=(0, 10))
        self.greeklish_profile_var = tk.StringVar(value=self.current_greeklish_profile)
        profile_combo = ttk.Combobox(
            top,
            textvariable=self.greeklish_profile_var,
            values=self.config_manager.list_greeklish_profiles(),
            state="readonly",
            width=20,
        )
        profile_combo.pack(side=tk.LEFT, padx=(0, 10))
        profile_combo.bind("<<ComboboxSelected>>", self._on_greeklish_profile_change)

        ttk.Button(top, text="Νέο", command=self._new_greeklish_profile).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text="Αποθήκευση", command=self._save_greeklish_profile).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text="Διαγραφή", command=self._delete_greeklish_profile).pack(side=tk.LEFT, padx=2)

        # Notebook for tabs
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Multi-character mappings tab
        multi_frame = ttk.Frame(notebook)
        notebook.add(multi_frame, text="Διπλά χαρακτήρα")
        self._build_greeklish_mapping_tab(multi_frame, "multi")

        # Single character mappings tab
        single_frame = ttk.Frame(notebook)
        notebook.add(single_frame, text="Απλά χαρακτήρα")
        self._build_greeklish_mapping_tab(single_frame, "single")

    def _load_greeklish_profile(self) -> dict:
        """Load the current greeklish profile or create default."""
        profile = self.config_manager.load_greeklish_profile(self.current_greeklish_profile)
        if not profile:
            from converter import GREEKLISH_MULTI, GREEKLISH_SINGLE
            profile = {
                "multi": GREEKLISH_MULTI.copy(),
                "single": GREEKLISH_SINGLE.copy(),
            }
        return profile

    def _build_greeklish_mapping_tab(self, parent, mapping_type):
        """Build a tab for editing greeklish mappings."""
        frame = ttk.Frame(parent, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Create treeview
        columns = ("Greeklish", "Ελληνικά")
        tree = ttk.Treeview(frame, columns=columns, height=15, show="headings")
        tree.column("Greeklish", width=100)
        tree.column("Ελληνικά", width=100)
        tree.heading("Greeklish", text="Greeklish")
        tree.heading("Ελληνικά", text="Ελληνικά")

        # Bind right-click for editing
        tree.bind("<Double-1>", lambda e: self._edit_greeklish_mapping(tree, mapping_type))

        # Load mappings
        mappings = self.greeklish_mappings.get(mapping_type, {})
        for source, target in mappings.items():
            tree.insert("", tk.END, values=(source, target))

        tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(
            btn_frame,
            text="Προσθήκη",
            command=lambda: self._add_greeklish_mapping(tree, mapping_type),
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            btn_frame,
            text="Επεξεργασία",
            command=lambda: self._edit_greeklish_mapping(tree, mapping_type),
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            btn_frame,
            text="Διαγραφή",
            command=lambda: self._delete_greeklish_mapping(tree, mapping_type),
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Reset", command=lambda: self._reset_greeklish_tab(tree, mapping_type)).pack(
            side=tk.LEFT, padx=5
        )

        # Store reference for later
        setattr(self, f"greeklish_{mapping_type}_tree", tree)

    def _add_greeklish_mapping(self, tree, mapping_type):
        """Add a new greeklish mapping."""
        dialog = tk.Toplevel(self)
        dialog.title("Προσθήκη χαρτογραφίας")
        dialog.geometry("300x150")

        ttk.Label(dialog, text="Greeklish:").pack(pady=5)
        source_entry = ttk.Entry(dialog, width=20)
        source_entry.pack(pady=5)

        ttk.Label(dialog, text="Ελληνικά:").pack(pady=5)
        target_entry = ttk.Entry(dialog, width=20)
        target_entry.pack(pady=5)

        def save():
            source = source_entry.get()
            target = target_entry.get()
            if source and target:
                self.greeklish_mappings[mapping_type][source] = target
                tree.insert("", tk.END, values=(source, target))
                dialog.destroy()
            else:
                messagebox.showwarning("Σφάλμα", "Συμπληρώστε και τα δύο πεδία.")

        ttk.Button(dialog, text="Αποθήκευση", command=save).pack(pady=10)

    def _edit_greeklish_mapping(self, tree, mapping_type):
        """Edit selected greeklish mapping."""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Σφάλμα", "Επιλέξτε μια σειρά για επεξεργασία.")
            return

        item = selection[0]
        values = tree.item(item, "values")
        source, target = values

        dialog = tk.Toplevel(self)
        dialog.title("Επεξεργασία χαρτογραφίας")
        dialog.geometry("300x150")

        ttk.Label(dialog, text="Greeklish:").pack(pady=5)
        source_entry = ttk.Entry(dialog, width=20)
        source_entry.insert(0, source)
        source_entry.pack(pady=5)

        ttk.Label(dialog, text="Ελληνικά:").pack(pady=5)
        target_entry = ttk.Entry(dialog, width=20)
        target_entry.insert(0, target)
        target_entry.pack(pady=5)

        def save():
            new_source = source_entry.get()
            new_target = target_entry.get()
            if new_source and new_target:
                # Remove old mapping
                if source in self.greeklish_mappings[mapping_type]:
                    del self.greeklish_mappings[mapping_type][source]
                # Add new mapping
                self.greeklish_mappings[mapping_type][new_source] = new_target
                # Update tree
                tree.item(item, values=(new_source, new_target))
                dialog.destroy()
            else:
                messagebox.showwarning("Σφάλμα", "Συμπληρώστε και τα δύο πεδία.")

        ttk.Button(dialog, text="Αποθήκευση", command=save).pack(pady=10)

    def _delete_greeklish_mapping(self, tree, mapping_type):
        """Delete selected greeklish mapping."""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Σφάλμα", "Επιλέξτε μια σειρά για διαγραφή.")
            return

        item = selection[0]
        values = tree.item(item, "values")
        source = values[0]

        if source in self.greeklish_mappings[mapping_type]:
            del self.greeklish_mappings[mapping_type][source]
        tree.delete(item)

    def _reset_greeklish_tab(self, tree, mapping_type):
        """Reset greeklish tab to defaults."""
        if messagebox.askyesno("Επιβεβαίωση", "Επαναφορά στις προεπιλογές;"):
            defaults = self.default_greeklish_multi if mapping_type == "multi" else self.default_greeklish_single
            self.greeklish_mappings[mapping_type] = defaults.copy()
            tree.delete(*tree.get_children())
            for source, target in defaults.items():
                tree.insert("", tk.END, values=(source, target))

    def _on_greeklish_profile_change(self, event=None):
        """Switch to different greeklish profile."""
        new_profile = self.greeklish_profile_var.get()
        self.current_greeklish_profile = new_profile
        self.greeklish_mappings = self._load_greeklish_profile()
        messagebox.showinfo("Προφίλ", f"Προφίλ αλλάγησε σε '{new_profile}'.\nΑποθηκεύστε για να εφαρμοστούν αλλαγές.")

    def _new_greeklish_profile(self):
        """Create new greeklish profile."""
        name = simpledialog.askstring("Νέο προφίλ", "Όνομα προφίλ:")
        if name and name != "default":
            self.greeklish_mappings = {
                "multi": self.default_greeklish_multi.copy(),
                "single": self.default_greeklish_single.copy(),
            }
            self.current_greeklish_profile = name
            self.greeklish_profile_var.set(name)
            self.config_manager.save_greeklish_profile(
                name,
                {"multi": self.default_greeklish_multi.copy(), "single": self.default_greeklish_single.copy()},
            )
            messagebox.showinfo("Επιτυχία", f"Νέο προφίλ '{name}' δημιουργήθηκε.")

    def _save_greeklish_profile(self):
        """Save current greeklish profile."""
        self.config_manager.save_greeklish_profile(self.current_greeklish_profile, self.greeklish_mappings)
        self.config_manager.set("active_greeklish_profile", self.current_greeklish_profile)
        messagebox.showinfo("Επιτυχία", f"Προφίλ '{self.current_greeklish_profile}' αποθηκεύθηκε.")

    def _delete_greeklish_profile(self):
        """Delete current greeklish profile."""
        if self.current_greeklish_profile == "default":
            messagebox.showwarning("Σφάλμα", "Δεν μπορείτε να διαγράψετε το προεπιλεγμένο προφίλ.")
            return
        if messagebox.askyesno("Επιβεβαίωση", f"Διαγραφή '{self.current_greeklish_profile}';"):
            self.config_manager.delete_greeklish_profile(self.current_greeklish_profile)
            self.current_greeklish_profile = "default"
            self.greeklish_profile_var.set("default")
            messagebox.showinfo("Επιτυχία", "Προφίλ διαγράφηκε.")

    def _build_shortcuts_tab(self, parent):
        """Build the Shortcuts editing tab."""
        # Escape character section
        ttk.Label(parent, text="Χαρακτήρας Escape:").pack(anchor=tk.W, pady=(0, 5))
        self.escape_char_var = tk.StringVar(value=self.config_manager.get("escape_character", "`"))
        escape_entry = ttk.Entry(parent, textvariable=self.escape_char_var, width=10)
        escape_entry.pack(anchor=tk.W, pady=(0, 20))

        # Shortcuts section
        ttk.Label(parent, text="Συντομεύσεις:").pack(anchor=tk.W, pady=(0, 5))
        
        shortcuts_config = self.config_manager.get("shortcuts", {})
        self.shortcuts_vars = {}
        
        shortcut_labels = {
            "clear_input": "Καθαρισμός εισόδου",
            "toggle_theme": "Εναλλαγή θέματος",
            "convert_text": "Μετατροπή κειμένου",
            "copy_output": "Αντιγραφή εξόδου",
            "improve_with_llm": "Βελτίωση με LLM",
        }
        
        for key, label in shortcut_labels.items():
            ttk.Label(parent, text=f"{label}:").pack(anchor=tk.W, pady=(0, 5))
            var = tk.StringVar(value=shortcuts_config.get(key, ""))
            self.shortcuts_vars[key] = var
            entry = ttk.Entry(parent, textvariable=var, width=30)
            entry.pack(anchor=tk.W, pady=(0, 15))

    def _test_connection(self):
        """Test LLM connection."""
        try:
            self.llm_assistant.OPENAI_BASE_URL = self.endpoint_var.get()
            self.llm_assistant.OPENAI_MODEL = self.model_var.get()
            self.llm_assistant.OPENAI_API_KEY = self.api_key_var.get()
            result = self.llm_assistant._invoke("Say 'OK' only.", "Test")
            if "OK" in result:
                messagebox.showinfo("Σύνδεση", "✅ Σύνδεση επιτυχής!")
            else:
                messagebox.showinfo("Σύνδεση", f"Απάντηση: {result[:50]}")
        except Exception as exc:
            messagebox.showerror("Σφάλμα σύνδεσης", f"❌ Σφάλμα: {exc}")

    def _reset_to_defaults(self):
        """Reset all settings to defaults."""
        if not messagebox.askyesno("Επιβεβαίωση", "Είστε σίγουρος; Όλες οι ρυθμίσεις θα επαναφερθούν στις προεπιλογές τους."):
            return
        
        from config import ConfigManager
        defaults = ConfigManager.DEFAULT_CONFIG
        
        # Reset General tab
        self.theme_var.set(defaults.get("theme", "dark"))
        self.tone_var.set(defaults.get("default_tone", "Μόνο διόρθωση γραμματικής και ορθογραφίας"))
        self.endpoint_var.set(defaults.get("llm_endpoint", "http://localhost:1234/v1"))
        self.model_var.set(defaults.get("llm_model", "llm_model"))
        self.api_key_var.set(defaults.get("llm_api_key", "random-api-key"))
        
        # Reset Shortcuts tab
        self.escape_char_var.set(defaults.get("escape_character", "`"))
        default_shortcuts = defaults.get("shortcuts", {})
        for key, var in self.shortcuts_vars.items():
            var.set(default_shortcuts.get(key, ""))
        
        messagebox.showinfo("Επαναφορά", "✅ Όλες οι ρυθμίσεις επαναφέρθηκαν στις προεπιλογές τους!")

    def _save(self):
        """Save settings and close."""
        try:
            self.config_manager.set("theme", self.theme_var.get())
            self.config_manager.set("default_tone", self.tone_var.get())
            self.config_manager.set("llm_endpoint", self.endpoint_var.get())
            self.config_manager.set("llm_model", self.model_var.get())
            self.config_manager.set("llm_api_key", self.api_key_var.get())
            self.config_manager.set("escape_character", self.escape_char_var.get())
            
            # Save shortcuts
            shortcuts = {}
            for key, var in self.shortcuts_vars.items():
                shortcuts[key] = var.get()
            self.config_manager.set("shortcuts", shortcuts)
            
            self.config_manager.save()
            
            # Update LLM settings
            self.llm_assistant.OPENAI_BASE_URL = self.endpoint_var.get()
            self.llm_assistant.OPENAI_MODEL = self.model_var.get()
            self.llm_assistant.OPENAI_API_KEY = self.api_key_var.get()
            
            # Apply theme change immediately if app callback is provided
            if self.app_callback:
                if self.app_callback.theme_name != self.theme_var.get():
                    self.app_callback.theme_name = self.theme_var.get()
                    self.app_callback._apply_theme()
                # Refresh connection status with new endpoint
                self.app_callback._check_connection()
                # Reload shortcuts and escape character from config
                self.app_callback.shortcuts = self.config_manager.get("shortcuts", {})
                self.app_callback.escape_character = self.config_manager.get("escape_character", "`")
                # Rebind shortcuts with new configuration
                self.app_callback._rebind_shortcuts()
                # Update the shortcuts display label
                self.app_callback._update_shortcuts_display()
                # Update button labels with new shortcuts
                self.app_callback._update_button_labels()
            
            messagebox.showinfo("Αποθήκευση", "✅ Ρυθμίσεις αποθηκεύτηκαν με επιτυχία!")
            self.result = True
            self.destroy()
        except Exception as exc:
            messagebox.showerror("Σφάλμα", f"❌ Αποτυχία αποθήκευσης: {exc}")


class SettingsDialog(tk.Toplevel):
    """Settings dialog for app configuration (kept for backwards compatibility)."""

    def __init__(self, parent, config, llm_assistant, app_callback=None, theme_name="dark"):
        super().__init__(parent)
        self.title("Ρυθμίσεις")
        self.geometry("350x380")
        self.config_manager = config
        self.llm_assistant = llm_assistant
        self.app_callback = app_callback
        self.result = None
        self.theme_name = theme_name
        self.style = ttk.Style()

        self._apply_theme()
        self._build_ui()

    def _apply_theme(self):
        """Apply the current theme to the dialog."""
        theme = THEMES[self.theme_name]
        self.configure(bg=theme["bg"])
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
        self.style.configure("TCombobox", fieldbackground=theme["card"], background=theme["card"], foreground=theme["fg"])
        self.style.map("TCombobox", fieldbackground=[("readonly", theme["card"])])

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
            self.config_manager.set("default_tone", self.tone_var.get())
            self.config_manager.set("llm_endpoint", self.endpoint_var.get())
            self.config_manager.set("llm_model", self.model_var.get())
            self.config_manager.set("llm_api_key", self.config_manager.get("llm_api_key", "random-api-key"))
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
    """Show all tone examples simultaneously with live updates."""

    TONES = {
        "Μόνο διόρθωση γραμματικής και ορθογραφίας": "correct grammar and spelling only, no tone changes",
        "Επαγγελματικός αλλά φιλικός": "professional but friendly",
        "Επίσημος": "formal",
        "Χαλαρός": "casual",
        "Ακαδημαϊκός": "academic",
        "Πειστικός": "persuasive",
    }

    def __init__(self, parent, llm_assistant, initial_text="", theme_name="dark"):
        super().__init__(parent)
        self.title("Παραδείγματα διαφορετικών τόνων")
        self.geometry("1200x800")
        self.llm_assistant = llm_assistant
        self.examples = {}
        self.tone_widgets = {}
        self.input_text = initial_text
        self.theme_name = theme_name
        self.style = ttk.Style()

        self._apply_theme()
        self._build_ui()

    def _apply_theme(self):
        """Apply the current theme to the dialog."""
        theme = THEMES[self.theme_name]
        self.configure(bg=theme["bg"])
        self.style.configure("TFrame", background=theme["bg"])
        self.style.configure("TLabel", background=theme["bg"], foreground=theme["fg"])
        self.style.configure("TLabelFrame", background=theme["bg"], foreground=theme["fg"])
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

    def _build_ui(self):
        """Build UI with input and live tone examples."""
        theme = THEMES[self.theme_name]
        
        # Top frame: Input text
        input_frame = ttk.LabelFrame(self, text="Κείμενο προς βελτίωση", padding=10)
        input_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=10)

        self.text_input = tk.Text(input_frame, wrap=tk.WORD, height=3, font=("Arial", 10), 
                                   bg=theme["card"], fg=theme["fg"], insertbackground=theme["accent"])
        self.text_input.pack(fill=tk.BOTH, expand=True)
        if self.input_text:
            self.text_input.insert("1.0", self.input_text)

        # Button frame
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(button_frame, text="Δημιουργία παραδειγμάτων", command=self._generate_examples).pack(side=tk.LEFT)
        
        # Status label
        self.status_label = ttk.Label(button_frame, text="", font=("Arial", 9, "italic"), foreground=theme["accent"])
        self.status_label.pack(side=tk.LEFT, padx=(20, 0))

        # Scrollable container for tone examples
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create scrollbar
        scrollbar = ttk.Scrollbar(container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create canvas for scrolling
        self.canvas = tk.Canvas(container, yscrollcommand=scrollbar.set, bg=theme["bg"], highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.canvas.yview)

        # Frame inside canvas
        self.scroll_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")

        # Bind canvas resize to update scroll region
        self.scroll_frame.bind("<Configure>", lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Create tone example widgets
        for tone in self.TONES.keys():
            tone_frame = ttk.LabelFrame(self.scroll_frame, text=tone, padding=10)
            tone_frame.pack(fill=tk.BOTH, expand=False, padx=0, pady=5)

            # Text widget for result
            result_text = tk.Text(tone_frame, wrap=tk.WORD, height=3, width=80, font=("Arial", 10), 
                                 bg=theme["card"], fg=theme["fg"], insertbackground=theme["accent"])
            result_text.pack(fill=tk.BOTH, expand=True)
            result_text.insert("1.0", "⏳ Αναμονή...")
            result_text.config(state=tk.DISABLED)

            # Click binding
            result_text.bind("<Button-1>", lambda e, t=tone: self._copy_tone(t))

            self.tone_widgets[tone] = result_text

        # Button frame at bottom
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(bottom_frame, text="Κλείσιμο", command=self.destroy).pack(side=tk.LEFT)

    def _generate_examples(self):
        """Generate tone examples for the input text in parallel."""
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            self.status_label.config(text="❌ Παρακαλώ εισάγετε κείμενο", foreground="red")
            return
        
        self.examples.clear()
        
        # Reset all displays to waiting state
        for tone, widget in self.tone_widgets.items():
            widget.config(state=tk.NORMAL)
            widget.delete("1.0", tk.END)
            widget.insert("1.0", "⏳ Φόρτωση...")
            widget.config(state=tk.DISABLED)

        self.status_label.config(text="⏳ Δημιουργία παραδειγμάτων...", foreground="blue")
        self.update()

        # Fetch all tones in parallel
        for tone in self.TONES.keys():
            thread = threading.Thread(target=self._fetch_single_tone, args=(text, tone), daemon=True)
            thread.start()

    def _fetch_single_tone(self, text, tone):
        """Fetch a single tone example and display immediately."""
        try:
            result = self.llm_assistant.improve_tone_grammar_orthography(text, tone)
            self.examples[tone] = result.strip()
            # Update widget immediately
            self.after(0, self._update_tone_widget, tone, result.strip())
        except Exception as exc:
            error_msg = f"❌ Σφάλμα: {str(exc)[:100]}"
            self.examples[tone] = error_msg
            self.after(0, self._update_tone_widget, tone, error_msg)

    def _update_tone_widget(self, tone, content):
        """Update a specific tone widget with the result."""
        if tone not in self.tone_widgets:
            return
        
        widget = self.tone_widgets[tone]
        widget.config(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert("1.0", content)
        widget.config(state=tk.DISABLED)

        # Check if all are done
        if len(self.examples) == len(self.TONES):
            self.status_label.config(text="✅ Έτοιμα! Κάντε κλικ σε ένα τόνο για αντιγραφή", foreground="green")

    def _copy_tone(self, tone):
        """Copy the selected tone to clipboard."""
        if tone not in self.examples:
            messagebox.showwarning("Προσοχή", "Δεν έχει παράδειγμα")
            return
        
        result = self.examples[tone]
        if result.startswith("❌"):
            messagebox.showerror("Σφάλμα", result)
            return
        
        self.clipboard_clear()
        self.clipboard_append(result)
        messagebox.showinfo("Αντιγραφή", "✅ Το παράδειγμα αντιγράφηκε!")



