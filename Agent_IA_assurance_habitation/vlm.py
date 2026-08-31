"""
Chargement du VLM utilisé par les agents Validation et Expertise
ATTENTION : architecture tranforsmoers + bitsandbytes qui nécessite CUDA
"""
import torch

from PIL import Image
from transformers import MllamaForConditionalGeneration, AutoProcessor

MODEL_ID = "unsloth/Llama-3.2-11B-Vision-Instruct-bnb-4bit"

# Chargement
def load_vlm() -> dict:
    """Charge le modèle et le processeur associé."""

    model = MllamaForConditionalGeneration.from_pretrained(MODEL_ID, device_map="cuda")
    processor = AutoProcessor.from_pretrained(MODEL_ID)

    return {"model": model, "processor": processor}

#
def analyser_image(vlm: dict, chemin_image: str, query: str) -> str:
    """Envoie une image + une question au VLM et reçoit une réponse texte en retour"""
    model = vlm["model"]
    processor = vlm["processor"]

    image = Image.open(chemin_image)

    messages=[
        {"role": "user", "content": [
            {"type": "text", "text": query},
            {"type": "image"},
        ],}
    ]
    input_text = processor.apply_chat_template(messages, add_generation_prompt=True)

    inputs = processor(
        image,
        input_text,
        add_special_tokens=False,
        return_tensors="pt",
    ).to(model.device)

    output = model.generate(
        **inputs,
        max_new_tokens=300,
        temperature=0.1,
        top_k=50,
        top_p=0.9,
    )

    nb_tokens_prompt = inputs["input_ids"].shape[-1] # récupère la longueur exacte du prompt en tokens AVANT génération
    reponse = processor.decode(output[0][nb_tokens_prompt:], skip_special_tokens=True) # on récupère ce qui est après

    return reponse.strip()


# TEST
"""if __name__ == "__main__":
    vlm = load_vlm()

    chemin_test = "/workspace/Formation/Agent_IA_assurance_habitation/data/exemples_pj/FireDamage_31.jpg"  # à adapter dans le sandbox
    reponse = analyser_image(vlm, chemin_test, "Décris cette image en une phrase.")
    print(reponse)"""