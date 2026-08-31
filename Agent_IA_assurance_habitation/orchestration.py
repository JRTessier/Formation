"""
Orchestration du pipeline avec les trois agents IA (Declaration, Validation, Expertise).
"""

from datetime import date
from agent_validation import valider_dossier
from agent_expertise import expertiser_dossier
from donnees_contrat import PRESTATAIRES

# Identification du prestaire
def identifier_prestataires(type_sinistre: str, gravite: str) -> dict:
    """Identifie le/les prestataire(s) necessaires en fonction du type et de la gravite du sinistre selon les règles établies dans le conttrat"""
    regles = PRESTATAIRES[type_sinistre]
    prestataires = list(regles["systematique"])
    a_verifier_manuellement = False

    conditionnel = regles["conditionnel"]
    if conditionnel is not None:
        if gravite == "inconnue":
            a_verifier_manuellement = True # Pas de photo exploitable, necessite une vérification humaine
        elif gravite == conditionnel["si_gravite"]:
            prestataires.append(conditionnel["prestataire"])

    return {"prestataires": prestataires, "a_verifier_manuellement": a_verifier_manuellement}


# Pipeline complet
async def orchestrer_dossier(
    llm,
    vlm,
    message: str,
    resultat_declaration: dict,
    date_reception: date,
    chemins_photos: list[str],
) -> dict:
    """Déroule le pipeline Declaration -> Validation -> Expertise."""

    # Appel l'agent IA Declaration
    type_sinistre = resultat_declaration["type_sinistre"]
    chemin_photo_principale = chemins_photos[0] if chemins_photos else None # on considère qu'une seul photo suffit pour valider le type de sinistre.

    # Appel l'agent IA Validation
    validation = await valider_dossier(
        llm,
        vlm,
        message=message,
        type_sinistre=type_sinistre,
        date_reception=date_reception,
        chemin_photo=chemin_photo_principale,
    )

    # Transition vers l'agent suivant ou retour assuré négatif pour non conformité
    if validation["decision"] != "conforme":
        return {"status": "retour_assure", "motifs": validation["motifs"]}

    # Appel l'agent IA Expertise
    expertise = await expertiser_dossier(
        llm,
        vlm,
        message=message,
        type_sinistre=type_sinistre,
        delai=validation["delai"],
        validation=validation,
        chemins_photos=chemins_photos,
    )

    prestataires = identifier_prestataires(type_sinistre, expertise["gravite"])

    # Retour assuré avec 
    return  {
        "status": "transmission_conseiller",
        "validation": validation,
        "expertise": expertise,
        "prestataires:": prestataires,
    }


# TEST — cycle complet, du message initial jusqu'à Expertise
if __name__ == "__main__":
    import asyncio
    from datetime import date as date_cls
    from graph_declaration import init_declaration, update_declaration

    from llm import load_llm
    from Agent_IA_assurance_habitation.vlm import load_vlm

    async def main():
        message_test = (
            "Bonjour, j'ai eu un feu dans ma cuisine le 28/08/2026. ma gazinière et "
            "mon frigo ont pris feu. Une fenetre a été cassée par les pompiers. "
            "Voici l'inventaire des biens détruits : gazinière, frigo, fenêtre. "
            "[Pièce jointe : photo.jpg]"
        )

        print("--- Déclaration ---")
        resultat = await init_declaration(message_test)
        print("Statut :", resultat["status"])

        if resultat["status"] == "en_attente":
            print("\n--- Reprise (simulation de la réponse de l'assuré) ---")
            resultat = await update_declaration(resultat["thread_id"], "Voici les factures manquantes.")
            print("Statut :", resultat["status"])

        if resultat["status"] != "complet":
            print("Dossier non complet, arrêt du test.")
            return

        date_reception = date_cls.fromisoformat(resultat["date_reception"])

        print("\n--- Chargement des modèles pour Validation/Expertise ---")
        llm = load_llm()
        vlm = load_vlm()

        print("\n--- Validation + Expertise ---")
        resultat_final = await orchestrer_dossier(
            llm,
            vlm,
            message=message_test,
            resultat_declaration=resultat["resultat"],
            date_reception=date_reception,
            chemins_photos=[
                "/Users/JR/Desktop/Blent/Projets/Agent_IA_assurance_habitation/data/exemples_pj/FireDamage_193.png"
            ],
        )
        print("Statut final :", resultat_final["status"])
        if resultat_final["status"] == "retour_assure":
            print("Motifs :", resultat_final["motifs"])
        elif resultat_final["status"] == "transmission_conseiller":
            print(resultat_final["expertise"]["rapport"])

    asyncio.run(main())