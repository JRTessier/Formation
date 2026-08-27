# Brief
Afin d'optimiser les délais de prise en charge et de résolution des sinistres, une grande compagnie d'assurance souhaite mettre en place une solution reposant sur des agents IA spécialisés, capables d'accompagner l'assuré dans sa déclaration et d'automatiser une partie des étapes de gestion du dossier.

Dans le cadre de ce projet Hands-On, nous nous concentrerons uniquement sur les trois sinistres suivants.

- Dégâts des eaux.
- Incendie / explosion.
- Vol, cambriolage, vandalisme.

# Architecture du pipeline

L'architecture s'inspire d'un pattern Plan-and-Execute. Mais ici le plan étant déjà fixé par le processus de gestion des sinistres, nous préfèrerons ne pas déléguer la tâche de plannification à un LLM qui laisserait la porte ouverte à d'éventuelles erreurs et ajouterait un appel inutile.
Nous implémentons également des étapes Human-in-the-Loop afin de fluidifier l'expérience de l'utilisateur.
```
Entrée de l'utilisateur
        |
        |
        v
Agent IA Déclaration
        |
        |   si imcomplet
        |<-----------------> Human-in-the-loop
        v
Agent IA Validation
        |
        |   si non valide
        |<-----------------> Human-in-the-loop
        v
Agent IA Expertise
        |
        |
        v
```


# Trois Agents IA
## Agent IA Déclaration
L'agent IA Déclaration guide l'assuré dans la saisie (photos, documents, délais légaux).

Ce qui est attendu de la part de l'assuré :

### Dégâts des eaux
- Date du sinistre
- Déclarer le sinistre sous 5 jours ouvrés.
- Fournir photos/vidéos des dégâts, factures si disponibles.
- Remplir un constat amiable dégâts des eaux avec les voisins/tiers concernés.

Checklist:
- Date du sinistre
- Description du sinistre
- Photos/vidéos du sinistre
- Factures des éléménents endommagés si possibles
- Si implique le voisinage ou un tier -> constat amiable

### Incendie / explosion
- Date du sinistre
- Avertir immédiatement les pompiers.
- Déclaration de sinistre sous 5 jours.
- Porter plainte si suspicion criminelle.
- Fournir inventaire des biens détruits (photos, factures).

Checklist:
- Date du sinistre
- Description du sinistre
- Inventaire des biens détruits
- Photos/vidéos des biens détruits
- Factures des biens détruits

*note: on ignorera si l'assuré à porter plainte car cette information n'est pas nécessaire pour la validation et l'étude du dossier.*

### Vol, cambriolage, vandalisme
- Date du sinistre
- Dépôt de plainte sous 24h.
- Déclaration sous 2 jours ouvrés.
- Inventaire des biens volés (factures, photos, garanties).

Checklist:
- Date du sinistre
- Description du sinistre
- Procès-verbal de police
- Inventaire des biens volés
- Photos/videos des biens si possible
- Facture des biens si possible
- Garanties des biens si possible

## Agent IA Validation
## Agent IA Expertise

# Point technique
- Préférant travailler en local, je reste sur le modèle plus léger `mistral-7b-Instruct`. Avec l'utilisation de `ChatLlamaCpp` me permettant d'alterner au besoin mes postes de travail entre Mac et Windows.
- Le chargement du modèle se fait dans un script séparé `llm.py` et son chemin est géré via le fichier `.env` pour plus de flexibilité.