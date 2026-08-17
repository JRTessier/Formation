# Développement d'un agent conversationnel RAG sur la documentation financière interne

## Objectif

Construire un assistant de chat afin que les équipes d'un département ALM puisse engager des conversations avec l'assistant, notamment pour retrouver très facilement des informations éparpillées dans l'ensemble des DIC à disposition.


## Rappel des contraintes
- Aucun outil tiers ou API cloud : tout tourne en local pour des raisons de confidentialités.
- Privilégier l'utilisation de modèles open weight (Mistral, Llama)
- Sourcer systématiquement les réponses
- Mode conversationnelle avec historique des précédents messages
- Stockage local des vecteurs d'embedding (ChromaDB ou FAISS)
- F1 BERT Score > 60% sur le dataset d'évaluation fourni


## Déroulement de la conception

### Etape 1 :
Création du fichier `ingestion.py` qui inclu parsing PDF, chunking, embedding et stockage FAISS des vecteurs dans le dossier `vectorstore/`

*Le fichier ayant été ajusté à une étape ultérieur, le fichier ingestion_Etape1.py correspond à la version directment issue de l'étape 1 avant modifications.*

### Etape 2 :
Création du fichier `rag_pipeline.py` qui inclu retriever, LLM, sourcing et mémoire conversationnelle.

*Le fichier ayant été ajusté à une étape ultérieur, le fichier rag_pipeline_Etape2.py correspond à la version directment issue de l'étape 2 avant modifications.*

### Etape 3 :
Création du fichier `evaluate.py` dont résulte le F1 Bert Score appliqué au dataset d'évaluation fourni.

Révision du prompt dans `rag_pipeline.py`.

- Lors de l'évaluation j'ai découvert une erreur d'utilisation du rôle `"system"` dans le prompt. `Mistral-7B-Instruct` ne supporte pas le rôle `"system"` et était silencieusement ignoré. Le contenu initialement prévu pour `"system"` a été déplacé dans le rôle `"human"`.


## Choix techniques

### Extraction PDF :
J'ai choisi d'utiliser `PyMuPDFLoader` en priorité car PyPDFLoader s'est avéré avoir une mauvaise gestion des accents et carcatères spéciaux.

### Embedding :
`paraphrase-multilingual-mpnet-base-v2`, modèle open weight de HuggingFace qui tourne 100% en local et supporte le français avec de bons résultats.

### Vector store :
J'ai volontairement pris le partie d'utiliser `FAISS` plutôt que ChromaDB afin d'anticiper son usage dans le cadre de mon projet personnel. FAISS faisant partie des propositions technique dans le brief.

### LLM de génération :
`Mistral-7B-Instruct-v0.3-Q4_K_M.gguf`, Open weight qui supporte Mac (Metal) et PC (CUDA) puisque j'alterne mes sessions de travail sur un MAC et un PC.

### Mémoire conversationnelle :
`create_history_aware_retriever` (LangChain), permet de reformuler automatiquement une question ambiguë (contexte dépendant d'échanges précédents) en question autonome à partir de l'historique.


## Résultats de l'évaluation

F1 Bert Score moyen : **70.90%**<br>
Précision moyenne : 67.14%<br>
Rappel moyen : 75.52%<br>


## Notes et observations
- Bon nombre de réponses de `answer.json` semblent tronquées. Et certaines questions de `queries.json` manquent de contexte ("Quel est l'objectif de gestion du FCP décrit dans le document ?"). On peut donc imaginer que le score obtenue est assez cohérent vis à vis du bruit du dataset de référence.
- Une fois que le problème du rôle `"system"` ignoré silencieusement a été corrigé, une seule réponse prenait plus de 2 minutes ! Les logs internes de `ChatLlamaCpp` ont montré que le temps était perdu dans `prompt eval time`, la lecture du prompt. En augmentant la valeur de `n_batch` à 512 (contre 8 par défaut) le gain de temps est considérable.