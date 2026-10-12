import time
import random
import pymongo
from multiprocessing import Pool, cpu_count
from playwright.sync_api import sync_playwright

client = pymongo.MongoClient("mongodb://root:root@localhost:27017/")
db = client["atpplayers"]
players_col = db["player"]
country_col = db["NA_playersCountry"]

def scrape_single_player(args):
    player, idx = args

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        player_name = player["Name"].lower().replace(" ", "-")
        player_code = player["PlayerLink"].split("/")[-2]

        url = f"https://www.atptour.com/en/players/{player_name}/{player_code}/overview"
        print(f"[{idx}] Acessando {url}")

        try:
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            time.sleep(random.uniform(2, 4))

            try:
                page.click("#onetrust-accept-btn-handler", timeout=2000)
            except:
                pass

            lis = page.query_selector_all("ul.pd_right li")
            country = None

            for li in lis:
                spans = li.query_selector_all("span")
                if len(spans) >= 2 and spans[0].inner_text().strip() == "Country":
                    country = spans[1].inner_text().strip()
                    break

        except Exception as e:
            print(f"[{idx}] ERRO em {player['Name']}: {e}")
            country = None

        browser.close()

        # salva no Mongo
        country_col.update_one(
            {"PlayerCode": player_code},
            {"$set": {
                "PlayerName": player["Name"],
                "PlayerCode": player_code,
                "Country": country
            }},
            upsert=True
        )

        print(f"[{idx}] {player['Name']} → {country}")
        time.sleep(random.uniform(1, 3))

    return country



if __name__ == "__main__":
    players = players = list(players_col.find({"Born": ""}))
    print(f"Total de jogadores carregados: {len(players)}")

    # Quantos browsers simultâneos
    WORKERS = 12

    # Distribuir jogadores pelos processos
    args_list = [(players[i], i) for i in range(len(players))]

    with Pool(WORKERS) as pool:
        pool.map(scrape_single_player, args_list)