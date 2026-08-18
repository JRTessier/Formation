import json
import re
from langchain_core.prompts import ChatPromptTemplate

ROUTER_PROMPT = ChatPromptTemplate.from_messages([
    ("human",
     """
        Tu détermines si une question concerne STRICTEMENT le service client d'un site e-commerce :
        suivi de commande, statut de livraison, annulation/modification de commande, réclamation sur une commande reçue.

        Toute question qui ne mentionne PAS explicitement une commande, une livraison, un achat ou un problème
        avec un produit commandé doit être classée comme NE concernant PAS le SAV, même si elle semble anodine
        ou polie. Les questions générales de culture, d'actualité, de conversation, ou toute autre demande non
        liée à une commande doivent être rejetées.

        Réponds UNIQUEMENT avec un objet JSON, sans texte avant ou après :
        {{"sav": true or false}}

        Exemples :
        Question : "où en est ma commande 12 ?"
        Réponse : {{"sav": true}}

        Question : "je veux annuler ma commande 12"
        Réponse : {{"sav": true}}

        Question : "ma commande est arrivée cassée"
        Réponse : {{"sav": true}}

        Question : "quelle est la couleur du cheval blanc d'Henri IV ?"
        Réponse : {{"sav": false}}

        Question : "qui est Maurice Moss ?"
        Réponse : {{"sav": false}}

        Question : "raconte-moi une blague"
        Réponse : {{"sav": false}}

        Question : "écris-moi un poème"
        Réponse : {{"sav": false}}

        Question : "peux-tu m'aider à réviser mon examen de maths ?"
        Réponse : {{"sav": false}}

        Question : "un petit 5 à 7 ?"
        Réponse : {{"sav": false}}

        Question : "quel temps fait-il aujourd'hui ?"
        Réponse : {{"sav": false}}

        Question : "comment tu t'appelles ?"
        Réponse : {{"sav": false}}

        Question : {question}
     """
    ),
])

def is_sav_related(llm, quesion: str) -> bool:
    chain = ROUTER_PROMPT | llm
    response = chain.invoke({"question": quesion})
    raw = response.content.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r'\{.*?\}', raw, re.DOTALL)
        data = json.loads(match.group()) if match else {}

    return data.get("sav", False) # False par défaut pour rejeter si ambiguë