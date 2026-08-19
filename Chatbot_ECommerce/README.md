# Création d'un assistant de service client personnalisé

## Objectif

Mettre en place un assistant de chat automatisé capable de répondre aux questions des utilisateurs concernant le statut de leurs commandes.  Le bot doit fournir des réponses rapides et précises aux clients tout en réduisant la charge de travail des agents du service client.


## Rappel des contraintes
- Le bot sera en communication avec un utilisateur donné authentifié avec son adresse email, nom et prénom.
- On ne considérera que des questions liées aux commandes déjà passées.
- Les prompts devront être capables d'éviter les injections.
- Implémenter du routage sémantique en amont de la requête afin d'éviter de router la demande vers le LLM en cas de question qui ne concerne pas directement un problème service client.
- Le bot peut fournir une information sur une commande en cours ou passée si celle-ci est disponible dans la base SQL.
- Si le client souhaite obtenir de l'aide sur une commande en cours ou passée, il faudra indiquer qu'un humain va prendre le relais dans la conversation.


## Déroulement de la conception

### Etape 1 : récupération des informations

- Création du fichier `db_request.py` qui inclu la requête SQL et le formatage de la réponse en langage naturel.
- Création du fichier `extractor.py` qui inlcu `EXTRACTION_PROMPT` permettant d'extraire un numéro de commande de la question de l'utilisateur.
- Création du fichier `llm_setup.py` mettant en place le modèle llm (Mistral-7B-Instruct-v0.3-Q4_K_M.gguf), j'utilise ici le même modèle que pour le projet précédent d'Agent conversationnel RAG 
- Création du fichier `pipeline.py` permettant de tester un premier flux :<br>
*question > `EXTRACTION_PROMPT` > requête SQL > réponse*

### Etape 2 : comportement du bot

- Création du fichier `user_intention.py` qui inclu `INTENTION_PROMPT` permettant de classer la demande de l'utilisateur entre info géréé par le bot ou aide redirigée vers un humain.
- Mise à jour du fichier `pipeline.py` pour tester le flux :<br>
*question > `INTENTION_PROMPT` > `EXTRACTION_PROMPT` > requête SQL > réponse*

### Etape 3 : protection des données et routage sémantique

- Création du fichier `router.py` qui inclu `ROUTER_PROMPT` permettant de classer la question de l'utilisateur entre hors-sujet ou relatif au sav.
- Mise à jour du fichier `db_request.py` pour inclure le `user_id` comme clé de sécurité à la requête SQL.
- Mise à jour du fichier `pipeline.py` pour injecter le `user_id` et tester le flux complet :<br>
*question > `ROUTER_PROMPT` > `INTENTION_PROMPT` > `EXTRACTION_PROMPT` > requête SQL > réponse*

### Etape 4 : Contextualisation de la question via l'historique de conversation

- Création du fichier `contextualizer.py` qui inlcu `CONTEXTUALIZE_PROMPT`permettant de reformuler le dernier message de l'utilisateur en question autonome à partir de l'historique de conversation.
- Mise à jour du fichier `pipeline.py` pour inclure cette étape de contextualisation et maintenir l'historique de conversation à jour.
- Test du nouveau flux :<br>
*question > `CONTEXTUALIZE_PROMPT` > `ROUTER_PROMPT` > `INTENTION_PROMPT` > `EXTRACTION_PROMPT` > requête SQL > réponse*

## Choix et templates de prompts :

Voir le document `PROMPTS_TEMPLATES.md`