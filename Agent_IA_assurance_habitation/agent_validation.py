"""..."""

import json
import re

from datetime import date
from langchain_core.messages import HumanMessage
from agent_declaration import DEFINITIONS_SINISTRE
from vlm import analyser_image

# Définitions des garanties par type de sinistre
GARANTIES: dict[str, dict] = {
    "degat_des_eaux": {
        "plafond": 25000,
        "franchise": 150,
        "delai_declaration": 5,
    },
    "incendie": {
        "plafond": 100000,
        "franchise": 300,
        "delai_declaration": 5,
    },
    "vol": {
        "plafond": 20000,
        "franchise": 200,
        "delai_declaration": 2,
    },
}


# --- VALIDITE DU DELAI DE DECLARATION ---
# Extraction de la date réelle du sinistre
PROMPT_EXTRACTION_DATE = """
Tu es un agent IA qui extrait la date exacte d'un sinistre à partir du message d'un assuré dans le cadre d'une déclaration de sinistre auprès d'une assurance habitation.

Aujourd'hui nous sommes le {date_reference}.

- Si le message ne donnes aucune indication temporelle exploitable, réponds null.
- La date doit être au format ISO (année-mois-jour), par exmple 2026-08-20 pour le 20 août 2026. Si même à l'aide de la date d'aujourd'hui tu ne peux pas déterminer la date du sinistre, répond null à la place.
- Réponds UNIQUEMENT avec un objet JSON valide, sans aucun texte autour, avec une seule clé "date_sinistre".

## Exemple

### Entrée

Aujourd'hui : 2026-08-20
Message : "Bonjour,

Il y a eu une fuite dans ma cuisine hier soir à cause de mon voisin du dessus. Son lave-vaisselle a été mal installé et du coup, le mur est infiltré d'eau et la peinture se détache (ci-joint une photo).

Cordialement.

[Pièce jointe : IMG_4580.jpg]"

### Sortie

Réponse : {{"date_sinistre": "2026-08-19"}}


## Exemple

### Entrée

Aujourd'hui : 2026-08-20
Message : "Bonjour, on m'a cambriolé ce matin, les voleurs sont passés par le vélux de la chambre et ont volé tous les appareils électroniques. Merci de me contacter rapidement."

### Sortie

Réponse : {{"date_sinistre": "2026-08-20"}}


## Exemple

### Entrée

Aujourd'hui : 2026-08-20
Message : "Bonjour,

Le 10/09/2025, un feu s'est déclaré dans la chambre à cause d'un appareil défectueux, et à endommager une grande partie de la pièce. Je souhaiterai être indemnisé pour pouvoir effectuer les travaux nécessaires.

Bien cordialement.

[Pièce jointe : Chambre_1.jpg]
[Pièce jointe : Chambre_2.jpg]"

### Sortie

Réponse : {{"date_sinistre": "2025-09-10"}}


## Exemple

### Entrée

Aujourd'hui : 2026-08-20
Message : "Bonjour, suite à un problème de plomberie chez moi, mon garage s'est retrouvé sous l'eau. Veuillez trouver plus de détails dans la photo ci-jointe. [Pièce jointe : garage.png]"

### Sortie

Réponse : {{"date_sinistre": null}}


A ton tour avec le message suivant : {message}
""".strip()

# Nettoyage de la réponse LLM pour s'assurer qu'elle correspond au format JSON brut
def _reponse_nettoyee(raw_output: str) -> dict:
    cleaned = raw_output.strip()

    debut = cleaned.find("{")
    if debut == -1:
        raise ValueError(f"Aucun JSON trouvé dans la réponse du LLM : {raw_output!r}")

    objet, _ = json.JSONDecoder().raw_decode(cleaned[debut:])
    return objet

# Extraction de la date
async def extraire_date_sinistre(llm, message: str, date_reference: date) -> date | None:
    """Extrait la date via le llm depuis le message original de l'assuré."""
    prompt = PROMPT_EXTRACTION_DATE.format(
        date_reference=date_reference.isoformat(),
        message=message,
    )
    reponse = await llm.ainvoke([HumanMessage(content=prompt)])
    format_reponse = _reponse_nettoyee(reponse.content)

    date_str = format_reponse.get("date_sinistre")
    if date_str is None:
        return None

    try:
        return date.fromisoformat(date_str)
    except ValueError as e:
        print(f"[AVERTISSEMENT] Date invalide renvoyée par le LLM : {date_str!r}.traitée comme indéterminable.")
        return None

# Vérification du délai légal de déclaration du sinistre
def verifier_delai(type_sinistre: str, date_sinistre: date | None, date_reception: date) -> dict:
    delai_max = GARANTIES[type_sinistre]["delai_declaration"]

    if date_sinistre is None:
        return {"statut": "indeterminable", "jours_ecoules": None, "delai_max_jours": delai_max}

    jours_ecoules = (date_reception - date_sinistre).days

    if jours_ecoules < 0:
        return {"statut": "anomalie", "jours_ecoules": jours_ecoules, "delai_max_jours": delai_max}

    statut = "valide" if jours_ecoules <= delai_max else "depasse"
    return {"statut": statut, "jours_ecoules": jours_ecoules, "delai_max_jours": delai_max}


# --- VALIDITE DES IMAGES FOURNIES ---
# Création de la question à partir des catégories définies
def _construire_question_vlm(type_sinistre: str) -> str:
    """..."""
    definition = DEFINITIONS_SINISTRE[type_sinistre]
    return (
        f"Dans le contrat d'assurance habitation, le type de sinistre '{type_sinistre}' correspond à : {definition} " 
        "Cette image montre-t-elle des éléments visuels cohérents avec ce type de sinistre ?\n\n"
        "Ta réponse doit être EXACTEMENT l'un de ces trois mots, en toutes lettres, sans rien ajouter d'autre : oui / non / incertain. "
        "Exemple de réponse correcte : oui\n\n"
        ""
    )

# Obtenir la bonne question en fonction du sinistre
QUESTIONS_VLM: dict[str, str] = {
    type_sinistre: _construire_question_vlm(type_sinistre)
    for type_sinistre in DEFINITIONS_SINISTRE
}

# Extraction d'une réponse simple depuis la réponse brute
def _extraire_reponse_VLM(texte: str) -> str:
    """..."""
    texte_lower = texte.lower()
    contient_oui = re.search(r"\boui\b", texte_lower) is not None
    contient_non = re.search(r"\bnon\b", texte_lower) is not None

    if contient_oui and not contient_non:
        return "oui"
    if contient_non and not contient_oui:
        return "non"
    return "incertain"

# Lancement de la verification visuel
def verifier_photo(vlm, chemin_image: str, type_sinistre: str) -> dict:
    """"""
    question = QUESTIONS_VLM[type_sinistre]
    reponse_brute = analyser_image(vlm, chemin_image, question)
    correspond = _extraire_reponse_VLM(reponse_brute)
    return {"correspond": correspond, "reponse_brut":reponse_brute}


# --- DECISION FINALE ---
# Validité du dossier à partir des photos et de la date.
def decider_validation(delai: dict, photo: dict) -> dict:
    """Décide de la conformité du dossier en fonction de la validité des photos et de la date."""
    motifs = []

    if delai["statut"] == "depasse":
        motifs.append(
            f"Délai de declaration dépassé ({delai['jours_ecoules']} jours, " f"maximum autorisé {delai['delai_max_jours']} jours)."
        )
    elif delai["statut"] == "anomalie":
        motifs.append("Anomalie : la date du sinistre postérieure à la date de réception de la déclaration.")
    elif delai["statut"] == "indeterminable":
        motifs.append("Date du sinistre non déterminée.")

    if photo["correspond"] == "non":
        motifs.append("La photo fournie ne semble pas correspondre au type de sinistre déclaré.")
    elif photo["correspond"] == "incertain":
        motifs.append("Correspondance entre la photo et le type de sinistre incertaine.")

    decision = "conforme" if not motifs else "non_conforme"
    return {"decision": decision, "motifs": motifs}


# --- PIPELINE DE VALIDATION ---
async def valider_dossier(
        llm,
        vlm,
        message: str,
        type_sinistre: str,
        date_reception: date,
        chemin_photo: str | None = None,
) -> dict:
    """Execute le pipeline complet de l'Agent IA Validation sur un dossier."""

    date_sinistre = await extraire_date_sinistre(llm, message, date_reception)
    delai = verifier_delai(type_sinistre, date_sinistre, date_reception)

    if chemin_photo is not None:
        photo = verifier_photo(vlm, chemin_photo, type_sinistre)
    else:
        photo = {"correspond": "incertain", "reponse_brut": None}

    return decider_validation(delai, photo)



# TEST
"""if __name__ == "__main__":
    import asyncio

    from llm import load_llm
    from vlm import load_vlm

    async def main():
        llm = load_llm()
        vlm = load_vlm()

        message_test = (
            "Bonjour, on m'a cambriolé ce matin, les voleurs sont passés par le vélux de la chambre et ont volé tous les appareils électroniques. Merci de me contacter rapidement."
        )
        resultat = await valider_dossier(
            llm,
            vlm,
            message=message_test,
            type_sinistre="vol",
            date_reception=date.today(),
            chemin_photo="/Users/JR/Desktop/Blent/Projets/Agent_IA_assurance_habitation/data/exemples_pj/FireDamage_45.jpg",
        )
        print(resultat)

    asyncio.run(main())"""

if __name__ == "__main__":
    import asyncio

    from llm import load_llm
    from vlm import load_vlm

    async def main():
        llm = load_llm()
        vlm = load_vlm()

        message_test = (
            "Bonjour, j'ai eu un feu dans ma cuisine le 24/08/2026. ma gazinière et mon frigo ont pris feu. Une fenetre a été cassée par les pompiers. Voici ci-jointes les photos du sinistre. [Pièce jointe : photo.jpg]"
        )
        resultat = await valider_dossier(
            llm,
            vlm,
            message=message_test,
            type_sinistre="incendie",
            date_reception=date.today(),
            chemin_photo="/Users/JR/Desktop/Blent/Projets/Agent_IA_assurance_habitation/data/exemples_pj/FireDamage_193.png",
        )
        print(resultat)

    asyncio.run(main())


"""if __name__ == "__main__":
    import asyncio

    from llm import load_llm

    async def main():
        llm = load_llm()
        message_test = (
            "Bonjour, j'ai eu un feu dans ma cuisine le 22/09/2025. ma gazinière et mon frigo ont pris feu. Une fenetre a été cassée par les pompiers. Voici ci-jointes les photos du sinistre."
        )
        resultat = await extraire_date_sinistre(llm, message_test, date.today())
        print(resultat)

    asyncio.run(main())"""


"""if __name__ == "__main__":
    from vlm import load_vlm

    vlm = load_vlm()

    chemin_test = "/Users/JR/Desktop/Blent/Projets/Agent_IA_assurance_habitation/data/exemples_pj/FireDamage_45.jpg"
    resultat = verifier_photo(vlm, chemin_test, "incendie")
    print(resultat)"""