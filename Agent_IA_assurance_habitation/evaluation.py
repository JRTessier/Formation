"""..."""

import csv
import asyncio

from agent_declaration import recevoir_declaration, _calculer_completude
from agent_validation import extraire_date_sinistre, verifier_delai
from datetime import date
from llm import load_llm
from golden_dataset import GOLDEN_DATASET


# Calcul du F1-score
def _f1_score(predits: set, golden: set) -> float:
    """
    Donne une évaluation F1-score entre ce qui est predtis par le llm et ce qui est attendu.
    """
    if not predits and not golden:
        return 1.0
    if not predits or not golden:
        return 0.0

    vrais_positifs = len(predits & golden) # intersection = nombre de fois où l'agent à eu raison
    precision = vrais_positifs / len(predits) # bonnes réponses parmi ce que l'agent à dit
    rappel = vrais_positifs / len(golden) # bonnes réponses parmi ce qui était vraiment attendu
    if precision + rappel == 0:
        return 0.0
    return 2 * precision * rappel / (precision + rappel) # formule F1 score


# Evaluation de l'agent IA Déclaration
async def evaluer_declaration(llm, exemple: dict) -> dict:
    """
    Evalue l'agent IA Déclaration sur le resultat obtenu concernant des éléments potentielement manquant dans le message de l'assuré.
    """
    resultat = await recevoir_declaration(llm, exemple["message"])

    golden_manquants, golden_complet = _calculer_completude(
        exemple["type_sinistre"], exemple["golden_elements_requis"]
    )

    return {
        "type_sinistre_predit": resultat["type_sinistre"],
        "type_sinistre_correct": resultat["type_sinistre"] == exemple["type_sinistre"],
        "complet_predit": resultat["complet"],
        "complet_golden": golden_complet,
        "complet_correct": resultat["complet"] == golden_complet,
        "f1_elements_manquants": round(
            _f1_score(set(resultat["elements_manquants"]), set(golden_manquants)), 3
        ),
    }

# Evaluation de l'agent IA Validation
async def evaluer_validation(llm, exemple: dict) -> dict:
    """
    Evalue l'agent IA Validation en se basant sur les résultats d'extraction de la date et la conformité du delai de déclaration.
    """

    date_reception = date.fromisoformat(exemple["date_reception"])

    date_sinistre_predite = await extraire_date_sinistre(llm, exemple["message"], date_reception)
    delai_predit = verifier_delai(exemple["type_sinistre"], date_sinistre_predite, date_reception)

    date_sinistre_golden = date.fromisoformat(exemple["golden_date_sinistre"])
    delai_golden = verifier_delai(exemple["type_sinistre"], date_sinistre_golden, date_reception)

    return {
        "date_sinistre_predite": date_sinistre_predite.isoformat() if date_sinistre_predite else None,
        "date_sinistre_golden": exemple["golden_date_sinistre"],
        "date_correcte": date_sinistre_predite == date_sinistre_golden,
        "statut_delai_predit": delai_predit["statut"],
        "statut_delai_golden": delai_golden["statut"],
        "statut_delai_correct": delai_predit["statut"] == delai_golden["statut"],
    }

# Orchestration de l'évaluation
async def evaluer_dataset(chemin_csv: str = "golden_dataset_resultats.csv"):
    """Orchestration de l'évaluation complète et création d'un fichier .csv regroupant les résultats."""
    llm = load_llm()
    lignes = []

    for exemple in GOLDEN_DATASET:
        print(f"--- Exemple {exemple['id']} ({exemple['type_sinistre']}) ---")

        eval_declaration = await evaluer_declaration(llm, exemple)
        eval_validation = await evaluer_validation(llm, exemple)

        ligne = {"id": exemple["id"], "type_sinistre": exemple["type_sinistre"]}
        ligne.update(eval_declaration)
        ligne.update(eval_validation)
        lignes.append(ligne)

        print(ligne)

    with open(chemin_csv, "w", newline="", encoding="utf-8") as fichier:
        writer = csv.DictWriter(fichier, fieldnames=lignes[0].keys())
        writer.writeheader()
        writer.writerows(lignes)

    print(f"\nRésultats écrits dans {chemin_csv}")
    return lignes

if __name__ == "__main__":
    asyncio.run(evaluer_dataset())