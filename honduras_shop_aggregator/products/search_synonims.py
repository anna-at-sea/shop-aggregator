SEARCH_SYNONYM_GROUPS = (
    # =========================
    # CELULARES / TECNOLOGÍA
    # =========================
    {"celular", "movil", "móvil", "telefono", "teléfono", "smartphone"},
    {"computadora", "ordenador", "pc", "computador", "laptop"},
    {"tableta", "tablet"},
    {"televisor", "television", "televisión", "tv"},
    {"audifonos", "audífonos", "auriculares", "headphones", "headset"},
    {"bocina", "parlante", "altavoz", "speaker"},
    {"cable", "cordon"},
    {"smartwatch", "reloj"},
    {"drone", "dron"},
    {"proyector", "videoproyector"},
    {"monitor", "pantalla"},
    {"impresora", "printer"},
    {"teclado", "keyboard"},
    {"mouse", "raton", "ratón"},
    {"usb", "flash", "pendrive"},
    {"memoria", "microsd"},
    {"consola", "videoconsola"},
    {"videojuego", "juego", "videojuegos"},
    {"playstation", "play", "ps5", "ps4"},
    # =========================
    # ELECTRODOMÉSTICOS
    # =========================
    {"refrigerador", "nevera", "refrigeradora"},
    {"freidora", "fryer"},
    {"aspiradora", "barredora"},
    {"ventilador", "abanico"},
    {"aire", "ac"},
    {"calentador", "termo"},
    # =========================
    # HOGAR / MUEBLES
    # =========================
    {"sofa", "sofá", "sillon", "sillón"},
    {"sillon", "sillón", "butaca"},
    {"almohada", "cojin", "cojín"},
    {"cortina", "cortinas"},
    {"mesa", "mesita"},
    {"silla", "asiento"},
    {"ropero", "armario", "closet", "guardarropa"},
    {"estante", "repisas", "repisa", "estanteria", "estantería"},
    {"lampara", "lámpara", "luz", "luminaria"},
    {"ventilador", "abanico"},
    # =========================
    # ROPA
    # =========================
    {"camiseta", "playera", "camisa"},
    {"vestido", "vestidos"},
    {"falda", "faldas"},
    {"chaqueta", "chamarra", "casaca"},
    {"sueter", "sweater", "jersey"},
    {"sudadera", "hoodie", "chompa"},
    {"abrigo", "chaqueton", "chaquetón"},
    # =========================
    # CALZADO
    # =========================
    {"zapatos", "calzado"},
    {"tenis", "zapatillas", "sneakers"},
    {"sandalias", "sandalia"},
    {"botas", "bota"},
    {"chanclas", "chancletas", "sandalias"},
    # =========================
    # ACCESORIOS / MODA
    # =========================
    {"bolso", "bolsa", "cartera"},
    {"mochila", "morral"},
    {"billetera", "cartera"},
    {"gorra", "gorras", "cap"},
    {"sombrero", "sombreros"},
    {"joyeria", "joyería", "joyas"},
    {"collar", "cadena"},
    {"aretes", "pendientes", "zarcillos"},
    {"pulsera", "brazalete"},
    # =========================
    # BELLEZA / CUIDADO PERSONAL
    # =========================
    {"perfume", "fragancia", "colonia"},
    {"maquillaje", "cosmeticos", "cosméticos"},
    {"crema", "locion", "loción"},
    {"shampoo", "champu", "champú"},
    {"acondicionador", "conditioner"},
    {"labial", "pintalabios", "lipstick"},
    {"afeitadora", "rasuradora"},
    # =========================
    # DEPORTES / FITNESS
    # =========================
    {"bicicleta", "bici"},
    {"pesas", "peso", "mancuernas"},
    {"caminadora", "treadmill"},
    {"balon", "balón", "pelota"},
    {"futbol", "fútbol", "soccer"},
    {"baloncesto", "basketball", "basquetbol", "básquetbol"},
    # =========================
    # AUTOS / MOTOS
    # =========================
    {"coche", "carro", "auto", "automovil", "automóvil"},
    {"moto", "motocicleta"},
    {"repuesto", "pieza", "autoparte"},
    {"llanta", "neumatico", "neumático", "goma"},
    {"bateria", "batería", "acumulador"},
    {"aceite", "lubricante"},
    # =========================
    # BEBÉS / NIÑOS
    # =========================
    {"bebe", "bebé", "infante"},
    {"cochecito", "carriola"},
    {"biberon", "biberón", "mamadera"},
    {"pañales", "panales", "pañal"},
    {"juguete", "juguetes"},
    {"muñeca", "muneca"},
    # =========================
    # COCINA
    # =========================
    {"sarten", "sartén"},
    {"olla", "ollas"},
    {"cuchillo", "cuchillos"},
    {"vajilla", "platos"},
    {"vasos", "vaso"},
    {"taza", "tazas"},
    # =========================
    # LIBROS / OFICINA
    # =========================
    {"libro", "libros"},
    {"cuaderno", "libreta"},
    {"lapiz", "lápiz"},
    {"lapicero", "boligrafo", "bolígrafo", "pluma"},
    {"mochila", "morral"},
)

SEARCH_SYNONYMS = {
    synonym: group
    for group in SEARCH_SYNONYM_GROUPS
    for synonym in group
}
