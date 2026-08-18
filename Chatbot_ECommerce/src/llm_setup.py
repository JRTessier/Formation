from pathlib import Path
from langchain_community.chat_models import ChatLlamaCpp
from huggingface_hub import hf_hub_download

MODEL_REPO = "bartowski/Mistral-7B-Instruct-v0.3-GGUF"
MODEL_FILENAME = "Mistral-7B-Instruct-v0.3-Q4_K_M.gguf"
MODEL_DIR = Path(__file__).parent.parent / "models"

def build_llm(temperature: float = 0.0) -> ChatLlamaCpp:
    model_path = MODEL_DIR / MODEL_FILENAME
    if not model_path.exists():
        print("Téléchargemenr du modèle...")
        hf_hub_download(repo_id=MODEL_REPO, filename=MODEL_FILENAME, local_dir=str(MODEL_DIR))

    return ChatLlamaCpp(
        model_path=str(model_path),
        n_ctx=4096,
        n_batch=512,
        n_gpu_layers=1,
        temperature=temperature, # temperature 0 car besoin d'un comportement déterministe, pas de créativité
        verbose=False
    )