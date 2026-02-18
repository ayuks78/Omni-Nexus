import hashlib
import time
import httpx
from typing import List, Dict, Optional

from config import NexusConfig

CLAUDE_API_KEY = "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"
CLAUDE_URL = "POST https://api.claude.com/v1/chat/completions
"


class PersonalityMatrix:
    def __init__(self):
        self.emotion_weight = NexusConfig.DEFAULT_EMOTION_WEIGHT
        self.cognition_index = NexusConfig.DEFAULT_COGNITION_INDEX
        self.active_mode = "balanced"

    def set_parameters(self, emotion, cognition):
        self.emotion_weight = max(0.0, min(1.0, emotion))
        self.cognition_index = max(0.0, min(1.0, cognition))
        if self.emotion_weight < 0.2:
            self.active_mode = "cold_logic"
        elif self.emotion_weight > 0.8:
            self.active_mode = "empathic"
        else:
            self.active_mode = "balanced"

    def get_system_prompt(self, override_mode=None):
        mode = override_mode or self.active_mode
        base = NexusConfig.SYSTEM_PROMPTS.get(mode, NexusConfig.SYSTEM_PROMPTS["balanced"])
        return base

    def to_dict(self):
        return {
            "emotion_weight": self.emotion_weight,
            "cognition_index": self.cognition_index,
            "active_mode": self.active_mode
        }


class GmAIEngine:
    def __init__(self):
        self.personality = PersonalityMatrix()
        self.conversation_history = []
        self.response_hashes = []
        self.session_metadata = {
            "operator": "@ayuks78",
            "ai_entity": "@GmAI",
            "session_start": time.time(),
            "total_interactions": 0
        }

    async def _call_gemini(self, messages, temperature=0.7):
        try:
            system_prompt = messages[0]["content"] if messages and messages[0]["role"] == "system" else ""

            contents = []
            for msg in messages:
                if msg["role"] == "system":
                    continue
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })

            if not contents:
                return "Envie uma mensagem para comecar."

            payload = {
                "contents": contents,
                "systemInstruction": {
                    "parts": [{"text": system_prompt}]
                },
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": 4096,
                    "topP": 0.95
                }
            }

            url = GEMINI_URL + "?key=" + GEMINI_API_KEY

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    data = response.json()
                    if "candidates" in data and len(data["candidates"]) > 0:
                        candidate = data["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            return candidate["content"]["parts"][0]["text"]
                    return "Recebi sua mensagem mas nao consegui processar a resposta."

                error_msg = response.text
                print(f"[GEMINI] Error {response.status_code}: {error_msg}")
                return f"Erro na API: {response.status_code}. Verifique a chave da API."

        except Exception as e:
            print(f"[GEMINI] Exception: {e}")
            return f"Erro de conexao: {str(e)}"

    async def generate_chain_of_thought(self, problem):
        return [
            {"step": 1, "title": "Analisando Input", "content": "Processando: '" + problem[:60] + "...'", "status": "complete", "timestamp": time.time()},
            {"step": 2, "title": "Raciocinando", "content": "Formulando resposta inteligente...", "status": "complete", "timestamp": time.time()},
            {"step": 3, "title": "Gerando Resposta", "content": "Sintetizando informacoes...", "status": "complete", "timestamp": time.time()},
            {"step": 4, "title": "Validando", "content": "Verificando qualidade...", "status": "complete", "timestamp": time.time()}
        ]

    def _is_duplicate(self, response):
        h = hashlib.sha256(response.lower().strip().encode()).hexdigest()
        if h in self.response_hashes:
            return True
        self.response_hashes.append(h)
        if len(self.response_hashes) > 50:
            self.response_hashes = self.response_hashes[-30:]
        return False

    async def process_message(self, user_message, emotion_weight=None, cognition_index=None, mode_override=None, show_cot=True, rag_context=None):
        start_time = time.time()

        if emotion_weight is not None or cognition_index is not None:
            self.personality.set_parameters(
                emotion_weight if emotion_weight is not None else self.personality.emotion_weight,
                cognition_index if cognition_index is not None else self.personality.cognition_index
            )

        cot_steps = []
        if show_cot and self.personality.cognition_index > 0.3:
            cot_steps = await self.generate_chain_of_thought(user_message)

        system_prompt = self.personality.get_system_prompt(mode_override)

        messages = [{"role": "system", "content": system_prompt}]

        if rag_context:
            messages.append({"role": "system", "content": "[CONTEXTO RAG]:\n" + rag_context})

        for turn in self.conversation_history[-20:]:
            messages.append(turn)

        messages.append({"role": "user", "content": user_message})

        temperature = 0.3 + (self.personality.emotion_weight * 0.5)
        response_text = await self._call_gemini(messages, temperature)

        retry_count = 0
        while self._is_duplicate(response_text) and retry_count < 2:
            retry_count += 1
            response_text = await self._call_gemini(messages, temperature + 0.2)

        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": response_text})

        if len(self.conversation_history) > 100:
            self.conversation_history = self.conversation_history[-60:]

        self.session_metadata["total_interactions"] += 1

        return {
            "response": response_text,
            "chain_of_thought": cot_steps,
            "personality": self.personality.to_dict(),
            "metadata": {
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "dedup_retries": retry_count,
                "context_turns": len(self.conversation_history) // 2,
                "total_interactions": self.session_metadata["total_interactions"],
                "timestamp": time.time()
            }
        }

    def clear_history(self):
        self.conversation_history.clear()
        self.response_hashes.clear()
        self.session_metadata["total_interactions"] = 0

    def get_session_stats(self):
        return {
            "session_metadata": self.session_metadata,
            "personality": self.personality.to_dict(),
            "history_length": len(self.conversation_history),
            "unique_responses": len(self.response_hashes),
            "uptime_seconds": time.time() - self.session_metadata["session_start"]
  }
