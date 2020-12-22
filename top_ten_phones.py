from pymongo import MongoClient 

client = MongoClient(URI_MONGODB)

precio_usuario = int(input("¿Cuánto quieres gastarte como máximo?"))

result = list(
    client["Amazon"]["Productos"].aggregate(
        [
            {
                "$match": {
                    "Precio": {"$lte": precio_usuario},
                    "Score": {"$exists": True},
                }
            },
            {"$sort": {"Score": -1}},
            {"$limit": 10},
        ]
    )
)

for resultado in result:
    if resultado["Marca"] is None:
        resultado["Marca"] = "Marca sin especificar"
    print("###################################################################")
    print(("Nombre:{nombre_result}").format(nombre_result=resultado["Nombre"]))
    print(("Precio:{precio_result}").format(precio_result=resultado["Precio"]))
    print(("Marca:{marca_result}").format(marca_result=resultado["Marca"]))
    print(("Media:{media_result}").format(media_result=resultado["media"]))
    print(("url:{url_result}").format(url_result=resultado["url"]))
