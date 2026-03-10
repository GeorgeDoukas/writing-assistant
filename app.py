import os
import re
import tkinter as tk
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


class LLMAssistant:
    def __init__(self) -> None:
        self._llm = None

    def _get_llm(self):
        if self._llm:
            return self._llm
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        try:
            from langchain_openai import ChatOpenAI
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("Install langchain-openai to enable LLM features.") from exc
        self._llm = ChatOpenAI(model=model_name, temperature=0.2)
        return self._llm

    def _invoke(self, system_prompt: str, user_text: str) -> str:
        llm = self._get_llm()
        response = llm.invoke(
            [
                ("system", system_prompt),
                ("human", user_text),
            ]
        )
        return response.content.strip()

    def improve_greek(self, text: str, tone: str) -> str:
        return self._invoke(
            f"Improve grammar and clarity in Greek. Keep meaning and output only Greek text with {tone} tone.",
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
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Writing Assistant")
        self.root.geometry("1000x680")
        self.theme_name = "dark"
        self.llm = LLMAssistant()
        self.auto_convert_var = tk.BooleanVar(value=True)

        self.tone_var = tk.StringVar(value="professional but friendly")
        self.style = ttk.Style()
        self._build_ui()
        self._apply_theme()
        self.root.bind("<Control-l>", lambda _e: self.input_text.focus_set())
        self.root.bind("<Control-d>", lambda _e: self.toggle_theme())
        self.root.bind("<Control-Return>", lambda _e: self.convert_text())

    def _build_ui(self):
        self.container = ttk.Frame(self.root, padding=14)
        self.container.pack(fill=tk.BOTH, expand=True)

        top = ttk.Frame(self.container)
        top.pack(fill=tk.X)

        title = ttk.Label(top, text="Greek Writing Assistant", font=("Segoe UI", 14, "bold"))
        title.pack(side=tk.LEFT)

        ttk.Checkbutton(top, text="Auto convert", variable=self.auto_convert_var).pack(side=tk.LEFT, padx=10)
        ttk.Button(top, text="Toggle Theme (Ctrl+D)", command=self.toggle_theme).pack(side=tk.RIGHT)

        panes = ttk.Panedwindow(self.container, orient=tk.HORIZONTAL)
        panes.pack(fill=tk.BOTH, expand=True, pady=(12, 8))

        left = ttk.Frame(panes, padding=8)
        right = ttk.Frame(panes, padding=8)
        panes.add(left, weight=1)
        panes.add(right, weight=1)

        ttk.Label(left, text="Greeklish Input").pack(anchor="w")
        self.input_text = tk.Text(left, wrap=tk.WORD, height=24, undo=True)
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        ttk.Label(right, text="Greek Output").pack(anchor="w")
        self.output_text = tk.Text(right, wrap=tk.WORD, height=24, undo=True)
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

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
        )
        tone_combo.pack(side=tk.LEFT, padx=(4, 0))

        ttk.Button(actions, text="LLM: Improve Tone", command=self.improve_with_llm).pack(side=tk.LEFT, padx=8)
        ttk.Button(actions, text="Translate EN → EL", command=self.translate_en_el).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Translate EL → EN", command=self.translate_el_en).pack(side=tk.LEFT, padx=4)
        ttk.Label(
            actions,
            text="Ctrl+L: focus  |  Ctrl+D: theme",
            font=("Segoe UI", 9),
        ).pack(side=tk.RIGHT)

        self.input_text.bind("<KeyRelease>", self._on_input_change)

    def _apply_theme(self):
        theme = THEMES[self.theme_name]
        self.root.configure(bg=theme["bg"])
        self.style.configure("TFrame", background=theme["bg"])
        self.style.configure("TLabel", background=theme["bg"], foreground=theme["fg"])
        self.style.configure("TButton", background=theme["card"], foreground=theme["fg"])
        self.style.configure("TCheckbutton", background=theme["bg"], foreground=theme["fg"])
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

    def _on_input_change(self, _event=None):
        if self.auto_convert_var.get():
            self.convert_text()

    def convert_text(self):
        source = self.input_text.get("1.0", tk.END).rstrip("\n")
        converted = greeklish_to_greek(source)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", converted)

    def _llm_action(self, action):
        try:
            result = action()
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", result)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(
                "LLM unavailable",
                f"{exc}\n\nSet OPENAI_API_KEY and install langchain-openai to use this action.",
            )

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
