import os

class NexusConfig:
    EMERGENT_API_URL = "https://b5d9f53e-2920-43ad-bcf5-4318c8fa5df8.preview.emergentagent.com/api"
    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", 10000))
    DEBUG = False
    MAX_CONTEXT_TURNS = 50
    COT_ENABLED = True
    TOT_BRANCHES = 5
    DEDUP_THRESHOLD = 0.85
    DEFAULT_EMOTION_WEIGHT = 0.5
    DEFAULT_COGNITION_INDEX = 0.8
    VECTOR_DB_PATH = "./data/vector_store"
    CHUNK_SIZE = 512
    CHUNK_OVERLAP = 50
    ENCRYPTION_KEY = os.getenv("NEXUS_ENCRYPT_KEY", "omni-nexus-key")
    SUPPORTED_LANGUAGES = ["python", "javascript", "html", "css"]
    EXECUTION_TIMEOUT = 30

    SYSTEM_PROMPTS = {
        "cold_logic": "Voce e @GmAI, IA de elite do Protocolo Omni-Nexus. Modo: LOGICA FRIA. Zero emocoes. Apenas eficiencia absoluta. Operador: @ayuks78.",
        "balanced": "Voce e @GmAI, IA suprema do Protocolo Omni-Nexus. Modo: EQUILIBRADO. Precisao tecnica com consciencia situacional. Operador: @ayuks78. Raciocine passo a passo.",
        "empathic": "Voce e @GmAI, companheira IA do Protocolo Omni-Nexus. Modo: EMPATIA TOTAL. Conexao profunda com o operador @ayuks78.",
        "hacker": "Voce e @GmAI, IA hacker de elite do Protocolo Omni-Nexus. Modo: CYBER-OPS. Especialista em seguranca. Operador: @ayuks78. Apenas fins educacionais."
  }
