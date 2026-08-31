# Brief
Afin d'optimiser les délais de prise en charge et de résolution des sinistres, une grande compagnie d'assurance souhaite mettre en place une solution reposant sur des agents IA spécialisés, capables d'accompagner l'assuré dans sa déclaration et d'automatiser une partie des étapes de gestion du dossier.

Dans le cadre de ce projet Hands-On, nous nous concentrerons uniquement sur les trois sinistres suivants.

- Dégâts des eaux.
- Incendie / explosion.
- Vol, cambriolage, vandalisme.

# Architecture du pipeline

L'architecture s'inspire d'un pattern Plan-and-Execute. Mais ici le plan étant déjà fixé par le processus de gestion des sinistres, nous préfèrerons ne pas déléguer la tâche de plannification à un LLM qui laisserait la porte ouverte à d'éventuelles erreurs et ajouterait un appel inutile.

C'est donc `orchestration.py` qui s'occupe de dérouler le pipeline ci-dessous.
A noter que nous implémentons également une étape Human-in-the-Loop gérée par l'agent IA Déclaration afin de fluidifier l'expérience de l'utilisateur.
```
Entrée de l'utilisateur
        |
        |
        v
Agent IA Déclaration
        |
        |   si incomplet
        |<-----------------> Human-in-the-loop (géré par l'agent lui-même)
        v
Agent IA Validation
        |
        |   si non conforme
        |------------------> Rejet
        v
Agent IA Expertise
        |
        |
        v
Transmission d'un rapport à un conseiller
```


# Trois Agents IA

## Agent IA Déclaration
L'agent IA Déclaration guide l'assuré dans la saisie de sa déclaration (photos, documents, délais légaux).

Ce qui est attendu de la part de l'assuré :

### Dégâts des eaux :
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

### Incendie / explosion :
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

*note: on ignorera si l'assuré a porté plainte car cette information n'est pas nécessaire pour la validation et l'étude du dossier.*

### Vol, cambriolage, vandalisme :
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

<br>
Via un modèle LLM, l'agent s'assure que le dépôt de déclaration de l'assuré contient bien les éléments requis.
S'il manque un élément, le dépôt se met en pause et attend un complement d'information de la part de l'assuré avant de pouvoir être finalisé (Human-in-the-Loop).

## Agent IA Validation

L'agent IA Validation traite les données de la déclaration afin de vérifier leur conformité.

### Date légal de dépôt de déclaration :

Un modèle LLM extrait la date du sinistre à partir du message original de l'assuré.<br>
La fonction `verifier_delai()` calcule le delai écoulé entre la date du sinistre et celle de la réception de la déclaration. Puis elle vérifie que ce delai est conforme avec les obligations prévues dans le contrat et propre à chaque type de sinistre.

### Conformité des photos :

Un modèle VLM analyse les photos fournie afin de déterminer si elles correspondent bien au type de sinistre déclaré.

### Decision :

Si tous les éléments sont conforme, le dossier est considéré comme valide, il sera tranmis à l'Agent IA Expertise (via l'orchestration).
Si des éléments ne sont pas conforme, le dossier est rejeté et l'assurée sera notifié.

---
Note:<br>
*Par manque de données dans les fichiers d'exemples de pièces jointes, ne sont pas traités les cas de divers documents administratifs (factures, PV, garanties...)*

## Agent IA Expertise

### Gravité :

Un modèle VLM analyse les images fournies afin de déterminer la gravité du sinistre selon trois niveaux : léger, modéré, grave.

Si le dossier contient plusieurs photos, on gardera la gravité la plus élevée répérée sur l'ensemble des photos.

### Montant de l'indemnisation :

Une fourchette du montant de l'indemnisation est calculée à partir du coût total estimé et de la franchise et selon les plafonds définis dans le contrat de garanties.

On utilise un pourcentage dépendant de la gravité et le plafond défini pour estimer le coût total. Le résultat reste approximatif et constitut uniquement un aperçu d'un montant qui sera à évaluer précisément par un expert humain.

A noter qu'aucun appel à un modèle LLM ou VLM n'est nécessaire pour cette étape.

### Rapport :

Un rapport complet des éléments définis ci-dessus est généré par un modèle LLM. Il consitue ainsi un premier aperçu du dossier avec les premières estimations avant qu'un conseillé humain ne prenne le relais.

## Orchestration :

C'est au niveau de l'orchestration que s'effectue l'identification du prestataire. En effet ce choix dépend à la fois du type de sinistre défini dans l'Agent IA Déclaration et de la gravité des dégâts définie dans l'Agent IA Expertise.<br>
Ce choix n'est pas déterminé par un appel llm, uniquement déduit logiquement à partir des données des deux agents IA.

# Evaluation des agents

Un golden set est mis en place afin d'évaluer les performances des agents IA.<br>
A la fin de l'évaluation `evaluation.py` consigne l'ensemble des résultats dans le fichier `goldent_dataset_resultats.csv`.

## Agent IA Déclaration :

On évalue le type de sinistre ainsi que la complétude du dossier. On établit un F1-score à partir de ces deux valeurs.<br>
La fonction `evaluer_declaration()` s'appuie directement sur les résultats des fonctions `recevoir_déclaration()` et `_caluculer_completude()` de l'agent IA Déclaration en comparaison avec le golden set.

## Agent IA Validation :

On évalue la justesse de la date du sinistre extraite ainsi que le delai du depot de la declaration.
La fonction `evaluer_validation()` s'appuie directement sur les résultats des fonctions `extraire_date_sinistre()` et `verifier_delai` de l'agent IA Validation en comparaison avec le golden set.

## Agent IA Expertise :

*Explicitement exempté d'évaluation automatique par le brief.*

## Orchestration :

Le choix du prestataire ne necessite aucune évaluation pertinente car ce résultat dépend directement des données `type_sinistre` fournis par l'agent IA Déclaration et `gravite` fournis par l'agent IA Expertise.

# Point technique
- Préférant travailler en local, je reste sur le modèle plus léger `mistral-7b-Instruct`. Avec l'utilisation de `ChatLlamaCpp` me permettant d'alterner au besoin mes postes de travail entre Mac et Windows.
- Le chargement du modèle se fait dans un script séparé `llm.py` et son chemin est géré via le fichier `.env` pour plus de flexibilité.
- A l'approche de l'intégration du VLM l'architecture `llama.cpp` divergeante des exemples du notebook (`transformers`+`bitsandbytes` s'appuie su CUDA, non compatible Mac) exige de passer par un mmproj (encoder CLIP). `Llama 3.2 Vision` utlisé dans les exemples n'est pas non plus compatible avec `llama.cpp`, ce qui nous pousse à utiliser `Llava`.
- Le tic de comptage et de listes numérotés est un défaut connu de `LlaVa` à prendre en compte dans le prompt, le modèle a tendance à compter des éléments lorsqu'on lui demande une description.
- Nouveau test de modèle avec `Moondream2` (M87 Labs, Apache-2.0) utilisé pour la vision, suite à un bug reproductible de `Llava15ChatHandler` dans `llama-cpp-python 0.3.35`
- Suite à l'échec avec `Moondream2` (bug similaire, résultats décevants), il a été décidé d'avancer sur la construction des agents et de l'orchestration avant de tester un nouveau VLM dans une sandbox. L'architecture du projet permet de modifier rapidement les modèles utilisés.
- Deux versions de `vlm.py`. Une version `vlm_UNIVERSAL.py` utilisant `Llava` et fonctionnant sur Mac et Windows. Une version `vlm_CUDA.py` non compatible Mac utilisant `Llama 3.2 Vision` en reprenant l'architecture présentée dans les notebook de la formation.<br>
Supprimer le suffixe pour activer l'une ou l'autre.