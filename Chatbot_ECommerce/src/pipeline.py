from db_request import get_order_by_id, format_order_status
from extractor import extract_order_id
from client_intention import classify_intention
from router import is_sav_related

def answer_question(llm, question: str, user_id: int) -> str:

    # Cas hors-sujet (router)
    if not is_sav_related(llm, question):
        return "Je ne peux répondre qu'aux questions liées à vos commandes."

    intention = classify_intention(llm, question)

    # Cas intention est une aide (client_intention)
    if intention == "aide":
        return ("Je transmets votre demande à un conseiller qui va prendre le relais. Merci de patienter un instant...")

    # Cas intention est une info (client_intention + extractor)
    order_id = extract_order_id(llm, question)

    if order_id is None:
        return "Je n'ai pas identifié de numéro de commande dans votre question. Pouvez-vous préciser ?"

    order = get_order_by_id(order_id, user_id) # user_id ici permet de bloquer les tentatives d'injections

    if order is None:
        return f"Aucune commande n°{order_id} n'a été trouvée pour votre compte."

    return format_order_status(order)