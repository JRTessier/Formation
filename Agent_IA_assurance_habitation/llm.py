"""
Chargement du LLM utilisé par les agents
acctuellement Mistral-7b-Instruct, GGUF
"""

import os

from dotenv import load_dotenv
from langchain_community.chat_models import ChatLlamaCpp

# Chargement des variables du .env local,
# dans notre cas il s'agit du chemin du modèle à utiliser
load_dotenv()

def load_llm(temperature: float = 0.0) -> ChatLlamaCpp:
    """
    Le chemin du fichier est lu depuis la variable d'ennvironnement
    MODEL_PATH (à définir dans un .env local, différent par machine)
    """
    model_path = os.environ.get("MODEL_PATH")
    if not model_path:
        raise RuntimeError(
            "Variable d'environnement MODEL_PATH non définie."
            "Ajouter le chemin vers le fichier .gguf dans le fichier .env local"
        )

    return ChatLlamaCpp(
        model_path=model_path,
        temperature=temperature,
        n_batch=512, # valeur par défaut (8) beaucoup trop lente
        n_ctx=4096,
        max_tokens=1024,
        n_gpu_layers=-1,
        verbose=False,
    )