"""
Permet d'obtenir un rapport complet avec les premières estimations sur photos du sinistre déclaré.
"""

import re
import asyncio

from agent_declaration import DEFINITIONS_SINISTRE
from vlm import analyser_image
from agent_validation import GARANTIES
from langchain_core.messages import HumanMessage

# --- ESTIMATION DE LA GRAVITE ---
# Définition des niveaux de gravités
GRAVITES: list[str] = ["leger", "modere", "grave"]

# Création de la question à partir des catégories définies
def _construire_question_gravite(type_sinistre: str) -> str:
    """Utilise le dictionnaire DEFINITIONS_SINISTRE pour adapter la question au type de sinistre."""
    definition = DEFINITIONS_SINISTRE[type_sinistre]
    return (
        f"Le type de sinistre '{type_sinistre}' correspond à : {definition} "
        "Décris en une phrase le niveau de gravité des dégâts visibles sur cette photo : léger (dégâts mineurs, superficiels), modéré (dégâts significatifs mais localisés), ou grave (dégâts étendus ou structurels)."
    )

# Obtenir la bonne question en fonction du sinistre
QUESTIONS_GRAVITE: dict[str, str] = {
    type_sinistre: _construire_question_gravite(type_sinistre)
    for type_sinistre in DEFINITIONS_SINISTRE
}

# Extraction du niveau de gravité depuis la réponse brute
def _extraire_gravite(texte: str) -> str:
    """Utilise le dictionnaire GRAVITES pour récupérer le mot-clé de gravité dans la réponse du VLM"""
    texte_lower = texte.lower()
    niveaux_presents = [g for g in GRAVITES if re.search(rf"\b{g}\b", texte_lower)]
    if len(niveaux_presents) == 1:
        return niveaux_presents[0]
    return "grave"

# Lancement de l'analyse de l'image par le VLM
def evaluer_gravite_photo(vlm, chemin_image: str, type_sinistre: str) -> dict:
    """Appel le VLM avec la question construite et retourne la gravite du sinistre d'après l'analyse d'une image."""
    question = QUESTIONS_GRAVITE[type_sinistre]
    reponse_brute = analyser_image(vlm, chemin_image, question)
    gravite = _extraire_gravite(reponse_brute)
    return {"gravite": gravite, "reponse_brute": reponse_brute}

# Evaluation de la pire gravité du set de photo
def evaluer_gravite_globale(vlm, chemins_photos: list[str], type_sinistre: str) -> dict:
    """Défini la gravité du sinistre à partir de l'ensemble des resultats d'analyse de toutes les images."""
    if not chemins_photos:
        return {"gravite": "inconnue", "details": []}

    resultats = [evaluer_gravite_photo(vlm, chemin, type_sinistre) for chemin in chemins_photos]
    rang = {g: i for i, g in enumerate(GRAVITES)} # on transforme les gravités en niveaux chiffrés
    pire = max(resultats, key=lambda r: rang[r["gravite"]]) # on compare les resultats de l'évaluation en utilisant la correspondance chiffrée
    return {"gravite": pire["gravite"], "details": resultats}


# --- ESTIMATION DE L'INDEMNISATION ---
# Definition des fourchettes par niveau de gravité (pourcentage du plafond d'indemnisation)
FOURCHETTES_GRAVITE: dict[str, tuple[float, float]] = {
    "leger": (0.05,0.15),
    "modere": (0.15,0.40),
    "grave": (0.40,0.80),
}

# Estimation de la fourchette de coût total
def estimer_fourchette_cout(type_sinistre: str, gravite: str) -> dict:
    """Donne la fourchette de coût total du sinsitre d'après les plafonds donnés dans le contrat de garanties et en fonction du type de sinistre."""

    if gravite not in FOURCHETTES_GRAVITE:
        return {"cout_min": None, "cout_max": None}

    plafond = GARANTIES[type_sinistre]["plafond"]
    pourcentage_min, pourcentage_max = FOURCHETTES_GRAVITE[gravite]
    return {
        "cout_min": round(plafond * pourcentage_min, 2),
        "cout_max": round(plafond * pourcentage_max, 2)
    }

# Estimation du montant de l'indemnisation
def calculer_montant_indemnisation(type_sinistre: str, cout_min: float | None, cout_max: float | None) -> dict:
    """Donne la fourchette du montant de l'indemnisation en fonction à partir de la fourchette de coût total et de la franchise du type de sinistre."""
    if cout_min is None or cout_max is None:
        return {"indemnisation_min": None, "indemnisation_max": None}

    plafond = GARANTIES[type_sinistre]["plafond"]
    franchise = GARANTIES[type_sinistre]["franchise"]

    indemnisation_min = max(min(cout_min, plafond) - franchise, 0) # min prend la valeur la plus basse du cout et max évite des valeurs negatives.
    indemnisation_max = max(min(cout_max, plafond) - franchise, 0)
    return {"indemnisation_min": round(indemnisation_min, 2), "indemnisation_max": round(indemnisation_max, 2)}


# --- REDACTION DU RAPPORT ---
# Prompt de génération du rapport
PROMPT_RAPPORT = """
Tu es un agent IA qui rédige un rapport d'analyse d'un dossier de sinistre à l'attention d'un consieiller d'une assurance habitation.
Voici le message original de l'assuré pour ton contexte narratif uniquement :
{message}

Ta seule tâche est de mettre en forme dans un texte claire les informations fournies ci-dessous.
- Type de sinistre : {type_sinistre}
- Statut du délai de déclaration : {delai_statut}
- Décision de validation du dossier : {decision_validation}
- Motifs de validation (le cas écheant) : {motifs_validation}
- Gravité estimée (sur analyse des photos) : {gravite}
- Fourchette de coût total estimée : {cout_min} € - {cout_max} €
- Fourchette du montant de l'indemnisation estimé : {indemnisation_min} € - {indemnisation_max} €

Rédige le rapport de synthèse correspondant à ces éléments de façon littéraire et concise.
Pas de liste.
Termine SYSTÉMATIQUEMENT ton rapport par cette phrase : "Ce dossier nécessite la validation d'un conseiller avant toute décision finale."
""".strip()

# Génération du rapport
async def generer_rapport(
        llm,
        message: str,
        type_sinistre: str,
        delai: dict,
        validation: dict,
        gravite: str,
        cout: dict,
        indemnisation: dict,
) -> str:
    """..."""
    prompt = PROMPT_RAPPORT.format(
        message=message,
        type_sinistre=type_sinistre,
        delai_statut=delai["statut"],
        decision_validation=validation["decision"],
        motifs_validation="; ".join(validation["motifs"]) if validation["motifs"] else "aucun",
        gravite=gravite,
        cout_min=cout["cout_min"],
        cout_max=cout["cout_max"],
        indemnisation_min=indemnisation["indemnisation_min"],
        indemnisation_max=indemnisation["indemnisation_max"],
    )
    reponse = await llm.ainvoke([HumanMessage(content=prompt)])
    return reponse.content


# --- PIPELINE COMPLET ---
async def expertiser_dossier(
    llm,
    vlm,
    message: str,
    type_sinistre: str,
    delai: dict,
    validation: dict,
    chemins_photos: list[str],
) -> dict:
    """Effectue l'analyse complète du dossier jusqu'à génération du rapport."""
    gravite_globale = await asyncio.to_thread(evaluer_gravite_globale, vlm, chemins_photos, type_sinistre)
    gravite = gravite_globale["gravite"]

    cout = estimer_fourchette_cout(type_sinistre, gravite)
    indemnisation = calculer_montant_indemnisation(type_sinistre, cout["cout_min"], cout["cout_max"])

    rapport = await generer_rapport(llm, message, type_sinistre, delai, validation, gravite, cout, indemnisation)

    return {
        "gravite": gravite,
        "cout_estime": cout,
        "indemnisation": indemnisation,
        "rapport": rapport,
        "necessite_conseiller": True,
    }


# TEST
"""if __name__ == "__main__":
    fourchette = estimer_fourchette_cout("degat_des_eaux", "modere")
    print(fourchette)
    indemnisation = calculer_montant_indemnisation("degat_des_eaux", fourchette["cout_min"], fourchette["cout_max"])
    print(indemnisation)"""

"""if __name__ == "__main__":
    import asyncio

    from llm import load_llm
    from vlm import load_vlm

    async def main():
        llm = load_llm()
        vlm = load_vlm()

        delai_fictif = {"statut": "valide", "jours_ecoules": 1, "delai_max_jours": 2}
        validation_fictive = {"decision": "conforme", "motifs": []}

        resultat = await expertiser_dossier(
            llm,
            vlm,
            message="Bonjour, j'ai eu un feu dans ma cuisine le 24/08/2026. ma gazinière et mon frigo ont pris feu. Une fenetre a été cassée par les pompiers. Voici ci-jointes les photos du sinistre. [Pièce jointe : photo.jpg]",
            type_sinistre="incendie",
            delai=delai_fictif,
            validation=validation_fictive,
            chemins_photos=["/Users/JR/Desktop/Blent/Projets/Agent_IA_assurance_habitation/data/exemples_pj/FireDamage_193.png"],
        )
        print(resultat["rapport"])

    asyncio.run(main())"""