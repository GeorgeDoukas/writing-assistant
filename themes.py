THEMES: dict = {
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

TONE_MAPPING: dict = {
    "Μόνο διόρθωση γραμματικής και ορθογραφίας": "correct grammar and spelling only, no tone changes",
    "Επαγγελματικός αλλά φιλικός": "professional but friendly",
    "Επίσημος": "formal",
    "Χαλαρός": "casual",
    "Ακαδημαϊκός": "academic",
    "Πειστικός": "persuasive",
}

TONE_LABELS: list[str] = list(TONE_MAPPING.keys())
