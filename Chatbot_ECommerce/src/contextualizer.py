from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage

CONTEXTUALIZE_PROMPT = ChatPromptTemplate.from_messages([
    ("human",
     """
        Tu reformules le dernier message d'un client en une question autonome,
        compréhensible sans l'historique de conversation.

        Réponds UNIQUEMENT avec la question reformulée, sans aucun texte avant ou après,
        sans salutation, sans commentaire, sans réponse à la question elle-même.

        Exemple 1 :
        Historique :
        Client: je veux savoir où en est ma commande
        Assistant: Pouvez-vous me fournir un numéro de commande ?
        Dernier message du client : voici le numéro : 32
        Question reformulée : où en est ma commande numéro 32 ?

        Exemple 2 :
        Historique :
        (aucun)
        Dernier message du client : où en est ma commande 5 ?
        Question reformulée : où en est ma commande 5 ?

        Maintenant, à toi :
        Historique :
        {history_text}
        Dernier message du client : {input}
        Question reformulée :
     """
     ),
])

def _format_history(chat_history: list) -> str:
    lines = []
    for msg in chat_history:
        role = "Client" if isinstance(msg, HumanMessage) else "Assistant"
        lines.append(f"{role}: {msg.content}")
    return "\n".join(lines) if lines else "(aucun)"

def contextualize_question(llm, chat_history: list, question: str) -> str:
    if not chat_history:
        return question

    chain = CONTEXTUALIZE_PROMPT | llm
    response = chain.invoke({
        "history_text": _format_history(chat_history),
        "input": question,
    })
    return response.content.strip()