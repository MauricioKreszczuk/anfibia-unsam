from pathlib import Path

SPANISH_STOPWORDS = {
    "a", "acá", "ahi", "ahí", "al", "algo", "algunas", "algunos", "ante", "antes", "aquel", "aquella", "aquellas", "aquello", "aquellos",
    "aqui", "aquí", "arriba", "asi", "así", "atras", "aun", "aunque", "bajo", "bien", "cada", "casi", "como", "con", "contra",
    "cual", "cuando", "de", "del", "desde", "donde", "dos", "durante", "e", "el", "él", "ella", "ellas", "ellos", "en", "entre",
    "era", "eran", "eres", "es", "esa", "esas", "ese", "eso", "esos", "esta", "está", "estaba", "estaban", "estado", "estamos", "estan", "están",
    "estar", "este", "esto", "estos", "estoy", "fue", "fueron", "fui", "ha", "haber", "habia", "había", "hace", "hacen", "hacer", "hacia",
    "han", "hasta", "hay", "la", "las", "le", "les", "lo", "los", "mas", "más", "me", "mi", "mis", "mismo", "mucha", "muchas", "mucho", "muchos",
    "muy", "nada", "ni", "no", "nos", "nosotras", "nosotros", "nuestra", "nuestras", "nuestro", "nuestros", "o", "otra", "otras", "otro", "otros",
    "para", "pero", "poco", "por", "porque", "que", "qué", "quien", "quién", "se", "sea", "segun", "según", "ser", "si", "sí", "sin",
    "sobre", "son", "su", "sus", "tambien", "también", "tan", "tanto", "te", "tenia", "tenía", "tener", "tiene", "tienen", "todo", "todos",
    "tu", "tus", "un", "una", "unas", "uno", "unos", "usted", "ustedes", "va", "van", "vez", "y", "ya", "yo",
}

DOMAIN_STOPWORDS = {
    "anfibia", "revista", "cronica", "crónica", "texto", "nota", "parte", "dice", "dijo", "hacer", "hace", "anos", "años",
    "argentina", "argentino", "argentinas", "argentinos", "buenos", "aires", "ano", "año", "poder",
    "decir", "ir", "ver", "solo", "llegar", "saber", "dar", "querer", "pasar", "volver", "día", "nuevo", "parecer", "quedar", 
    "creer", "dejar", "seguir", "encontrar", "llamar", "venir", "empezar", "persona", "historia", "vida", "caso", "momento", 
    "tiempo", "lugar", "forma", "primero", "despues", "después", "hoy", "ahora", "siempre", "nunca", "mientras", "cosa", 
    "alguno", "algun", "medio", "propio", "cierto", "grande", "dia"
}

NUEVAS_STOPWORDS = {
    # Verbos comodín y acciones genéricas
    "hablar", "deber", "pensar", "poner", "llevar", "vivir", "contar", "salir", 
    "tomar", "buscar", "trabajar", "tratar", "terminar", "sentir", "conocer", 
    "mostrar", "pedir", "preguntar", "mirar", "escuchar", "entender", "permitir", 
    "lograr", "ganar", "existir", "aparecer", "convertir", "explicar", "esperar", 
    "comenzar", "recordar", "generar", "cambiar", "construir", "recibir", "producir", 
    "usar", "abrir", "sacar", "presentar", "necesitar", "escribir", "jugar",
    
    # Adverbios, pronombres, números y conectores
    "cómo", "sino", "tú", "último", "menos", "tres", "sólo", "frente", "entonces", 
    "luego", "manera", "gran", "lado", "mil", "mes", "mejor", "además", "único", 
    "distinto", "varios", "tipo", "sentido", "junto", "ninguno", "tal", "modo", 
    "aún", "posible", "cualquiera", "nadie", "incluso", "embargo", "buen", 
    "importante", "largo", "allí", "alto", "tarde", "general", "partir", "pasado", 
    "claro", "todavía", "allá", "final", "medida", "dentro", "paso", "cuatro", "segundo",
    
    # Sustantivos genéricos y meta-periodismo
    #"público","trabajo", "libro","discurso", "obra"
    "grupo", "hora", "espacio", "gente", "problema", 
    "calle", "relación", "hecho", "palabra", "punto", "foto", "proceso", "tema", 
    "ejemplo", "imagen", "cuenta",  "situación", "través", 
    "mayoría", "pregunta", "diario", "acción", "posibilidad", "nombre", "fin", "centro"
}

NUEVAS_STOPWORDS_2 = {
    # Verbos en infinitivo
    #"leer", "morir", "pagar"
    "perder", "entrar", "decidir", "intentar", "sostener", 
    "mantener", "responder", "gustar", "considerar", "caer", 
    "suceder", "resultar", "ocurrir", "sumar", "reconocer", "alcanzar", 
    "soler", "proponer", "incluir", "tocar", "crear",
    
    # Adjetivos, adverbios, pronombres y números
    "mayor", "principal", "viejo", "pequeño", "común", "diferente", "igual", 
    "mal", "necesario", "fuerte", "difícil", "real", "apenas", "tampoco", 
    "cinco", "diez", "veces", "alguien", "mañana", "verdad",
    
    # Sustantivos abstractos, de relleno o métricas
    "idea", "mano", "amigo", "experiencia", "millón", "condición", "respuesta", 
    "diferencia", "camino", "puerta", "acuerdo", "resultado", "lucha", 
    "cuestión", "práctica", "presente", "ojo", "efecto", "cara", "personal", 
    "valor", "término"
}

NUEVAS_STOPWORDS_3 = {
    # Verbos en infinitivo restantes
    "funcionar", "ofrecer", "compartir", "comprar", "cumplir", "elegir", 
    "realizar", "crecer", "conseguir", "formar", "ocupar", "nacer", "correr",
    
    # Gramática, números y tiempo
    "cuyo", "cerca", "actual", "20", "ciento", "minuto", 
    
    # Comodines periodísticos o palabras vacías
    "clave", "llamado", "base", "falta"
}

NUEVAS_STOPWORDS_4 = {
    # Pronombres, preposiciones y conectores
    "ambos", "pesar", "fuera", "resto", "vuelta", "razón", 
    
    # Verbos en infinitivo genéricos
    #"publicar", "aprender", "participar",
    
    # Sustantivos abstractos de uso métrico/estructural
    #"número", 
    "uso",

    # Preposición temporal/espacial
    "tras", 
    
    # Verbos comodín / muletillas de redacción
    "acompañar", "señalar"
}



# Actualizá
DOMAIN_STOPWORDS = DOMAIN_STOPWORDS.union(NUEVAS_STOPWORDS)
DOMAIN_STOPWORDS = DOMAIN_STOPWORDS.union(NUEVAS_STOPWORDS_2)
DOMAIN_STOPWORDS = DOMAIN_STOPWORDS.union(NUEVAS_STOPWORDS_3)
DOMAIN_STOPWORDS = DOMAIN_STOPWORDS.union(NUEVAS_STOPWORDS_4)

STOPWORDS = sorted(SPANISH_STOPWORDS | DOMAIN_STOPWORDS)

# Resolución de ruta y guardado en data/processed/
PROJECT_ROOT = Path.cwd().resolve()
if PROJECT_ROOT.name == "notebooks":
    PROJECT_ROOT = PROJECT_ROOT.parent

OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "stopwords_anfibia.txt"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(STOPWORDS))

print(f"Guardadas {len(STOPWORDS)} stopwords en: {OUTPUT_PATH}")