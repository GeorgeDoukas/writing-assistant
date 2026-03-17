# writing-assistant
A lightweight desktop writing assistant for Greek text that combines fast local Greeklish conversion with optional LLM-powered improvements.

## Key Advantage: No External Dependencies Required

The core functionality works **completely offline with zero external packages** — just Python's built-in `tkinter`. Add LLM features (grammar improvement, translation) if you need them.

## Features

### Core Conversion (No Dependencies)
- **Greeklish → Greek**: Instant local conversion
  - Supports multi-character patterns (e.g., `ps` → `ψ`, `ou` → `ου`)
  - Second-pass corrections (final sigma handling: σ→ς)
  - Backtick passthrough to preserve text (`` `word` `` stays as-is)
- **Customizable Greeklish Profiles**: Create and edit your own conversion rules
- **Auto-Convert Toggle**: Automatically convert Greeklish as you type

### Optional LLM-Powered Features
Enhance your writing with AI (requires LLM setup):

- **Grammar & Tone Improvement**: Six styles available:
  - Grammar & spelling only (Μόνο διόρθωση γραμματικής και ορθογραφίας)
  - Professional but friendly (Επαγγελματικός αλλά φιλικός)
  - Formal (Επίσημος)
  - Casual (Χαλαρός)
  - Academic (Ακαδημαϊκός)
  - Persuasive (Πειστικός)
- **Auto-Improve**: Automatically improve text every 5 seconds (toggle in top bar)
- **Translation**: Translate to 11+ languages (English, French, German, Spanish, Italian, Portuguese, Dutch, Swedish, Japanese, Chinese, Russian)

### UI & Usability
- **Light/Dark Themes**: Toggle with `Ctrl+D`
- **Customizable Settings**: Configure LLM endpoint, model, and defaults
- **Tone Examples**: View real-world examples of each tone/style
- **Auto Window Switch**: Copy output and automatically switch to the previous window (OS-aware)

### Keyboard Shortcuts
| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` | Convert Greeklish to Greek |
| `Ctrl+I` | Improve text with LLM |
| `Ctrl+L` | Clear input |
| `Ctrl+Shift+C` | Copy output & auto-switch window (if enabled) |
| `Ctrl+D` | Toggle light/dark theme |

### Top Bar Toggles
- **Αυτόματη μετατροπή** (Auto-Convert): Convert Greeklish as you type
- **Αυτόματη Βελτίωση** (Auto-Improve): Improve Greek text every 5 seconds
- **Εναλλαγή παραθύρου** (Auto Window Switch): Auto-switch to previous window on copy

## Setup

### Installation (No External Packages Required for Core)
```bash
git clone <repo>
cd writing-assistant
python app.py
```

That's it! The Greeklish converter runs with just Python's built-in libraries.

### (Optional) LLM Features Setup
To use grammar improvement and translation features, you'll need to configure an LLM endpoint:

1. Clone and run the app as above
2. Click **Ρυθμίσεις** (Settings) button
3. Set **LLM Endpoint** (default: `http://localhost:1234/v1`)
4. Set **LLM Model** (e.g., `neural-chat`, `mistral`, etc.)
5. Click **Δοκιμάστε σύνδεση** (Test Connection)

**Quick Option**: Use [LM Studio](https://lmstudio.ai/) for local LLM inference (no internet required)

### (Optional) Virtual Environment Setup
For isolated Python environments:
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On macOS/Linux
python app.py
```

### Configuration
Edit `config.json` to customize settings:
- **Theme**: "dark" or "light"
- **Default Tone**: Default improvement style (for LLM features)
- **LLM Endpoint**: OpenAI-compatible API endpoint
- **LLM Model**: Name of the model to use
- **Greeklish Profile**: Custom Greeklish → Greek conversion rules
- **Auto toggles**: Enable/disable auto-convert, auto-improve, auto-switch

Copy `config.example.json` to `config.json` to get started.
