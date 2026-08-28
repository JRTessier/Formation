"""
Agent IA Déclaration

A partir du message de l'utilisateur, l'agent doit identifier le type de sinistre
et uniquement vérifier la présence effective des éléments requis.
"""

import json

from langchain_core.messages import HumanMessage

# Checklist par type de sinistre
CHECKLISTS: dict[str, dict[str, str]] = {
    "degat_des_eaux": {
        "date_sinistre": {
            "description": "Date à laquelle le sinistre s'est produit",
            "obligatoire": True,
        },
        "description": {
            "description": "Récit de ce qui s'est passé",
            "obligatoire": True,
        },
        "photos_videos": {
            "description": "Photos ou vidéos du sinistre",
            "obligatoire": True,
                },
        "factures": {
            "description": "Factures des éléments endommagés (si disponibles)",
            "obligatoire": False,
                },
        "constat_amiable": {
            "description": "Constat amiable avec les voisins/tiers concernés le cas échant",
            "obligatoire": True, # passera en null pour les cas ne necessitant pas de constat amiable
        },
    },
    "incendie": {
        "date_sinistre": {
            "description": "Date à laquelle le sinistre s'est produit",
            "obligatoire": True,
                },
        "description": {
            "description": "Récit de ce qui s'est passé",
            "obligatoire": True,
                },
        "inventaire": {
            "description": "Inventaire exhaustif des biens détruits",
            "obligatoire": True,
                },
        "photos_videos": {
            "description": "Photos ou vidéos du sinistre",
            "obligatoire": True,
                },
        "factures": {
            "description": "Factures des éléments endommagés (si disponibles)",
            "obligatoire": False,
        },
    },
    "vol": {
            "date_sinistre": {
                "description": "Date à laquelle le sinistre s'est produit",
                "obligatoire": True,
            },
            "description": {
                "description": "Récit de ce qui s'est passé",
                "obligatoire": True,
            },
            "pv_police": {
                "description": "Procès-verbal du dépôt de plainte à la police",
                "obligatoire": True,
            },
            "inventaire": {
                "description": "Inventaire exhaustif des biens volés",
                "obligatoire": True,
            },
            "photos_videos": {
                "description": "Photos ou vidéos des biens volés (si disponibles)",
                "obligatoire": False,
            },
            "factures": {
                "description": "Factures des biens volés (si disponibles)",
                "obligatoire": False,
            },
            "garanties": {
                "description": "Garanties des biens volés (si disponibles)",
                "obligatoire": False,
            },
        },
}

# On ajoute la définition officielles de l'assurance pour chacun des types de sinistre à traiter.
DEFINITIONS_SINISTRE: dict[str, str] = {
    "degat_des_eaux": (
        "Fuites, ruptures de canalisation, infiltrations. "
        "Débordement d’appareils électroménagers (lave-linge, lave-vaisselle, etc.). "
        "Dommages causés aux voisins (responsabilité civile)."),
    "incendie": (
        "Incendie, explosion, implosion. "
        "Fumées accidentelles."),
    "vol": (
        "Vol avec effraction ou agression. "
        "Détérioration lors d’une tentative de vol."
    )
}

PROMPT_TEMPLATE = """
Tu es un agent IA qui traite les messages des assurés d'une assurance habitation afin d'établir leur dossier de déclaration de sinistre

Ta mission :
1. Identifier dans le message le type de sinistre parmi : "degat_des_eaux", "incendie", "vol".
2. Vérifier, pour le type identifié, la présence effective dans le message de l'assuré, de chacun des éléments requis.

Tu ne dois PAS juger si les informations sont correctes, uniquement vérifier que les éléments sont présents.

Voici les définitions officielles de l'assurance pour chaque type de sinistre :
{definitions}

Voici les éléments requis par type de sinistre pour le dossier:
{checklists}

Règles :
- Un élément textuel (date_sinistre, description, inventaire) est considéré présent si le texte le mentionne explicitement.
- Un élément qui nécessite un document ou une preuve visuelle (photos_vidéos, factures, garanties, pv_police(PV, procès-verbal), constat_amiable) n'est considéré présent QUE s'il existe un marqueur [Pièce jointe : ...] correspondant dans le message. Une simple affirmation de l'assuré dans le texte ("voici les photos", "je joins la facture") SANS marqueur [Pièce jointe : ...] ne suffit PAS : réponds false dans ce cas, l'assuré a pu oublier la pièce jointe.
- Ne déduis JAMAIS la nature d'une pièce jointe uniquement depuis son nom de fichier (ex: un fichier nommé "PV.jpg" n'est pas forcément un procès-verbal). Base-toi sur ce que le texte environnant décrit explicitement à propos de cette pièce jointe.
- En cas de doute réel sur la présence d'un élément (aucun indice textuel, ni sur le nom du fichier, ni dans la description), réponds false plutôt que true.
- ATTENTION ! Pour constat_amiable du type degat_des_eaux, si le sinistre n'implique pas de voisins/tiers réponds null à la place de false.
- Pour inventaire, on attend un liste exhaustive des biens volés ou détruits. "on m'a volé toutes mes cartes pokemon" n'est pas un inventaire valide.
- Date_sinistre est considéré présent si le texte indique QUAND le sinistre s'est produit, sous n'importe quelle forme (date précise, ou expression relative comme "hier", "ce matin"). Si le texte ne donne AUCUNE indication temporelle, réponds false.
- Réponds UNIQUEMENT avec un objet JSON valide, sans aucun texte autour, au format suivant :

{{"type_sinistre": "...", "elements_requis": {{"nom_element": true, "...": false, "...": null}}}}

## Exemple

### Entrée

Message : "Bonjour, Il y a eu une fuite dans ma cuisine hier soir à cause de mon voisin du dessus. Son lave-vaisselle a été mal installé et du coup, le mur est infiltré d'eau et la peinture se détache (ci-joint une photo). Cordialement. [Pièce jointe : IMG_4580.jpg]"

### Sortie

Réponse : {{"type_sinistre": "degat_des_eaux", "elements_requis": {{"date_sinistre": true, "description": true, "inventaire": false, "photos_videos": true, "factures": false, "constat_amiable": false, "pv_police": false, "garanties": false}}}}
 
## Exemple

### Entrée

Message : "Bonjour, on m'a cambriolé ce matin, les voleurs sont passés par le vélux de la chambre et ont volé tous les appareils électroniques. Merci de me contacter rapidement."

### Sortie

Réponse : {{"type_sinistre": "vol", "elements_requis": {{"date_sinistre": true, "description": true, "inventaire": false, "photos_videos": false, "factures": false, "constat_amiable": null, "pv_police": false, "garanties": false}}}}

## Exemple

### Entrée

Message : "Bonjour, Le 10/09/2025, un feu s'est déclaré dans la chambre à cause d'un appareil défectueux, et à endommager une grande partie de la pièce. Je souhaiterai être indemnisé pour pouvoir effectuer les travaux nécessaires. L'appareil était sous garantie ci-jointe. Bien cordialement. [Pièce jointe : Chambre_1.jpg] [Pièce jointe : Chambre_2.jpg] [Pièce jointe : Garantie.jpg]"

### Sortie

Réponse : {{"type_sinistre": "incendie", "elements_requis": {{"date_sinistre": true, "description": true, "inventaire": false, "photos_videos": true, "factures": false, "constat_amiable": null, "pv_police": false, "garanties": true}}}}

## Exemple

### Entrée

Message : "Bonjour, j'ai eu un feu dans ma cuisine le 22/09/2025. ma gazinière et mon frigo ont pris feu. Une fenetre a été cassée par les pompiers. Voici ci-jointes les photos du sinistre."

### Sortie

Réponse : {{"type_sinistre": "incendie", "elements_requis": {{"date_sinistre": true, "description": true, "inventaire": true, "photos_videos": false, "factures": false, "constat_amiable": null, "pv_police": false, "garanties": false}}}}

## Exemple

### Entrée

Message : "Des individus sont entré par effraction par la fenetre de ma chambre dans la nuit du 15 au 16 aout dernier. Ils ont derobé mon collier en diamant 18 carat. Veuillez trouver ci joints la photo du collier et le procès verbal [Pièce jointe : SexyMoss.jpg] [Pièce jointe : MauriceCop.jpg]"

### Sortie

Réponse : {{"type_sinistre": "vol", "elements_requis": {{"date_sinistre": true, "description": true, "inventaire": true, "photos_videos": true, "factures": false, "constat_amiable": null, "pv_police": true, "garanties": false}}}}

## Exemple

### Entrée

Message : "J'ai un degats des eaux dans mon appartement, survenu le 16/08/2026 suite à un problème avec ma machine à laver. [Pièce jointe : degat-des-eaux.jpg]"

### Sortie

Réponse : {{"type_sinistre": "degat_des_eaux", "elements_requis": {{"date_sinistre": true, "description": true, "inventaire": false, "photos_videos": true, "factures": false, "constat_amiable": null, "pv_police": false, "garanties": false}}}}

## Exemple

### Entrée

Message : "Bonjour, suite à un problème de plomberie chez moi, mon garage s'est retrouvé sous l'eau. Veuillez trouver plus de détails dans la photo ci-jointe. [Pièce jointe : garage.png]"

### Sortie

Réponse : {{"type_sinistre": "degat_des_eaux", "elements_requis": {{"date_sinistre": false, "description": true, "inventaire": false, "photos_videos": true, "factures": false, "constat_amiable": null, "pv_police": false, "garanties": false}}}}

## Exemple

### Entrée

Message : "Mon PC a explosé ! Regardez la photo ! En plus il était tout neuf. Voici la liste des biens détruits:"
        "- PC gamer AMD Ryzen 5 5500"
        "- televiseur sony 32 pouces"
        "- iphone 11"
        "- lampe de bureau ikea"
        "Et les factures ci jointes[Pièce jointe : PC.png] [Pièce jointe : PC_facture.png] [Pièce jointe : portable_facture.png] [Pièce jointe : TV_facture.png]"
    )
### Sortie

Réponse : {{"type_sinistre": "incendie", "elements_requis": {{"date_sinistre": false, "description": true, "inventaire": true, "photos_videos": true, "factures": true, "constat_amiable": null, "pv_police": false, "garanties": false}}}}


A ton tour avec le message suivant : {message}
""".strip()

# Formatage des dictionnaires en texte brute pour être insérés dans le prompt
# Definition
def _format_definitions() -> str:
    return "\n".join(
        f"- {type_sinistre} : {definition}"
        for type_sinistre, definition in DEFINITIONS_SINISTRE.items()
    )

# Checklist
def _format_checklist(checklist: dict[str, dict]) -> str:
    return "\n".join(
        f"- {key} : {meta['description']}"
        for key, meta in checklist.items()
    )
def _format_all_checklist() -> str:
    return "\n".join(
        f"### {type_sinistre}\n{_format_checklist(checklist)}"
        for type_sinistre, checklist in CHECKLISTS.items()
    )

# Nettoyage de la réponse LLM pour s'assurer qu'elle correspond au format JSON brut
def _reponse_nettoyee(raw_output: str) -> dict:
    cleaned = raw_output.strip()

    debut = cleaned.find("{")
    if debut == -1:
        raise ValueError(f"Aucun JSON trouvé dans la réponse du LLM : {raw_output!r}")

    objet, _ = json.JSONDecoder().raw_decode(cleaned[debut:])
    return objet

# Verification de la completude du dossier
def _calculer_completude(type_sinistre: str, elements_requis: dict) -> tuple[list[str], bool]:
    checklist = CHECKLISTS[type_sinistre]
    _ABSENTE = object()
    elements_manquants = [
        cle for cle, meta in checklist.items()
        if meta["obligatoire"]
        and (valeur := elements_requis.get(cle, _ABSENTE)) is not True
        and valeur is not None
    ]
    complet = len(elements_manquants) == 0
    return elements_manquants, complet

# Interpretation et reception de la déclaration
async def recevoir_declaration(llm, message: str) -> dict:
    """ Interprète le type de sinsitre depuis le message de l'assuré et vérifie la présence des éléments requis pour la declaration """
    prompt = PROMPT_TEMPLATE.format(
        definitions=_format_definitions(),
        checklists=_format_all_checklist(),
        message=message,
    )
    reponse = await llm.ainvoke([HumanMessage(content=prompt)])
    format_reponse =_reponse_nettoyee(reponse.content)

    type_sinistre = format_reponse["type_sinistre"]
    elements_requis = format_reponse["elements_requis"]
    elements_manquants, complet = _calculer_completude(type_sinistre, elements_requis)

    return {
        "type_sinistre": type_sinistre,
        "elements_requis": elements_requis,
        "elements_manquants": elements_manquants,
        "complet": complet,
    }

# TEST
if __name__ == "__main__":
    import asyncio
    from llm import load_llm

    async def main():
        llm = load_llm()

        declaration_test = (
            "Bonjour, suite à un problème de plomberie chez moi, mon garage s'est retrouvé sous l'eau. Veuillez trouver plus de détails dans la photo ci-jointe. [Pièce jointe : garage.png]"
        )
        resultat = await recevoir_declaration(llm, declaration_test)
        print(json.dumps(resultat, indent=2, ensure_ascii=False))

    asyncio.run(main())