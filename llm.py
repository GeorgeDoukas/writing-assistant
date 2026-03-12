import json
import os
import urllib.error
import urllib.request


class LLMAssistant:
    def __init__(self):
        self.OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:1234/v1")
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "llm_model")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "random-api-key")

    def _invoke(self, system_prompt: str, user_text: str, max_tokens: int | None = None) -> str:
        body: dict = {
            "model": self.OPENAI_MODEL,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
        }
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        payload = json.dumps(body).encode()
        req = urllib.request.Request(
            f"{self.OPENAI_BASE_URL.rstrip('/')}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.OPENAI_API_KEY}",
            },
        )
        print(f"Invoking LLM at {self.OPENAI_BASE_URL} with model {self.OPENAI_MODEL}...")
        print(f"System Prompt:\n{system_prompt}\n")
        print(f"User Text:\n{user_text}\n")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Cannot reach LLM endpoint ({self.OPENAI_BASE_URL}).\n"
                "Make sure LM Studio is running and a model is loaded, or set "
                "OPENAI_BASE_URL / OPENAI_API_KEY / OPENAI_MODEL."
            ) from exc
        print(f"LLM Response:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n")
        return data["choices"][0]["message"]["content"].strip()

    def check_connection(self) -> None:
        """Minimal ping — expects the single word 'true' in response."""
        self._invoke("Reply with only the word: true. No reasoning, no explanation.", "Are you online?")

    def improve_greek(self, text: str, tone: str) -> str:
        return self._invoke(
            f"You are a professional Greek text editor. "
            f"Fix grammar, syntax, and clarity while strictly preserving the original meaning. "
            f"Apply a '{tone}' tone throughout. "
            f"Return ONLY the corrected Greek text — no explanations, no markdown, no introductory phrases.",
            text,
        )

    def improve_tone_grammar_orthography(self, text: str, tone: str) -> str:
        if "grammar" in tone.lower() and "only" in tone.lower():
            return self._invoke(
                "You are a professional Greek text editor and orthography specialist. "
                "1. Fix ONLY grammar, syntax, and clarity while strictly preserving the original meaning and tone. "
                "2. DO NOT change the writing tone or style. "
                "3. Add correct accent marks (tonifies) to every word that requires one, following the modern monotonic system. "
                "Return ONLY the improved Greek text — no explanations, no markdown, no introductory phrases.",
                text,
            )
        return self._invoke(
            f"You are a professional Greek text editor and orthography specialist. "
            f"1. Fix grammar, syntax, and clarity while strictly preserving the original meaning. "
            f"2. Apply a '{tone}' tone throughout. "
            f"3. Add correct accent marks (tonifies) to every word that requires one, following the modern monotonic system. "
            f"Return ONLY the improved Greek text — no explanations, no markdown, no introductory phrases.",
            text,
        )

    def tonify(self, text: str) -> str:
        return self._invoke(
            "You are a Greek orthography specialist. "
            "Add the correct accent marks to every word that requires one, "
            "following the modern monotonic system. "
            "Do NOT change any word, word order, or punctuation — only add or correct accents. "
            "Return ONLY the accented text — no explanations, no markdown.",
            text,
        )

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        return self._invoke(
            f"You are a professional translator. "
            f"Translate the following text from {source_lang} to {target_lang}. "
            f"Preserve the style, tone, and structure of the original as closely as possible. "
            f"Return ONLY the translation — no explanations, no markdown, no introductory phrases.",
            text,
        )
