import json
import re
from langchain_core.prompts import ChatPromptTemplate

EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("human",
     """
     Tu extrais des informations depuis une question d'un client à propos d'une commande.

     Réponds UNIQUEMNET avec un objet JSON, sans aucun texte avant ou après, au format suivant :
     {{"order_id": <numéro> or null}}

     Exemples :
     Question : "où en est ma commande numéro 12 ?"
     Réponse : {{"order_id": 12}}

     Question : "bonjour, j'ai perdu 2 commandes'"
     Réponse : {{"order_id": null}}

     Question : "j'ai 3 enfants et ma commande est la 7"
     Réponse : {{"order_id": 7}}

     Question : "bonjour, comment allez-vous ?"
     Réponse : {{"order_id": null}}

     Question : {question}
    """),
])

# --- Structured outup ---
def extract_order_id(llm, question: str) -> int | None:
    chain = EXTRACTION_PROMPT | llm
    response = chain.invoke({"question": question})
    raw = response.content.strip()

    try:
        data = json.loads(raw)
        return data.get("order_id")
    except json.JSONDecodeError:
        match = re.search(r'\{.*?\}', raw, re.DOTALL) # on applique un re.search si le llm a quand même enrobé sa réponse de texte.
        if match:
            try:
                data = json.loads(match.group())
                return data.get("order_id")
            except json.JSONDecodeError:
                pass
        return None