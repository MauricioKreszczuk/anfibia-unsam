# Estructura de Datos para Streamlit

Este directorio almacena los datos consolidados y precalculados requeridos para la ejecución del dashboard (`notebooks/informe/`). 

No trabajamos con normalización de tablas al ser datos de una cantidad acotada de filas, priorizando la lectura directa y la velocidad de carga.

---

## 1_Articulos.py

* **`category_counts.csv`**
  * **Qué es:** Conteo agregado de artículos por categoría editorial normalizada.
  * **Uso:** Tablas resumen y gráfico horizontal de volumen por categoría.

* **`bow_vocabulary.csv`**
  * **Qué es:** Vocabulario completo consolidado y lematizado con métricas de frecuencia.
  * **Columnas:** `term`, `document_frequency`, `term_frequency`.
  * **Uso:** Gráfico del Top 20 de términos más frecuentes y buscador de palabras clave.

* **`wordclouds_categoria_index.csv`**
  * **Qué es:** Índice relacional entre cada categoría editorial y su correspondiente archivo PNG generado.
  * **Columnas:** `category`, `path`, `filename`.

* **`wordclouds_categoria_periodo_index.csv`**
  * **Qué es:** Índice de nubes de palabras segmentadas por categoría y período temporal con estadística suficiente.
  * **Columnas:** `category`, `period`, `documents`, `tokens_after_stopwords`, `unique_terms_after_stopwords`, `path`, `filename`.

* **`wordclouds_categoria_global/` (Directorio)**
  * **Qué es:** Archivos de imagen PNG de las nubes de palabras por categoría histórica.

* **`wordclouds_categoria_periodo/` (Directorio)**
  * **Qué es:** Archivos de imagen PNG de las nubes de palabras segmentadas por año/ventana temporal.

---

## 2_Topicos.py

* **`topicos_info.csv`**
  * **Qué es:** Ficha técnica centralizada de los tópicos extraídos por el modelo BERTopic híbrido.
  * **Columnas:** `Topic`, `Name`, `Docs`, `% Corpus`, `Coherencia_NPMI`, `Articulos_Representativos`, `Tagline_Representativo`, `URL_Articulo`.
  * **Uso:** Tabla general interactiva, métricas de volumen, palabras clave y links al artículo más cercano al centroide de cada tema.

* **`graficos/` (Directorio de HTMLs interactivos)**
  * **`01_barchart_topicos.html`:** Relevancia de términos c-TF-IDF para los tópicos principales.
  * **`02_evolucion_topicos_completa.html`:** Evolución temporal de publicaciones por tópico con picos históricos y notas coyunturales destacadas.
  * **`03_espacio_documentos.html`:** Proyección UMAP 2D del espacio semántico de notas coloreadas por tópico.

---

## 3_Etiquetas.py

* **`tags_vs_categorias.csv`**
  * **Qué es:** Tabla desanidada que vincula cada artículo con sus etiquetas y categorías asignadas.
  * **Columnas:** `doc_id`, `ID`, `source_url`, `title_text`, `post_year`, `categoria_normalizada`, `tag`.
  * **Uso:** Alimenta el buscador de notas por etiqueta, el heatmap de etiquetas vs. categorías y las donas temporales por año.

* **`tag_counts.csv`**
  * **Qué es:** Catálogo de frecuencias de etiquetas únicas calculado directamente sobre `tags_vs_categorias.csv`.
  * **Columnas:** `tag`, `frecuencia`.
  * **Uso:** Tabla del Top 100 de etiquetas más utilizadas y opciones del menú desplegable del buscador.

* **`tags_vs_topicos.parquet`**
  * **Qué es:** Relación columnar compacta y optimizada entre artículos, etiquetas y tópicos.
  * **Columnas:** `tag`, `topic_name`, `doc_id`.
  * **Uso:** Renderizado reactivo del heatmap interactivo de Tópicos vs. Etiquetas.

* **`tags_fusiones_automaticas.csv`**
  * **Qué es:** Auditoría morfológica y sintáctica de etiquetas redundantes con alta certeza técnica (diacríticos/tildes, singulares/plurales por lematización y similitud léxica/semántica extrema).
  * **Columnas:** `Tag Variante`, `Frecuencia Variante`, `Tag Canónico`, `Frecuencia Canónico`, `Similitud Léxica`, `Es Diacrítico`, `Mismo Lema`, `Similitud Semántica`.

* **`tags_revision_manual.csv`**
  * **Qué es:** Pares de etiquetas con similitud semántica o léxica cercana que requieren supervisión editorial humana antes de fusionarse.
  * **Columnas:** `Tag Variante`, `Frecuencia Variante`, `Tag Canónico`, `Frecuencia Canónico`, `Similitud Léxica`, `Es Diacrítico`, `Mismo Lema`, `Similitud Semántica`.

* **`tags_solapamiento_prob_topicos.csv`**
  * **Qué es:** Pares de etiquetas con perfiles contextuales coincidentes calculados vía similitud coseno sobre distribuciones de tópicos continuas.
  * **Columnas:** `Tag A`, `Tag B`, `Similitud_Coseno_Prob_Topicos`.

* **`graficos/` (HTMLs complementarios de etiquetas)**
  * **`07_pie_cobertura.html`:** Gráfico de torta con la proporción general de artículos con y sin etiqueta.
  * **`07_evolucion_etiquetado.html`:** Barras apiladas anuales mostrando la adopción de etiquetas en el tiempo.
  * **`07_distribucion_etiquetas_por_categoria.html`:** Volumen de etiquetas únicas creadas dentro de cada sección editorial.

---

## 4_Recomendador.py

* **`articulos.csv`**
  * **Qué es:** El archivo maestro de documentos (1 fila = 1 artículo estrictamente).
  * **Columnas:** `doc_id`, `ID`, `title_text`, `source_url`, `tagline`, `post_tag`, `post_date`, `topic`, `topic_label`, `umap_sem_x`, `umap_sem_y`, `umap_tem_x`, `umap_tem_y`.
  * **Uso:** Catálogo principal del buscador de artículos, información de contexto (título, bajada, fecha, URL), asignación de tópicos, gráfico temporal en `1_Articulos.py` y coordenadas 2D para los mapas semántico y temático.

* **`doc_topic_dist.npy`**
  * **Qué es:** Matriz NumPy densa de flotantes ($N \times K$) con la distribución suave de tópicos por documento.
  * **Alineación:** La fila $i$ corresponde exactamente al `doc_id = i` de `articulos.csv`.
  * **Uso:** Cálculo vectorial en memoria de la Similitud Coseno para obtener el Top 10 de artículos recomendados en tiempo real.