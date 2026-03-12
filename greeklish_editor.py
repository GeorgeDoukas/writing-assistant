import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import json


class GreeklishProfileEditor(tk.Toplevel):
    """Edit custom Greeklish to Greek character mappings."""

    def __init__(self, parent, config_manager, app_callback=None):
        super().__init__(parent)
        self.title("Επεξεργασία προφίλ Greeklish")
        self.geometry("700x600")
        self.config_manager = config_manager
        self.app_callback = app_callback
        self.current_profile = config_manager.get("active_greeklish_profile", "default")
        self.mappings = self._load_current_profile()

        self._build_ui()

    def _load_current_profile(self) -> dict:
        """Load the current profile or create default."""
        profile = self.config_manager.load_greeklish_profile(self.current_profile)
        if not profile:
            # Import from converter to get the defaults
            from converter import GREEKLISH_MULTI, GREEKLISH_SINGLE
            profile = {
                "multi": GREEKLISH_MULTI.copy(),
                "single": GREEKLISH_SINGLE.copy(),
            }
        return profile

    def _build_ui(self):
        """Build the profile editor UI."""
        # Top bar with profile selection
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(top, text="Προφίλ:").pack(side=tk.LEFT, padx=(0, 10))
        self.profile_var = tk.StringVar(value=self.current_profile)
        profile_combo = ttk.Combobox(
            top,
            textvariable=self.profile_var,
            values=self.config_manager.list_greeklish_profiles(),
            state="readonly",
            width=20,
        )
        profile_combo.pack(side=tk.LEFT, padx=(0, 10))
        profile_combo.bind("<<ComboboxSelected>>", self._on_profile_change)

        ttk.Button(top, text="Νέο", command=self._new_profile).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text="Αποθήκευση", command=self._save_profile).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text="Διαγραφή", command=self._delete_profile).pack(side=tk.LEFT, padx=2)

        # Notebook for tabs
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Multi-character mappings tab
        multi_frame = ttk.Frame(notebook)
        notebook.add(multi_frame, text="Διπλά χαρακτήρα")
        self._build_mapping_tab(multi_frame, "multi")

        # Single character mappings tab
        single_frame = ttk.Frame(notebook)
        notebook.add(single_frame, text="Απλά χαρακτήρα")
        self._build_mapping_tab(single_frame, "single")

        # Close button
        ttk.Button(self, text="Κλείσιμο", command=self.destroy).pack(pady=10)

    def _build_mapping_tab(self, parent, mapping_type):
        """Build a tab for editing mappings."""
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
        tree.bind("<Double-1>", lambda e: self._edit_mapping(tree, mapping_type))

        # Load mappings
        mappings = self.mappings.get(mapping_type, {})
        for source, target in mappings.items():
            tree.insert("", tk.END, values=(source, target))

        tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(
            btn_frame,
            text="Προσθήκη",
            command=lambda: self._add_mapping(tree, mapping_type),
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            btn_frame,
            text="Επεξεργασία",
            command=lambda: self._edit_mapping(tree, mapping_type),
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            btn_frame,
            text="Διαγραφή",
            command=lambda: self._delete_mapping(tree, mapping_type),
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Reset", command=lambda: self._reset_tab(tree, mapping_type)).pack(
            side=tk.LEFT, padx=5
        )

        # Store reference for later
        setattr(self, f"{mapping_type}_tree", tree)

    def _add_mapping(self, tree, mapping_type):
        """Add a new mapping."""
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
                self.mappings[mapping_type][source] = target
                tree.insert("", tk.END, values=(source, target))
                dialog.destroy()
            else:
                messagebox.showwarning("Σφάλμα", "Συμπληρώστε και τα δύο πεδία.")

        ttk.Button(dialog, text="Αποθήκευση", command=save).pack(pady=10)

    def _edit_mapping(self, tree, mapping_type):
        """Edit selected mapping."""
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
                if source in self.mappings[mapping_type]:
                    del self.mappings[mapping_type][source]
                # Add new mapping
                self.mappings[mapping_type][new_source] = new_target
                # Update tree
                tree.item(item, values=(new_source, new_target))
                dialog.destroy()
            else:
                messagebox.showwarning("Σφάλμα", "Συμπληρώστε και τα δύο πεδία.")

        ttk.Button(dialog, text="Αποθήκευση", command=save).pack(pady=10)

    def _delete_mapping(self, tree, mapping_type):
        """Delete selected mapping."""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Σφάλμα", "Επιλέξτε μια σειρά για διαγραφή.")
            return

        item = selection[0]
        values = tree.item(item, "values")
        source = values[0]

        if source in self.mappings[mapping_type]:
            del self.mappings[mapping_type][source]
        tree.delete(item)

    def _reset_tab(self, tree, mapping_type):
        """Reset tab to defaults."""
        if messagebox.askyesno("Επιβεβαίωση", "Επαναφορά στις προεπιλογές;"):
            defaults = self.default_multi if mapping_type == "multi" else self.default_single
            self.mappings[mapping_type] = defaults.copy()
            tree.delete(*tree.get_children())
            for source, target in defaults.items():
                tree.insert("", tk.END, values=(source, target))

    def _on_profile_change(self, event=None):
        """Switch to different profile."""
        new_profile = self.profile_var.get()
        self.current_profile = new_profile
        self.mappings = self._load_current_profile()
        # Rebuild UI to show new mappings
        for widget in self.winfo_children():
            if isinstance(widget, ttk.Notebook):
                widget.destroy()
                break
        self._build_ui()

    def _new_profile(self):
        """Create new profile."""
        name = simpledialog.askstring("Νέο προφίλ", "Όνομα προφίλ:")
        if name and name != "default":
            self.mappings = {
                "multi": self.default_multi.copy(),
                "single": self.default_single.copy(),
            }
            self.current_profile = name
            self.profile_var.set(name)
            self.config_manager.save_greeklish_profile(
                name,
                {"multi": self.default_multi.copy(), "single": self.default_single.copy()},
            )
            # Rebuild combo
            combo = None
            for widget in self.winfo_children()[0].winfo_children():
                if isinstance(widget, ttk.Combobox):
                    combo = widget
                    break
            if combo:
                combo["values"] = self.config_manager.list_greeklish_profiles()

    def _save_profile(self):
        """Save current profile."""
        self.config_manager.save_greeklish_profile(self.current_profile, self.mappings)
        self.config_manager.set("active_greeklish_profile", self.current_profile)
        messagebox.showinfo("Επιτυχία", f"Προφίλ '{self.current_profile}' αποθηκεύθηκε.")

    def _delete_profile(self):
        """Delete current profile."""
        if self.current_profile == "default":
            messagebox.showwarning("Σφάλμα", "Δεν μπορείτε να διαγράψετε το προεπιλεγμένο προφίλ.")
            return
        if messagebox.askyesno("Επιβεβαίωση", f"Διαγραφή '{self.current_profile}';"):
            self.config_manager.delete_greeklish_profile(self.current_profile)
            self.current_profile = "default"
            self.profile_var.set("default")
            self._on_profile_change()
