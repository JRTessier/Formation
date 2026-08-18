"""
Placer le fichier dans le dossier src/ avant de lancer un test
"""

from db_request import get_order_by_id, format_order_status
from llm_setup import build_llm
from extractor import extract_order_id
from pipeline import answer_question

# --- TEST 1 ---
#print(get_order_by_id(1))

# --- TEST 2 ---
#order = get_order_by_id(2)
#print(format_order_status(order))

# --- TEST 3 ---
#llm = build_llm()

#print(extract_order_id(llm, "où en est ma commande numéro 12 ?"))
#print(extract_order_id(llm, "quel est le statut de ma première commande"))
#print(extract_order_id(llm, "bonjour, je m'appelle 9"))
#print(extract_order_id(llm, "ça fait 2 ans que j'attends ma commande n°27 !"))

# --- TEST 4 ---
llm = build_llm()

print(answer_question(llm, "où en est ma commande numéro 12 ?"))
print(answer_question(llm, "quel est le statut de ma première commande"))
print(answer_question(llm, "bonjour, je m'appelle 9"))
print(answer_question(llm, "ça fait 2 ans que j'attends ma commande n°27 !"))
print(answer_question(llm, "je n'ai pas reçu ma commande 999"))
print(answer_question(llm, "bonjour !"))