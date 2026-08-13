"""
Découpage des documents PDF, embedding et stockage mémoire avec FAISS
"""

import glob

from langchain_community.document_loaders import PyPDFLoader, PyMuPDFLoader

# Initialisation de la liste qui va contenir tous les documents chargés
documents = []

# On parcourt tous les PDF du dossier pour les charger un par un
for file in glob.glob("data/DIC/*.pdf"):
    try:
        loader = PyPDFLoader(file)  # Retourne une liste de documents (un par page)
        documents += loader.load()
    except Exception:
        # PyPDFLoader (basé sur pypdf) est strict sur la structure du PDF et peut échouer
        # sur certains fichiers pourtant valides. On retente alors avec PyMuPDFLoader,
        # plus tolérant, avant d'abandonner ce fichier.
        try:
            loader = PyMuPDFLoader(file)
            documents += loader.load()
        except Exception as e:
            # On n'affiche une erreur que si les deux loaders ont échoué
            print(f"Erreur survenue pour le fichier '{file}' : {e}")

# parsing

# chunking

# embedding
# On génère 10,000 vecteurs aléatoires de taille 200
data = np.random.rand(10000, 200).astype("float32")

# On initialise cet index et on y ajoute les vecteurs
index = faiss.IndexFlatL2(data.shape[1])
index.add(data)