# Templates de prompts

Le pipeline se base sur l'utilisation de quatre prompts avec chacun leur rôle respectif.
`CONTEXTUALIZE_PROMPT`,`ROUTER_PROMPT`, `INTENTION_PROMPT`, `EXTRACTION_PROMPT`

## Architecture générale du pipeline (`pipeline.py`)

```
    Question utilisateur
            |
            v
    [1] CONTEXTUALIZE_PROMPT
        reformulation en question autonome
            |
            v
    [2] ROUTER_PROMPT
        routage sémantique : est-ce une question SAV ?
            |
            v (if True)
    [3] INTENTION_PROMPT
        classification d'intention : l'utilisateur recherche une info ou une aide ?
            |
            v (if "info")
    [4] EXTRACTION_PROMPT
        Extraction du numéro de commande à partir de la question utilisateur.
            |
            v
    Requête SQL
```

## 1. Contextualisation de la question

`CONTEXTUALIZE_PROMPT`dans `contextualizer.py`

On commence par reformuler la question de l'utilisateur en utilisant le context de l'historique de conversation. Ainsi on s'assure une fluidité pour l'utilisateur. (ex: *"où en est ma commande ?", "pouvez-vous me fournir le numéro de votre commande?", "n°2", etc...*)<br>
La question ne passe pas par le prompt si l'historique est vide.

## 2. Routage sémantique

`ROUTER_PROMPT`dans `router.py`

On défini si la question de l'utilisateur est légitime. Est-ce que sa question relève du SAV ?
Il s'agit du premier filtre avant tout engagement dans une autre étape.<br>
<br>
Le prompt répond un objet JSON true or false :<br>
`{"sav": true or false}`<br>

La fonction `is_sav-related()` traite la réponse :
- Si `True`, la question passe et est transmise à `INTENTION_PROMPT`
- Si `False`, on rejète la question

Par défaut la fonction retourne `False`, en cas d'échec de parsing JSON, dans le doute on préfère refuser la question que de laisser passer une question hors-sujet.

**Note de conception :**
<br>
Ce prompt a fait l'objet d'itérations successives à la suite de faux positifs identifiés pendant les tests :
- Certaines questions hors-sujet parvenaient à être classée `true`. Il a fallu ajouter des consignes négative explicite et des exemples de Q/R variés.
- La question "quel est le score du match, 3 à 1 ?" était classé `true`. La piste de confusion numérique explorée fut écartée lorsque d'autres questions comprenant divers pièges numériques se classaient correctement. La solution est venu de l'ajout du terme "actualité" dans la consigne.

## 3. Classification d'intention

`INTENTION_PROMPT`dans `user_intention.py`

La question de l'utilisateur est examinée pour définir s'il s'agit d'une demande d'information (qui peut être traitée directement par le chatbot) ou une demande d'aide.
<br>
<br>
Le prompt répond un objet JSON "info" or "aide" :<br>
`{"intention": "info" or "aide"}`<br>

La fonction `classify_intention()` traite la réponse :
- Si `"info"`, la question passe et est transmise à `EXTRACTION_PROMPT`
- Si `"aide"`, on stoppe la progression, un humain doit prendre le relais

Par défaut la fonction retourne `aide`, en cas d'échec de parsing JSON, dans le doute on préfère rediriger l'utilisateur vers l'aide humaine que de le laisser bloquer dans une recherche d'info sans issue.

## 4. Extraction du numéro de commande

`EXTRACTION_PROMPT`dans `extractor.py`

La question de l'utilisateur est examinée pour en extraire un numéro de commande.
<br>
<br>
Le prompt répond un objet JSON numéro or null :<br>
`{"order_id": <numéro> or null}`<br>

La fonction `extract_order_id()` traite la réponse :
- Si `int` présent, la fonction `get_order_by_id()`(dans `db_request.py`) est appelée, celle-ci effectue la requête SQL et retourne les informations cherchées si elles existent.
- Si `null`, une réponse négative est immédiatement envoyé à l'utilisateur, évitant une recherche SQL ivouée à l'échec.

**Note de conception :**
<br>
Le prompt initial se laissait piéger par des chiffres non liés à une commande (ex: "bonjour, je m'appelle 9"). L'ajout d'un contre-exmple à permis de corriger ce defaut.<br>
A noter que `EXTRACTION_PROMPT` fut le premier créé lors de la conception du pipeline. Donc "bonjour, je m'appelle 9" devrait logiquement échouer au `ROUTER_PROMPT`. Mais en imaginant une question légitime contenant des chiffres parasites (ex: "La commande 32 pour mon fils de 9 ans n'est pas arrivée"), le contre-exemple garde son utilité dans le prompt.
<br><br>

# Choix de conception

## 4 prompts vs 1 prompt ?
Un prompt unique qui fusionnerait contextualisation + routage + intention + extraction réduirait la latence mais augmenterait le risque d'erreurs lié à des confusions entre les différentes catégories. Ici le cadre sav e-commerce exigeant une fiabilité accrue pousse à privilégier l'efficacité plutôt que la rapidité.

## Pourquoi pas text-to-SQL ?

Ici j'ai pris le parti de ne pas utiliser de text-to-SQL. Ne pas laisser de LLM générer du SQL permet de s'assurer qu'aucune manipulation malveillante n'est possible via le prompt.<br>
Dans ce projet le user_id est injecté dès le départ par le code et jamais extrait du texte par le LLM ce qui garanti une bonne sécurité.