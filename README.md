# writing-assistant
A local writing assistant that helps you write better messages in real time.

## Features
- Fast local Greeklish -> Greek conversion (no LLM required)
- Second-pass corrections (e.g. final sigma handling)
- Minimal desktop UI with light/dark themes
- Keyboard shortcuts:
  - `Ctrl+L`: focus input
  - `Ctrl+D`: toggle theme
- Optional LangChain/OpenAI actions for:
  - Greek grammar/tone improvement
  - English <-> Greek translation

## Run
```bash
python app.py
```

## Optional LLM setup
Install optional dependencies and set your OpenAI key if you want LLM actions:

```bash
pip install langchain-openai
```

Then set:
- `OPENAI_API_KEY`
- Optional: `OPENAI_MODEL` (default: `gpt-4o-mini`)
