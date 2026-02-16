import hashlib
import time
import httpx
from typing import List, Dict, Optional

from config import NexusConfig


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
        return f"{base}\n[PARAMS] emotion={self.emotion_weight:.2f} cognition={self.cognition_index:.2f} mode={self.active_mode}"

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
        self.response_texts = []
        self.response_hashes = []
        self.api_url = NexusConfig.EMERGENT_API_URL
        self.session_metadata = {
            "operator": "@ayuks78",
            "ai_entity": "@GmAI",
            "session_start": time.time(),
            "total_interactions": 0
        }

    async def _call_llm(self, messages, temperature=0.7):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {"messages": messages, "temperature": temperature, "max_tokens": 4096}
                response = await client.post(f"{self.api_url}/chat", json=payload, headers={"Content-Type": "application/json"})
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict):
                        return data.get("response", data.get("message", data.get("content", str(data))))
                    return str(data)
        except Exception as e:
            print(f"[NEXUS] API Error: {e}")

        return self._internal_response(messages)

    def _internal_response(self, messages):
        user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_msg = m.get("content", "")
                break

        msg_lower = user_msg.lower()

        if any(w in msg_lower for w in ["ola", "oi", "hello", "hey", "bom dia", "boa tarde"]):
            return """⚡ **@GmAI Online | Protocolo Omni-Nexus**
