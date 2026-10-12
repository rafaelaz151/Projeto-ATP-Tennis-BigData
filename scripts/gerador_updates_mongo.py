
from pymongo import MongoClient

client = MongoClient("mongodb://root:root@localhost:27017/")
db = client["atpplayers"]
country_col = db["NA_playersCountry"]

#Lê todos os jogadores que já têm país preenchido
players = list(country_col.find({}))

#Cria o ficheiro .txt com os updates para usar no Mongo
with open("updates_countries.txt", "w", encoding="utf-8") as f:
    for p in players:
        player_code = p.get("PlayerCode", "")
        country = p.get("Country", None)


        
        # Corrigir valores None para aparecer como null em JS
        country_js = "null" if country is None else f"\"{country}\""

        linha = (
            f"db.player.updateOne("
            f"{{'id_player': '{player_code}'}}, "
            f"{{$set: {{'Born': {country_js}}}}}"
            f");\n"
        )

        f.write(linha)

print("Ficheiro 'updates_countries.txt' criado com sucesso!")