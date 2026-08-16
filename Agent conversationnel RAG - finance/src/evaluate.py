import json
import random
from pathlib import Path

from bert_score import score as bert_score

import sys
sys.path.append(str(Path(__file__).parent))
from rag_pipeline import build_rag_chain

EVAL_DIR = Path("data/dataset_eval")

# --- Chargement du datasel d'évaluation ---
with open(EVAL_DIR / "queries.json", encoding="utf-8") as f:
    queries = json.load(f)
with open(EVAL_DIR / "answers.json", encoding="utf-8") as f:
    answers = json.load(f)

# --- Echantillon de questions ---
sample_ids = list(queries.keys())
# sample_ids = sample_ids[:len(sample_ids) //64] # Test sur un échantillion réduit
SAMPLE_SIZE = len(sample_ids)

# --- Mise en route du pipeline RAG ---
print ("Mise en route du pipeline RAG")
rag_chain = build_rag_chain()

# --- Génération des réponses ---
predictions = []
references = []

for i, uuid in enumerate(sample_ids, 1):
    question = queries[uuid]
    expected_answer = answers[uuid]

    print(f"[{i}/{SAMPLE_SIZE}] {question}")
    response = rag_chain.invoke({"input": question, "chat_history": []})
    generated_answer = response["answer"]

    predictions.append(generated_answer)
    references.append(expected_answer)

    print(f" Attendu : {expected_answer[:100]}...")
    print(f" Généré : {generated_answer[:100]}...\n")

# --- Calcul du F1 Bert Score ---
print("F1 Bert Score :")
Precision, Rappel, F1 = bert_score(predictions, references, lang="fr", verbose=True)

print(f"\n=== Résultats sur {SAMPLE_SIZE} questions ===")
print(f"F1 BERT Score moyen : {F1.mean().item():.2%}")
print(f"Précision moyenne   : {Precision.mean().item():.4f}")
print(f"Rappel moyen        : {Rappel.mean().item():.4f}")