# writing-assistant
A desktop writing assistant for Greek text that combines fast local Greeklish conversion with optional LLM-powered improvements.

## Features

### Text Conversion
- **Greeklish → Greek**: Fast local conversion (no LLM required)
  - Supports multi-character patterns (e.g., `ps` → `ψ`, `ou` → `ου`)
  - Second-pass corrections (e.g., final sigma handling)
  - Backtick passthrough for preserving text (`word` stays as-is)
- **Customizable Greeklish Profiles**: Create and edit your own conversion rules
- **Auto-Convert Toggle**: Automatically convert text as you type

### LLM-Powered Features
- **Grammar & Tone Improvement**: Enhance text with different styles:
  - Grammar & spelling only (Μόνο διόρθωση γραμματικής και ορθογραφίας)
  - Professional but friendly (Επαγγελματικός αλλά φιλικός)
  - Formal (Επίσημος)
  - Casual (Χαλαρός)
  - Academic (Ακαδημαϊκός)
  - Persuasive (Πειστικός)
- **Auto-Tonify**: Automatically improve text every 5 seconds (toggle in top bar)
- **Translation**: Translate to 11+ languages (English, French, German, Spanish, Italian, Portuguese, Dutch, Swedish, Japanese, Chinese, Russian)

### UI & UX
- **Light/Dark Themes**: Toggle with `Ctrl+D`
- **Customizable Settings**: Configure LLM endpoint, model, and defaults
- **Tone Examples**: View real-world examples of each tone/style
- **Auto Window Switch**: Copy output and automatically switch to the previous window (OS-aware)

### Keyboard Shortcuts
| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` | Convert text |
| `Ctrl+I` | Improve text with LLM |
| `Ctrl+L` | Clear input |
| `Ctrl+Shift+C` | Copy output & auto-switch window (if enabled) |
| `Ctrl+D` | Toggle light/dark theme |

### Toggles (Top Bar)
- **Αυτόματη μετατροπή** (Auto-Convert): Automatically convert Greeklish as you type
- **Αυτόματη Βελτίωση** (Auto-Tonify): Improve Greek text every 5 seconds
- **Εναλλαγή παραθύρου** (Auto Window Switch): Auto-switch to previous window on copy

## Setup

### Installation
```bash
git clone <repo>
cd writing-assistant
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration
Copy the example config to create your local settings:
```bash
cp config.example.json config.json
```

Edit `config.json` to customize:
- **LLM Endpoint & Model**: For LLM features (improvement, translation)
- **Theme**: "dark" or "light"
- **Default Tone**: Default improvement style
- **Greeklish Profile**: Custom Greeklish → Greek conversion rules
- **Auto toggles**: Enable/disable auto-convert, auto-tonify, auto-switch

### Running the App
```bash
python app.py
```

### LLM Configuration
To use LLM features (grammar improvement, translation), configure your LLM endpoint:

1. Click **Ρυθμίσεις** (Settings) button
2. Set **LLM Endpoint** (default: `http://localhost:1234/v1`)
3. Set **LLM Model** (e.g., `neural-chat`, `mistral`, etc.)
4. Click **Δοκιμάστε σύνδεση** (Test Connection)

**Recommended**: Use [LM Studio](https://lmstudio.ai/) for local LLM inference (no internet required)

### Settings
- **Theme**: Choose dark or light mode
- **Default Tone**: Set your preferred tone for improvements
- **LLM Endpoint**: OpenAI-compatible API endpoint
- **LLM Model**: Name of the model to use
