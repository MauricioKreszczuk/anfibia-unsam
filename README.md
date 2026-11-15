# Proyecto Anfibia

Proyecto desarrollado como optativa en el marco de la **Licenciatura en Ciencia de Datos (UNSAM)**. Desarrollado por el **Centro de Inteligencia Artificial Interdisciplinario (CIAI)** junto a **Mauricio Kreszczuk (estudiante LCD)** en colaboración con **Revista Anfibia**.

Se realiza una exploración sobre el archivo de publicaciones de la revista (2012–2026), modelado de tópicos y algoritmos de similitud para recomendación de notas.

---

## Estructura del Repositorio

La disposición del proyecto sigue las recomendaciones de reproducibilidad y resguardo del CIAI-UNSAM:

```text
├── data/
│   ├── raw/                 # Datos originales (.sql, .csv) [ignorado por Git]
│   ├── processed/           # Datasets curados (.parquet, .csv) [ignorado por Git]
├── docs/                    # Diseño, decisiones, informes
├── notebooks/               # Exploración y análisis
├── outputs/                 # Figuras, tableros, resultados
├── src/                     # Scripts auxiliares de extracción y procesamiento
├── requirements.txt         # Entorno 
├── .gitignore               # Reglas de exclusión
└── README.md                # Documentación General

---

Los archivos originales y procesados estan explicados en 
diccionario_columnas.md

---

## ⚙️ Requisitos e Instalación

1. **Entorno virtual:**  
   Se recomienda utilizar Python 3.10 o superior:
   ```bash
   python -m venv venv
   # En Linux/macOS:
   source venv/bin/activate
   # En Windows:
   venv\Scripts\activate

pip install -r requirements.txt

En caso de que no se halla instalado automaticamente:

python -m spacy download es_core_news_md


---


## Flujo de Trabajo (Que orden seguir para reproducir)

El procesamiento del corpus y el modelado se articulan en etapas secuenciales:

1. **Extracción y filtrado del dump (`src/extract_posteos_anfibia.py`):**  
   Lectura por streaming del volcado de la base de datos MariaDB para aislar los artículos editoriales publicados (`post_type == "post"` y `post_status == "publish"`), extrayendo texto limpio, fechas y taxonomías.
2. **Curaduría y lematización (`notebooks/01_exploracion_y_diagnostico.ipynb` y `02.exploracion_limpieza_lematizacion.ipynb`):**  
   Descarte de artículos sin cuerpo de texto, remoción de versiones anteriores republicadas (`-N/`), filtrado por idioma y lematización morfosintáctica en lotes con spaCy (`es_core_news_md`).
3. **Modelado Dinámico de Tópicos (`notebooks/06.6_bertopic_reduccion.ipynb` y `06.6_topico_outlier.ipynb`):**  
   Entrenamiento de la arquitectura híbrida con BERTopic (embeddings contextuales densos con `MiniLM-L12-v2`, reducción con UMAP y agrupamiento con HDBSCAN), reducción iterativa de clústeres y calibración del Tópico 100 para misceláneos.
4. **Auditoría de Taxonomías (`notebooks/07.etiquetas.ipynb`):**  
   Evaluación de la cobertura histórica de `post_tag`, análisis de dispersión mediante el *Ratio de Fragmentación* por tópico y propuesta de normalización léxica y semántica.
5. **Motor de Recomendación (`notebooks/08.recomendacion_articulos.ipynb`):**  
   Cálculo de distribuciones suaves de probabilidad de tópicos (*soft topic distributions*) y aplicación de similitud coseno para obtener el ranking de lecturas afines.