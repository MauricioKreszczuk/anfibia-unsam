# Proyecto Anfibia

Proyecto desarrollado como optativa en el marco de la **Licenciatura en Ciencia de Datos (UNSAM)**. Desarrollado por el **Centro de Inteligencia Artificial Interdisciplinario (CIAI)** junto a **Mauricio Kreszczuk (estudiante LCD)** en colaboración con **Revista Anfibia**.

Se realiza una exploración sobre el archivo de publicaciones de la revista (2012–2026), modelado de tópicos y algoritmos de similitud para recomendación de notas.

---

## 📂 Estructura del Repositorio

La disposición del proyecto sigue las recomendaciones de reproducibilidad y resguardo del CIAI-UNSAM:

```text
├── data/
│   ├── raw/                 # Datos originales (.sql, .csv) [ignorado por Git]
│   ├── processed/           # Datasets curados (.parquet, .csv) [ignorado por Git]
├── docs/                    # diseño, decisiones, informes
├── notebooks/               # Exploración y análisis
├── outputs/                 # Figuras, tableros, resultados
├── src/                     # Scripts auxiliares de extracción y procesamiento
├── app.py                   # Tablero interactivo (Streamlit)
├── requirements.txt         # Entorno reproducible
├── .gitignore               # Reglas de exclusión
└── README.md                # Documentación técnica general


