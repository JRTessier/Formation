import asyncio
import secrets
import functools

from typing_extensions import TypedDict
from agent_declaration import recevoir_declaration
from langgraph.types import interrupt, Command
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from llm import load_llm
from datetime import date

class DeclarationState(TypedDict):
    message: str
    resultat: dict | None
    date_reception: str

# --- Noeuds ---
async def _node_recevoir(llm, state: DeclarationState) -> DeclarationState:
    """Appelle l'agent Déclaration sur le message."""
    state["resultat"] = await recevoir_declaration(llm, state["message"])
    return state

def _node_demander_complement(state: DeclarationState) -> DeclarationState:
    """
    Met le processus en pause en attendant la réponse de l'assuré, lorsqu'il manque un ou des éléments obligatoires dans le dossier.
    """
    elements_manquants = state["resultat"]["elements_manquants"]
    reponse_assure = interrupt(
        {
            "elements_manquants": elements_manquants,
            "message_a_envoyer": (
                "Merci de compléter votre déclaration avec les éléments suivants : " + ", ".join(elements_manquants)
            ),
        }
    )
    state["message"] = state["message"] + "\n\n" + reponse_assure
    return state

# Aiguillage après node_recevoir
def _transition_apres_reception(state: DeclarationState) -> str:
    if state["resultat"]["complet"]:
        return "end"
    return "demander_complement"

# Construction de l'agent
def build_graph_declaration(llm, checkpointer): # on passe llm ici en paramètre pour garder plus de flexibilité sur l'utilisation du modèle.
    """Construit le graphe de l'agent Declaration (reception et boucle Human-in-the-Loop)"""
    graph_builder = StateGraph(DeclarationState)

    graph_builder.add_node("recevoir", functools.partial(_node_recevoir, llm)) # impossible d'utiliser une fonction lambda ici car automatiquement reconnue comme synchrone.
    graph_builder.add_node("demander_complement", _node_demander_complement)

    graph_builder.add_edge(START, "recevoir")
    graph_builder.add_conditional_edges(
        "recevoir",
        _transition_apres_reception,
        {"demander_complement": "demander_complement", "end": END},
    )
    graph_builder.add_edge("demander_complement", "recevoir")

    return graph_builder.compile(checkpointer=checkpointer)

# Traitement de l'entrée de la declaration
async def init_declaration(message_initial: str, db_path: str = "checkpoints.db") -> str:
    """Initialisation d'une nouvelle déclaration à partir du message de l'assuré."""
    async with AsyncSqliteSaver.from_conn_string(db_path) as checkpointer:
        llm = load_llm()
        graph = build_graph_declaration(llm, checkpointer)

        thread_id = secrets.token_hex(8)
        config = {"configurable": {"thread_id": thread_id}}

        etat_initial = {
            "message": message_initial,
            "resultat": None,
            "date_reception": date.today().isoformat(),
        }
        resultat = await _execution_graph(graph, etat_initial, config)

    resultat["thread_id"] = thread_id
    return resultat

async def update_declaration(thread_id: str, reponse_assure: str, db_path: str = "checkpoints.db") -> None:
    """Reprend une déclaration interrompue, une fois la réponse de l'assuré reçue."""
    async with AsyncSqliteSaver.from_conn_string(db_path) as checkpointer:
        llm = load_llm()
        graph = build_graph_declaration(llm, checkpointer)

        config = {"configurable": {"thread_id": thread_id}}
        return await _execution_graph(graph, Command(resume=reponse_assure), config)

# Execution du graph defini dans les fonctions de traitement et Human-in-the-Loop
async def _execution_graph(graph, entree, config: dict) -> dict:
    dernier_step = None
    async for step in graph.astream(entree, config=config):
        #_afficher_etape_DEBUG(step)
        dernier_step = step

    node_name = list(dernier_step.keys())[0]
    if node_name == "__interrupt__":
        return {
            "status": "en_attente",
            "interruption": dernier_step["__interrupt__"][0].value,
        }
    return {
        "status": "complet",
        "resultat": dernier_step[node_name]["resultat"],
        "date_reception": dernier_step[node_name]["date_reception"],
    }

# DEBUG
def _afficher_etape_DEBUG(step: dict) -> None:
    """Affichage pour le developpement uniquement"""
    node_name = list(step.keys())[0]
    if node_name == "__interrupt__":
        print("[INTERRUPTION]", step["__interrupt__"][0].value)
    else:
        print(f"[{node_name}]", step[node_name].get("resultat"))

# TEST

"""async def main():
    declaration_test_incomplete = (
        "Mon PC a explosé et mon bureau a pris feu ! Regardez la photo ! En plus il était tout neuf. Voici l'inventaire des biens détruits:"
        "- PC gamer AMD Ryzen 5 5500"
        "- televiseur sony 32 pouces"
        "- iphone 11"
        "- lampe de bureau ikea"
        "Et les factures ci jointes[Pièce jointe : PC.png] [Pièce jointe : PC_facture.png] [Pièce jointe : portable_facture.png] [Pièce jointe : TV_facture.png]"
    )

    print ("--- Démarrage ---")
    resultat = await init_declaration(declaration_test_incomplete)
    print("Statut :", resultat["status"])

    if resultat["status"] == "en_attente":
        print("\n--- Reprise (simulation de la réponse de l'assuré) ---")
        resultat = await update_declaration(
            resultat["thread_id"],
            "ça s'est passé le 10 septembre.",
        )
        print("Statut :", resultat["status"])
    else:
        print("Dossier déjà complet.")

if __name__ == "__main__":
    asyncio.run(main())"""