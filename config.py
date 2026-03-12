import json
import os
from pathlib import Path


class ConfigManager:
    """Manage application settings and persistence."""

    CONFIG_DIR = Path.cwd()
    CONFIG_FILE = CONFIG_DIR / "config.json"

    DEFAULT_CONFIG = {
        "theme": "dark",
        "default_tone": "Μόνο διόρθωση γραμματικής και ορθογραφίας",
        "auto_convert": True,
        "auto_tonify": False,
        "llm_endpoint": "http://localhost:1234/v1",
        "llm_model": "llm_model",
        "llm_api_key": "random-api-key",
        "window_width": 1080,
        "window_height": 690,
        "last_language": "English",
        "active_greeklish_profile": "default",
        "greeklish_profiles": {
            "default": {
                "multi": {
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
                },
                "single": {
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
                    "?": ";",
                },
            }
        },
    }

    def __init__(self):
        self.config = self._load_config()
        # Ensure config file is created on first run
        if not self.CONFIG_FILE.exists():
            self.save()

    @property
    def config_dir(self):
        return self.CONFIG_DIR

    def _load_config(self) -> dict:
        """Load config from JSON or return defaults."""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge with defaults to handle missing keys
                    return {**self.DEFAULT_CONFIG, **loaded}
            except Exception:
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()

    def _ensure_default_profile(self):
        """Ensure greeklish_profiles exists in config."""
        if "greeklish_profiles" not in self.config:
            self.config["greeklish_profiles"] = self.DEFAULT_CONFIG["greeklish_profiles"]
            self.save()

    def save(self):
        """Save config to JSON file."""
        try:
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            print(f"Failed to save config: {exc}")

    def get(self, key: str, default=None):
        """Get config value."""
        return self.config.get(key, default)

    def set(self, key: str, value):
        """Set config value and save."""
        self.config[key] = value
        self.save()

    def load_greeklish_profile(self, profile_name: str = "default") -> dict:
        """Load greeklish mapping profile from config."""
        profiles = self.config.get("greeklish_profiles", {})
        if profile_name in profiles:
            return profiles[profile_name]
        return profiles.get("default", {})

    def save_greeklish_profile(self, profile_name: str, mappings: dict):
        """Save greeklish mapping profile to config."""
        if "greeklish_profiles" not in self.config:
            self.config["greeklish_profiles"] = {}
        self.config["greeklish_profiles"][profile_name] = mappings
        self.save()

    def list_greeklish_profiles(self) -> list[str]:
        """List all available greeklish profiles."""
        profiles = self.config.get("greeklish_profiles", {})
        return sorted(profiles.keys()) if profiles else ["default"]

    def delete_greeklish_profile(self, profile_name: str):
        """Delete a greeklish profile from config."""
        if profile_name == "default":
            return  # Prevent deleting default profile
        profiles = self.config.get("greeklish_profiles", {})
        if profile_name in profiles:
            del profiles[profile_name]
            self.save()
