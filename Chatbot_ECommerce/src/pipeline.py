from db_request import get_order_by_id, format_order_status
from extractor import extract_order_id
from user_intention import classify_intention
from router import is_sav_related
from contextualizer import contextualize_question
from langchain_core.messages import HumanMessage, AIMessage

def answer_question(llm, question: str, user_id: int, chat_history: list) -> str:

    standalone_question = contextualize_question(llm, chat_history, question)

    # Cas hors-sujet (router)
    if not is_sav_related(llm, standalone_question):
        return "Je ne peux répondre qu'aux questions liées à vos commandes."
    else:
        intention = classify_intention(llm, standalone_question)

        # Cas intention est une aide (client_intention)
        if intention == "aide":
            answer = "Je transmets votre demande à un conseiller qui va prendre le relais. Merci de patienter un instant..."
        else:
            # Cas intention est une info (client_intention + extractor)
            order_id = extract_order_id(llm, standalone_question)

            if order_id is None:
                answer = "Pouvez-vous me fournir le numéro de votre commande ?"
            else:
                order = get_order_by_id(order_id, user_id) # user_id ici permet de bloquer les tentatives d'injections
                answer = (
                    format_order_status(order)
                    if order
                    else f"Aucune commande n°{order_id} n'a été trouvée pour votre compte."
                )

    chat_history.append(HumanMessage(content=question))
    chat_history.append(AIMessage(content=answer))

    return answer