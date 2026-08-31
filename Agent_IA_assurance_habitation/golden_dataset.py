"""
Agent IA Déclaration : évaluer la complétude des informations demandées.
Agent IA Validation : évaluer la capacité de l'agent à utiliser les bonnes informations factuelles du contrat par rapport au sinistre déclaré.
Agent IA Expertise : aucune évaluation n'est attendue, celle-ci sera effectuée manuellement par les experts métiers.

Agent IA Declaration : complet / incomplet
Agent IA Validation : conforme / non conforme

"""

GOLDEN_DATASET = [
    # --- Dégât des eaux ---
    {
        "id": 1, # complet et conforme
        "type_sinistre": "degat_des_eaux",
        "message": (
            "Bonjour, ma machine à laver a débordé hier soir dans ma salle de bain, inondant une partie du sol. Voici une photo des dégâts. [Pièce jointe : salle_de_bain.jpg]"
        ),
        "date_reception": "2026-08-30",
        "golden_date_sinistre": "2026-08-29",
        "golden_elements_requis": {
            "date_sinistre": True,
            "description": True,
            "inventaire": False,
            "photos_videos": True,
            "factures": False,
            "constat_amiable": None,
            "pv_police": False,
            "garanties": False,
        },
    },
    {
        "id": 2, # incomplet
        "type_sinistre": "degat_des_eaux",
        "message": (
            "Il y a une semaine, mon voisin du dessus a eu une fuite dans sa salle de bain. L'eau a traversé mon plafond. Le voisin est bien au courant. Voici une photo du plafond endommagé. "
            "[Pièce jointe : plafond.jpg]"
        ),
        "date_reception": "2026-08-30",
        "golden_date_sinistre": "2026-08-23", # !!! on garde ça ?
        "golden_elements_requis": {
            "date_sinistre": True,
            "description": True,
            "inventaire": False,
            "photos_videos": True,
            "factures": False,
            "constat_amiable": False, # <-- manque le constat amiable
            "pv_police": False,
            "garanties": False,
        },
    },
    {
        "id": 3, # complet et non conforme
        "type_sinistre": "degat_des_eaux",
        "message": (
            "Bonjour, je vous informe qu'un dégât des eaux est survenu dans ma cuisine le 05/08/2026 suite à une fuite de canalisation. "
            "Veuillez trouver ci-jointe une photo de l'inondation. "
            "[Pièce jointe : cuisine_degat.jpg]"
        ),
        "date_reception": "2026-08-30",
        "golden_date_sinistre": "2026-08-05", # <-- delai de declaration dépassé
        "golden_elements_requis": {
            "date_sinistre": True,
            "description": True,
            "inventaire": False,
            "photos_videos": True,
            "factures": False,
            "constat_amiable": None,
            "pv_police": False,
            "garanties": False,
        },
    },
    # --- Incendie ---
    {
        "id": 4, # complet et conforme
        "type_sinistre": "incendie",
        "message": (
            "Bonjour, un court-circuit à déclenché un incendie dans mon salon avant-hier. Les pompiers sont intervenus, la télévision et le canapé ont été détruits. Voici les photos des dégâts. "
            "[Pièce jointe : salon_incendie01.jpg] [Pièce jointe : salon_incendie02.jpg]"
        ),
        "date_reception": "2026-08-30",
        "golden_date_sinistre": "2026-08-28",
        "golden_elements_requis": {
            "date_sinistre": True,
            "description": True,
            "inventaire": True,
            "photos_videos": True,
            "factures": False,
            "constat_amiable": None,
            "pv_police": False,
            "garanties": False,
        },
    },
    {
        "id": 5, # incomplet
        "type_sinistre": "incendie",
        "message": (
            "Bonjour, il y a 3 jours, un feu s'est déclaré dans ma cuisine à cause d'un appareil défectueux. Une partie du plafond de la cuisine a été endommagée par la fumée. Voici une photo. "
            "[Pièce jointe : cuisine_feu.jpg]"
        ),
        "date_reception": "2026-08-30",
        "golden_date_sinistre": "2026-08-27",
        "golden_elements_requis": {
            "date_sinistre": True,
            "description": True,
            "inventaire": False, # <-- manque inventaire
            "photos_videos": True,
            "factures": False,
            "constat_amiable": None,
            "pv_police": False,
            "garanties": False,
        },
    },
    {
        "id": 6, # complet et non conforme
        "type_sinistre": "incendie",
        "message": (
            "Je vous signale qu'un incendie s'est déclaré dans mon garage le 16/06/2026, détruisant une tondeuse et des outils de jardinage. Les photos des dégâts sont en pièces jointes. "
            "[Pièce jointe : garage_incendie.jpg] [Pièce jointe : tondeuse.jpg] [Pièce jointe : garage_armoire.jpg]"
        ),
        "date_reception": "2026-08-30",
        "golden_date_sinistre": "2026-06-16", # <-- délai de déclaration dépassé
        "golden_elements_requis": {
            "date_sinistre": True,
            "description": True,
            "inventaire": True,
            "photos_videos": True,
            "factures": False,
            "constat_amiable": None,
            "pv_police": False,
            "garanties": False,
        },
    },
    # --- vol ---
    {
        "id": 7, # complet
        "type_sinistre": "vol",
        "message": (
            "Bonjour, hier soir des cambrioleurs sont entrés par la fenêtre de mon salon et ont volé un ordinateur portable, une montre connectée et des bijoux. J'ai déposé plainte ce matin. Voici le procès-verbal et une photo de la fenêtre forcée. "
            "[Pièce jointe : PV_police.jpg] [Pièce jointe : fenetre_forcee.jpg]"
        ),
        "date_reception": "2026-08-30",
        "golden_date_sinistre": "2026-08-29",
        "golden_elements_requis": {
            "date_sinistre": True,
            "description": True,
            "pv_police": True,
            "inventaire": True,
            "photos_videos": True,
            "factures": False,
            "garanties": False,
        },
    },
    {
        "id": 8, # incomplet
        "type_sinistre": "vol",
        "message": (
            "Bonjour, ce matin j'ai découvert que mon appartement avait été forcé et cambriolé pendant la nuit. Ils ont volé mon écran TV, ma PS5 et ma trotinette électrique. Voici une photo des dégâts sur la porte d'entrée. [Pièce jointe : porte_forcee.jpg]"
        ),
        "date_reception": "2026-08-30",
        "golden_date_sinistre": "2026-08-30",
        "golden_elements_requis": {
            "date_sinistre": True,
            "description": True,
            "pv_police": False, # <-- manque le procès-verbal 
            "inventaire": True,
            "photos_videos": True,
            "factures": False,
            "garanties": False,
        },
    },
    {
        "id": 9, # complet et non conforme
        "type_sinistre": "vol",
        "message": (
            "Madame, monsieur "
            "Des individus ont pénétré mon domicile par effraction le "
            "20/08/2026. Ont été dérobés: "
            "- un ordinateur portable "
            "- un appareil photo "
            "- une console de jeux Nintendo Switch 2 "
            "J'ai déposé plainte le jour même. Voici le procès-verbal et une photo de la serrure forcée. "
            "[Pièce jointe : PV.jpg] [Pièce jointe : serrure.jpg]"
        ),
        "date_reception": "2026-08-30",
        "golden_date_sinistre": "2026-08-20", # <-- délai de déclaration dépassé
        "golden_elements_requis": {
            "date_sinistre": True,
            "description": True,
            "pv_police": True,
            "inventaire": True,
            "photos_videos": True,
            "factures": False,
            "garanties": False,
        },
    },
]