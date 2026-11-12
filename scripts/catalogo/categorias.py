"""Mapa de `categories_tags` de Open Food Facts a departamentos de tienda de abarrotes.

Las etiquetas de OFF van de lo general a lo específico ("en:beverages", "en:sodas",
"en:colas"). Se revisan las palabras de cada etiqueta contra listas de palabras clave,
en el orden de prioridad de `REGLAS`: gana la primera categoría con alguna coincidencia.
"""

from __future__ import annotations

CATEGORIAS = [
    "Bebidas", "Botanas", "Lácteos", "Panadería", "Abarrotes", "Limpieza", "Higiene personal",
    "Dulces", "Enlatados", "Congelados", "Carnes y embutidos", "Mascotas", "Bebés", "Otros",
]

# (categoría, palabras clave). Las palabras se comparan contra las palabras de la etiqueta
# (separadas por guiones, sin el prefijo de idioma). El orden importa.
REGLAS: list[tuple[str, frozenset[str]]] = [
    ("Mascotas", frozenset({
        "pet", "pets", "petfood", "dog", "dogs", "cat", "cats", "kibble", "kibbles", "mascotas",
        "perro", "perros", "gato", "gatos",
    })),
    ("Bebés", frozenset({
        "baby", "babies", "infant", "infants", "toddler", "toddlers", "diaper", "diapers", "nappies",
        "bebe", "bebes", "panales", "pañales", "lactantes",
    })),
    ("Limpieza", frozenset({
        "cleaning", "cleaners", "cleaner", "detergent", "detergents", "laundry", "bleach", "bleaches",
        "dishwashing", "softener", "softeners", "household", "disinfectant", "disinfectants",
        "insecticide", "insecticides", "limpieza", "limpiadores", "detergentes", "aromatizantes",
        "trash", "garbage",
    })),
    ("Higiene personal", frozenset({
        "hygiene", "shampoo", "shampoos", "conditioner", "conditioners", "soap", "soaps", "toothpaste",
        "toothpastes", "toothbrush", "toothbrushes", "deodorant", "deodorants", "antiperspirant",
        "antiperspirants", "cosmetic", "cosmetics", "beauty", "skincare", "skin", "hair", "razor",
        "razors", "shaving", "sanitary", "tampons", "pads", "toilet", "lotion", "lotions", "sunscreen",
        "perfume", "perfumes", "fragrance", "fragrances", "makeup", "make", "mouthwash", "mouthwashes",
        "body", "face", "lip", "lips", "nails", "hand", "hands", "bath", "higiene", "cuidado",
        "medicine", "medicines", "medication", "pharmacy", "supplement", "supplements", "vitamins",
        "vitaminas", "suplementos", "medicamentos", "farmacia",
    })),
    ("Congelados", frozenset({
        "frozen", "ice", "icecream", "popsicle", "popsicles", "congelados", "helados", "paletas",
    })),
    ("Enlatados", frozenset({"canned", "tinned", "enlatados", "conservas"})),
    # Abarrotes explícitos: van antes de Lácteos/Dulces para que "nut-butters", "chocolate-spreads"
    # o "chocolate-cereals" no caigan en otro departamento.
    ("Abarrotes", frozenset({
        "cereal", "cereals", "breakfast", "breakfasts", "spread", "spreads", "jam", "jams", "honey",
        "honeys", "syrup", "syrups", "sauce", "sauces", "condiment", "condiments", "pasta", "pastas",
        "noodle", "noodles", "rice", "rices", "flour", "flours", "legume", "legumes", "bean", "beans",
        "lentils", "chickpeas", "oil", "oils", "vinegar", "vinegars", "sweetener",
        "sweeteners", "seasoning", "seasonings", "spice", "spices", "soup", "soups",
        "broth", "broths", "bouillon", "mayonnaise", "mayonnaises", "ketchup", "mustard", "mustards",
        "dressing", "dressings", "salsa", "salsas", "mole", "moles", "instant", "grains", "oats",
        "granola", "granolas", "powder", "powders", "mixes", "mix", "dried", "dehydrated", "abarrotes", "harina", "harinas",
        "frijol", "frijoles", "arroz", "aceite", "aceites", "especias", "sopas",
    })),
    ("Lácteos", frozenset({
        "dairy", "dairies", "milk", "milks", "cheese", "cheeses", "yogurt", "yogurts", "yoghurt",
        "yoghurts", "cream", "creams", "butter", "butters", "egg", "eggs", "lacteos", "leche",
        "quesos", "yogur", "crema", "mantequilla", "huevo", "huevos", "kefir", "margarine", "margarines",
    })),
    # Botanas saladas inequívocas: antes de Panadería/Dulces porque OFF etiqueta a veces
    # "sweet-snacks" junto con "salted-popcorn".
    ("Botanas", frozenset({
        "salty-snacks", "salted-snacks", "chips", "crisps", "popcorn", "popcorns", "pretzels", "nuts",
        "peanuts", "tortilla-chips", "corn-chips", "chicharrones", "frituras", "cacahuates", "botanas",
    })),
    ("Carnes y embutidos", frozenset({
        "meat", "meats", "sausage", "sausages", "ham", "hams", "charcuterie", "poultry", "chicken",
        "chickens", "beef", "pork", "turkey", "bacon", "fish", "fishes", "seafood", "seafoods",
        "shrimp", "shrimps", "tuna", "tunas", "sardines", "salmon", "surimi", "carnes", "embutidos",
        "salchichas", "jamon", "jamones", "pescados", "mariscos", "chorizo", "chorizos", "frankfurters",
        "cold-cuts", "hot-dogs", "deli-meats",
    })),
    ("Panadería", frozenset({
        "bread", "breads", "bakery", "bakeries", "biscuit", "biscuits", "cookie", "cookies", "cake",
        "cakes", "pastry", "pastries", "tortilla", "tortillas", "muffin", "muffins", "doughnut",
        "doughnuts", "donut", "donuts", "croissant", "croissants", "buns", "bun", "wafer", "wafers",
        "crackers", "cracker", "toast", "toasts", "brioche", "brioches", "pan", "panaderia",
        "galletas", "pasteles", "bolillo", "tostadas", "viennoiseries",
    })),
    ("Dulces", frozenset({
        "candy", "candies", "confectionery", "confectioneries", "chocolate", "chocolates", "lollipop",
        "lollipops", "gum", "gums", "chewing", "gummies", "gummy", "marshmallow", "marshmallows",
        "caramel", "caramels", "sweets", "sweet", "bonbons", "dulces", "caramelos", "paletas", "chicles",
        "toffee", "toffees", "nougat", "licorice",
    })),
    ("Botanas", frozenset({
        "snack", "snacks", "chip", "chips", "crisps", "crisp", "popcorn", "pretzel", "pretzels", "nut",
        "nuts", "peanut", "peanuts", "almonds", "pistachios", "seeds", "botanas", "frituras", "cacahuates",
        "churritos", "chicharrones", "tortilla-chips", "puffs", "extruded", "appetizers", "appetizer",
    })),
    ("Bebidas", frozenset({
        "beverage", "beverages", "drink", "drinks", "water", "waters", "soda", "sodas", "cola", "colas",
        "juice", "juices", "nectar", "nectars", "beer", "beers", "wine", "wines", "spirits", "liquor",
        "liquors", "tequila", "tequilas", "mezcal", "vodka", "rum", "whisky", "whiskey", "cider", "ciders",
        "isotonic", "lemonade", "lemonades",
        "smoothie", "smoothies", "bebidas", "refrescos", "jugos", "agua", "cerveza", "cervezas",
        "infusions", "infusion", "kombucha", "horchata", "atole",
    })),
]

# Etiquetas raíz que, si aparecen solas, siguen siendo comida → Abarrotes.
_RAIZ_ABARROTES = frozenset({"en:foods", "en:food", "en:groceries", "en:plant-based-foods-and-beverages"})


# Palabras del nombre del producto → categoría, para productos sin etiquetas en OFF
# (la mayoría de los productos de México). Mismo orden de prioridad que REGLAS.
REGLAS_NOMBRE: list[tuple[str, frozenset[str]]] = [
    ("Mascotas", frozenset({"croquetas", "croqueta", "perro", "perros", "gato", "gatos", "mascota", "mascotas",
                            "cachorro", "cachorros", "dog", "cat", "pet"})),
    ("Bebés", frozenset({"bebe", "bebes", "panal", "panales", "infantil", "lactante", "lactantes", "papilla",
                         "papillas", "gerber", "enfamil", "nutramigen", "formula", "toallitas", "baby"})),
    ("Limpieza", frozenset({"detergente", "detergentes", "cloro", "limpiador", "limpiadores", "suavizante",
                            "lavatrastes", "desinfectante", "insecticida", "aromatizante", "aromatizantes",
                            "desengrasante", "blanqueador", "jerga", "fibra", "escoba", "trapeador", "servilletas",
                            "servilleta", "basura", "fabuloso", "pinol", "ariel", "ace", "limpia", "lavanderia",
                            "multiusos", "antibacterial", "aluminio", "esponja", "cerillos", "veladora"})),
    ("Higiene personal", frozenset({"shampoo", "champu", "jabon", "jabones", "dental", "desodorante", "desodorantes",
                                     "rastrillo", "rastrillos", "enjuague", "acondicionador", "talco", "cepillo",
                                     "cepillos", "condon", "condones", "preservativo", "preservativos", "locion",
                                     "perfume", "colonia", "crema-corporal", "bloqueador", "protector", "maquillaje",
                                     "labial", "toalla", "toallas", "femenina", "femeninas", "tampones", "higienico",
                                     "higienicos", "pasta-dental", "hilo-dental", "medicamento", "medicamentos",
                                     "tabletas", "capsulas", "jarabe", "paracetamol", "ibuprofeno", "metamizol",
                                     "naproxeno", "aspirina", "vitamina", "vitaminas", "suplemento", "suplementos",
                                     "analgesico", "antiacido", "hidroxido", "gel", "cuidado", "afeitar", "pañuelos",
                                     "panuelos", "cotonetes", "algodon", "curitas", "alcohol", "antiseptico", "electrolitos"})),
    ("Congelados", frozenset({"helado", "helados", "nieve", "nieves", "congelado", "congelados", "congelada",
                              "congeladas", "paleta-helada", "paletas-heladas", "hielo", "hielos", "ice-cream"})),
    ("Enlatados", frozenset({"atun", "sardina", "sardinas", "enlatado", "enlatados", "enlatada", "lata", "latas",
                             "conserva", "conservas", "en-lata", "chiles-en-vinagre", "rajas", "elote-en-grano"})),
    ("Lácteos", frozenset({"leche", "leches", "queso", "quesos", "yogurt", "yoghurt", "yogur", "yogures", "griego",
                           "crema", "cremas", "mantequilla", "margarina", "huevo", "huevos", "kefir", "requeson",
                           "lacteo", "lacteos", "petit", "danonino", "oaxaca", "manchego", "panela", "cottage",
                           "milk", "cheese", "yogourt", "lala", "alpura", "nido"})),
    ("Carnes y embutidos", frozenset({"carne", "carnes", "pavo", "pollo", "cerdo", "res", "salchicha", "salchichas",
                                      "pechuga", "chorizo", "jamon", "jamones", "tocino", "molida", "bistec",
                                      "milanesa", "milanesas", "embutido", "embutidos", "longaniza", "peperoni",
                                      "pepperoni", "salami", "mortadela", "chuleta", "chuletas", "pescado",
                                      "camaron", "camarones", "mariscos", "pierna", "nuggets", "chicken", "beef",
                                      "pork", "turkey", "ham", "bacon", "surimi", "fud", "chicharron", "chicharrones"})),
    ("Panadería", frozenset({"pan", "panes", "tortilla", "tortillas", "tostada", "tostadas", "galleta", "galletas",
                             "bolillo", "bolillos", "pastel", "pasteles", "dona", "donas", "panque", "panques",
                             "muffin", "muffins", "pastelito", "pastelitos", "bisquet", "bisquets", "cookies", "cookie",
                             "bread", "rol", "roles", "concha", "conchas", "mantecadas", "mantecada", "pinguinos",
                             "gansito", "tortillinas", "tostitos", "cuernitos", "polvorones", "baguette", "hot-cakes",
                             "hotcakes", "waffles", "barritas", "wafer", "obleas", "oblea", "marias", "crackers"})),
    ("Dulces", frozenset({"dulce", "dulces", "gomitas", "gomita", "paleta", "paletas", "caramelo", "caramelos",
                          "chicle", "chicles", "chocolate", "chocolates", "bombon", "bombones", "malvavisco",
                          "malvaviscos", "mazapan", "cajeta", "turron", "chamoy", "tamarindo", "pulparindo",
                          "candy", "candies", "lollipop", "gummies", "chocolatin", "trufas", "mentas", "menta",
                          "mazapanes", "ate", "ates", "alegria", "alegrias", "palanqueta", "palanquetas", "glorias"})),
    ("Botanas", frozenset({"chips", "papas", "papitas", "palomitas", "totopos", "cacahuate", "cacahuates", "botana",
                           "botanas", "frituras", "fritura", "churritos", "takis", "doritos", "sabritas", "cheetos",
                           "ruffles", "nueces", "nuez", "almendras", "almendra", "pistaches", "semillas", "pepitas",
                           "pretzels", "pretzel", "snack", "snacks", "nachos", "rancheritos", "chicharrin", "crujitos",
                           "duros", "arandanos", "mix", "frutos-secos", "pasas", "habas", "garbanzos-tostados"})),
    ("Bebidas", frozenset({"jugo", "jugos", "agua", "aguas", "refresco", "refrescos", "nectar", "bebida", "bebidas",
                           "cerveza", "cervezas", "tequila", "vino", "vinos", "mezcal", "ron", "vodka", "whisky",
                           "whiskey", "brandy", "soda", "cola", "limonada", "naranjada", "horchata", "jamaica",
                           "kombucha", "energetica", "energizante", "hidratante", "isotonica", "te", "cafe-frio",
                           "coca", "pepsi", "sprite", "fanta", "jumex", "boing", "bonafont", "epura", "ciel", "gatorade",
                           "powerade", "electrolit", "red-bull", "monster", "drink", "juice", "water", "beer", "wine",
                           "sidra", "pulque", "michelada", "clamato", "sangria", "ponche"})),
    ("Abarrotes", frozenset({"salsa", "salsas", "harina", "harinas", "arroz", "aceite", "aceites", "avena", "cereal",
                             "cereales", "pasta", "pastas", "espagueti", "spaghetti", "fideo", "fideos", "sopa", "sopas",
                             "granola", "frijol", "frijoles", "lenteja", "lentejas", "garbanzo", "garbanzos", "mayonesa",
                             "aderezo", "aderezos", "catsup", "ketchup", "mostaza", "vinagre", "miel", "azucar", "sal",
                             "mole", "consome", "consomes", "cafe", "chocolate-en-polvo", "cocoa", "mermelada",
                             "mermeladas", "amaranto", "gelatina", "gelatinas", "flan", "polvo", "sazonador",
                             "sazonadores", "especias", "condimento", "condimentos", "chile", "chiles", "chipotle",
                             "chipotles", "jalapeno", "jalapenos", "habanero", "pure", "tomate", "verduras", "verdura",
                             "vegetales", "maiz", "elote", "nopal", "nopales", "soya", "proteina", "protein", "whey",
                             "crema-de-cacahuate", "semola", "levadura", "polvo-para-hornear", "canela", "vainilla",
                             "sauce", "rice", "flour", "beans", "oats", "cereal", "oliva", "ajonjoli", "chia", "linaza",
                             "quinoa", "endulzante", "sustituto", "caldo", "caldos", "knorr", "maggi", "maseca",
                             "minsa", "mccormick", "herdez", "costena", "valentina", "huichol", "bimbo-tostado",
                             "barra", "barras", "mezcla", "preparado", "jarabe-de-maple", "maple", "tahini",
                             "pure-de-papa", "atole", "chocolate-abuelita", "ibarra", "nesquik", "leche-en-polvo"})),
]


def _normalizar_palabra(palabra: str) -> str:
    import unicodedata
    palabra = unicodedata.normalize("NFKD", palabra.lower()).encode("ascii", "ignore").decode()
    return palabra.strip(".,;:()[]\"'!¡¿?-/")


def categoria_por_nombre(nombre: str | None) -> str | None:
    """Categoría deducida de las palabras del nombre (sin acentos, minúsculas) o None."""
    if not nombre:
        return None
    palabras = [_normalizar_palabra(p) for p in nombre.replace("/", " ").replace("-", " ").split()]
    palabras = [p for p in palabras if p]
    conjunto = set(palabras)
    # Frases de dos palabras ("papel higienico", "paleta helada", "en lata") como "palabra-palabra".
    conjunto |= {f"{a}-{b}" for a, b in zip(palabras, palabras[1:])}
    for categoria, claves in REGLAS_NOMBRE:
        if conjunto & claves:
            return categoria
    return None


def _palabras(etiqueta: str) -> set[str]:
    cuerpo = etiqueta.split(":", 1)[1] if ":" in etiqueta else etiqueta
    return set(cuerpo.split("-")) | {cuerpo}


def categoria_para(etiquetas: list[str] | None, fuente: str = "off", nombre: str | None = None) -> str:
    """Devuelve el departamento para las `categories_tags` de un producto.

    Si las etiquetas no deciden, se intenta con las palabras de `nombre`. `fuente` decide el
    valor por defecto: "obf" → Higiene personal, "opff" → Mascotas, "off" con etiquetas →
    Abarrotes, sin etiquetas → Otros.
    """
    etiquetas = [e for e in (etiquetas or []) if e]
    palabras_por_etiqueta = [_palabras(e) for e in etiquetas]
    for categoria, claves in REGLAS:
        for palabras in palabras_por_etiqueta:
            if palabras & claves:
                return categoria
    if fuente == "obf":
        return "Higiene personal"
    if fuente == "opff":
        return "Mascotas"
    por_nombre = categoria_por_nombre(nombre)
    if por_nombre:
        return por_nombre
    if fuente == "opf":
        return "Otros"
    return "Abarrotes" if etiquetas else "Otros"
