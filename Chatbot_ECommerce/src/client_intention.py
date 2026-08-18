import json
import re
from langchain_core.prompts import ChatPromptTemplate

INTENTION_PROMPT = ChatPromptTemplate.from_messages([
    ("human",
     """
        Tu classes une question de client e-commerce selon son intention.

        Deux catégories possibles :
        - "info" : le client cherche une information sur une commande (statut, date de changement de statut). Le bot peut répondre directement depuis la base de données.
        - "aide" : le client demande une action, une modification, une annulation, signale un problème ou une plainte. Un humain doit prendre le relais.

        Réponds UNIQUEMENT avec un objet JSON, sans texte avant ou après :
        {{"intention": "info" or "aide"}}

        Exemples :
        Question : "où en est ma commande 12 ?"
        Réponse : {{"intention": "info"}}

        Question : "je veux annuler ma commande 12"
        Réponse : {{"intention": "aide"}}

        Question : "ma commande est arrivée cassée, c'est inadmissible !"
        Réponse : {{"intention": "aide"}}

        Question : "ma commande n'est toujours pas arrivée !"
        Réponse : {{"intention": "info"}}

        Question : {question}
     """
    ),
])

def classify_intention(llm, question: str) -> str:
    chain = INTENTION_PROMPT | llm
    response = chain.invoke({"question": question})
    raw = response.content.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r'\{.*?\}', raw, re.DOTALL)
        data = json.loads(match.group()) if match else {}

    return data.get("intention", "aide") # retourne aide par défaut
