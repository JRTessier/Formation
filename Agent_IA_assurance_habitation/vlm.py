import base64
import os

from dotenv import load_dotenv
from llama_cpp import Llama
from llama_cpp.llama_chat_format import Llava15ChatHandler

load_dotenv()

_MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}

"""
PIPELINE :

image brute (pixels)
    │
    │  base64.b64encode()  <-  fait ici dans _image_vers_data_uri()
    ▼
string Base64 (data_uri)
    │
    │  transmise dans le message au modèle vlm par _image_vers_data_uri()
    ▼
chat handler reçoit la string Base64
    │
    │  décodage Base64  ->  image brute (fait automatiquement par le mmproj)
    ▼
image brute (pixels), reconstituée
    │
    │  encodeur CLIP (via mmproj)  ->  vecteurs (fait automatiquement par le mmproj)
    ▼
vecteurs numériques (compréhensibles par LLaVA)
"""

# Chargement des variables du .env local,
# dans notre cas il s'agit du chemin du modèle VLM et de l'encodeur à utiliser
def load_vlm(temperature: float = 0.0) -> Llama:
    """Chargement du modèle VLM et de l'encoder CLIP MMPROJ"""
    model_path = os.environ.get("VLM_MODEL_PATH")
    mmproj_path = os.environ.get("MMPROJ_PATH")

    if not model_path or not mmproj_path:
        raise RuntimeError(
            "Variable d'environnement VLM_MODEL_PATH et/ou MMPROJ_PATH non définis."
            "Ajouter le chemin vers le fichier .gguf dans le fichier .env local"
        )

    chat_handler = Llava15ChatHandler(clip_model_path=mmproj_path)

    return Llama(
        model_path=model_path,
        chat_handler=chat_handler, # permet de traduire l'image pour le modele cible
        n_ctx=4096, # doit être suffisant pour une image qui occupe beaucoup de tokens
        n_gpu_layers=-1, # tous les layers sur GPU
        temperature=temperature,
        #repeat_penalty=1.3, # évite les répétitions dues à des boucles de génération dégénérée
        verbose=False,
    )

# Traitement de l'image
def _image_vers_data_uri(chemin_image: str) -> str:
    """Transforme l'image reçu au format string Base64 (Uniform Resource Identifier)"""
    extension = os.path.splitext(chemin_image)[1].lower()
    mime_type = _MIME_TYPES.get(extension)
    if mime_type is None:
        raise ValueError(f"Format de fichier non supportée : {extension!r}")

    with open(chemin_image, "rb") as fichier:
        donnees_b64 = base64.b64encode(fichier.read()).decode("utf-8")

    return f"data: {mime_type};base64,{donnees_b64}"

def analyser_image(llm: Llama, chemin_image: str, query: str) -> str:
    """envoie une image base 64 + une question au VLM et reçoit une réponse texte en retour"""
    data_uri = _image_vers_data_uri(chemin_image)

    reponse = llm.create_chat_completion(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": query},
                    {"type": "image_url", "image_url": {"url": data_uri}},
                ],
            }
        ]
    )
    max_tokens=300, # On limite la longueur de la réponse, pas besoin d'écrire un roman et évite les défauts de répétitions
    return reponse["choices"][0]["message"]["content"] # format dictionnaire hérité du standard API OpenAI


# TEST
if __name__ == "__main__":
    llm = load_vlm()

    chemin_test = "/Users/JR/Desktop/Blent/Projets/Agent_IA_assurance_habitation/data/exemples_pj/NaturalDamage_432.jpg"
    reponse = analyser_image(llm, chemin_test, "Décrit l'image suivante en une seule phrase.")
    print(reponse)


def analyser_image_complet(llm: Llama, chemin_image: str, question: str) -> dict:
    """Comme analyser_image(), mais retourne la réponse complète de
    create_chat_completion (utile pour diagnostiquer via finish_reason,
    usage, etc.) plutôt que juste le texte extrait."""
    data_uri = _image_vers_data_uri(chemin_image)

    return llm.create_chat_completion(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_uri}},
                    {"type": "text", "text": question},
                ],
            }
        ],
        max_tokens=300,
    )