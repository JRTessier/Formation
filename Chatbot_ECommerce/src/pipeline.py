from db_request import get_order_by_id, format_order_status
from extractor import extract_order_id
from client_intention import classify_intention

def answer_question(llm, question: str) -> str:
    intention = classify_intention(llm, question)

    # Cas intention est une aide
    if intention == "aide":
        return ("Je transmets votre demande à un conseiller qui va prendre le relais. Merci de patienter un instant...")

    # Cas intention est une info
    order_id = extract_order_id(llm, question)

    if order_id is None:
        return "Je n'ai pas identifié de numéro de commande dans votre question. Pouvez-vous préciser ?"

    order = get_order_by_id(order_id)

    if order is None:
        return f"Aucune commande n°{order_id} n'a été trouvée."

    return format_order_status(order)