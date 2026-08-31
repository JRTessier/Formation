"""
Données de référence du contrat d'assurance habitation, partagées entre
les agents Déclaration, Validation et Expertise.
"""

# Checklist par type de sinistre.
CHECKLISTS: dict[str, dict[str, dict]] = {
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
            "obligatoire": True,  # passera en null pour les cas ne necessitant pas de constat amiable
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

# Définitions officielles de l'assurance pour chaque type de sinistre.
DEFINITIONS_SINISTRE: dict[str, str] = {
    "degat_des_eaux": (
        "Fuites, ruptures de canalisation, infiltrations. "
        "Débordement d’appareils électroménagers (lave-linge, lave-vaisselle, etc.). "
        "Dommages causés aux voisins (responsabilité civile)."
    ),
    "incendie": ("Incendie, explosion, implosion. " "Fumées accidentelles."),
    "vol": ("Vol avec effraction ou agression. " "Détérioration lors d’une tentative de vol."),
}

# Définitions des garanties par type de sinistre.
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

PRESTATAIRES : dict[str, dict] = {
    "degat_des_eaux": {
        "systematique": ["plombier"],
        "condtionnel": {"prestataire": "expert_assurance", "si_gravite": "grave"},
    },
    "incendie": {
        "systematique": ["expert_incendie"],
        "conditionnel": {"prestataire": "hebergement_temporaire", "si_gravite": "grave"},
    },
    "vol": {
        "systematique": ["serrurier"],
        "conditionnel": None,
    }
}