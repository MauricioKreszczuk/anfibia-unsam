# Proyecto Anfibia — Cartografía Temática y Recomendador de Notas

Proyecto desarrollado como materia optativa en el marco de la **Licenciatura en Ciencia de Datos (ECyT - UNSAM)**, llevado adelante por **Mauricio Kreszczuk** junto a **Manuel Szewc** y **Natalia Debandi**, integrantes del  **Centro de Inteligencia Artificial Interdisciplinario (CIAI)**, en colaboración con **Revista Anfibia**.

Se realiza una exploración sobre el archivo de publicaciones de la revista (2012–2026), modelado de tópicos y algoritmos de similitud para recomendación de notas.

---

## Estructura del Repositorio

La organización sigue los criterios de reproducibilidad, trazabilidad y resguardo de datos establecidos por el CIAI-UNSAM:

```text
├── data/
│   ├── raw/                 # Volcado SQL original de WordPress [ignorado por Git]
│   ├── processed/           # Corpus curados, lematizados y vocabulario [ignorado por Git]
├── docs/                    # Diccionario de variables, bitácora de decisiones e informe final
│   └── diccionario_columnas.md
├── notebooks/               # Pipeline secuencial de exploración, modelado y evaluación
│   ├── 01_exploracion_y_diagnostico.ipynb
│   ├── 02_limpieza_y_lematizacion.ipynb
│   ├── 03_bow_y_wordclouds.ipynb
│   ├── 04_bertopic_entrenamiento_y_reduccion.ipynb
│   ├── 05_bertopic_outliers_y_evolucion.ipynb
│   ├── 06_auditoria_etiquetas.ipynb
│   └── 07_recomendador_articulos.ipynb
├── outputs/                 # Modelos serializados, métricas y visualizaciones interactivas
├── src/                     # Scripts reproducibles de extracción y generación de recursos
│   ├── extract_posteos_anfibia.py
│   └── stopwords.py
├── requirements.txt         # Dependencias del entorno Python
├── .gitignore               # Reglas de exclusión de datos y artefactos pesados
└── README.md                # Documentación general del proyecto
```

El detalle de todas las variables extraídas y generadas se encuentra documentado en `docs/diccionario_columnas.md`.

---

## Requisitos e Instalación

1. **Crear y activar entorno virtual (Python 3.10+):**
```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/macOS:
source venv/bin/activate

```


2. **Instalar dependencias y modelo lingüístico de spaCy (el modelo necesita descargarse por separado):**
```bash
pip install -r requirements.txt
python -m spacy download es_core_news_md

```



---

## Ejecución

Para reproducir la ejecución completa ejecutar los archivos en este orden:

1. **Extracción y sanitización del dump (`src/extract_posteos_anfibia.py`):**
Procesa por streaming el volcado de la base de datos filtrando únicamente notas publicadas (`post_type == "post"` y `post_status == "publish"`). Remueve etiquetas HTML, *shortcodes* y bloques de Gutenberg, excluye tablas de usuarios/suscriptores y redacta correos electrónicos (`[EMAIL_REDACTED]`). Genera `data/processed/posteos_anfibia.csv`.

1. **Generación de stopwords (`src/stopwords.py`):**
Consolida stopwords generales del español junto con términos editoriales de alta frecuencia (Necesario para la creación de tópicos). Genera `data/processed/stopwords_anfibia.txt`.

1. **Exploración y auditoría inicial (`notebooks/01_exploracion_y_diagnostico.ipynb`):**
Verifica consistencia temporal, distribución de longitudes, taxonomías y completitud de campos.

1. **Curaduría y lematización (`notebooks/02_limpieza_y_lematizacion.ipynb`):**
Filtra notas sin cuerpo textual, descarta versiones republicadas obsoletas (`-N/`), filtra idiomas extranjeros, integra copete y bajada al documento y ejecuta lematización por lotes con `es_core_news_md`. Genera `corpus_anfibia_lematizado.csv`.

1. **Representación Bag-of-Words y nubes de palabras (`notebooks/03_bow_y_wordclouds.ipynb`):**
Construye la matriz documento-término (`CountVectorizer`) y genera visualizaciones léxicas globales y temporales por categoría.

1. **Modelado de Tópicos Híbrido (`notebooks/04_bertopic_entrenamiento_y_reduccion.ipynb`):**
Entrena BERTopic combinando embeddings densos sobre texto natural (`paraphrase-multilingual-MiniLM-L12-v2` + UMAP + HDBSCAN) con representación c-TF-IDF / `KeyBERTInspired` sobre los artículos lematizados. Incluye fusión guiada y reasignación de *outliers* por umbral de similitud coseno ($\ge 0.65$).

1. **Calibración de Misceláneos y Evolución Temporal (`notebooks/05_bertopic_outliers_y_evolucion.ipynb`):**
Consolida los documentos residuales en el Tópico `100`, reordena clústeres por volumen y calcula series temporales (`topics_over_time`) identificando picos históricos y notas representativas.

1. **Auditoría de Taxonomías Editoriales (`notebooks/06_auditoria_etiquetas.ipynb`):**
Evalúa cobertura de `post_tag`, dispersión temática (*Ratio de Fragmentación*), coocurrencia (Índice de Jaccard) y detección híbrida de cuasi-duplicados léxicos y semánticos.

1. **Motor de Recomendación (`notebooks/07_recomendador_articulos.ipynb`):**
Calcula distribuciones suaves de probabilidad temática (`approximate_distribution`) y similitud coseno para rankear artículos similares.

---

## Gobernanza y Resguardo de Datos

En cumplimiento con los *Lineamientos para la Gobernanza de Datos e IA de la UNSAM*:

* El volcado SQL crudo (`data/raw/`) y los datasets derivados (`data/processed/`) se encuentran excluidos del control de versiones mediante `.gitignore`.
* El script de extracción opera bajo el principio de minimización de datos, descartando metadatos técnicos, credenciales o información de usuarios antes de generar cualquier artefacto analítico.

```