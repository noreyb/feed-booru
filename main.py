import os
import time

import requests
import yaml
from dotenv import load_dotenv
from urllib.parse import urlencode, quote


def get_from_raindrop(collection_id, token):
    url = "https://api.raindrop.io/rest/v1"
    endpoint = "/raindrops"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    query = {
        "perpage": 50,
    }
    r = requests.get(
        f"{url}{endpoint}/{collection_id}",
        headers=headers,
        params=query,
    )

    if r.status_code != requests.codes.ok:
        print(r.text)
        exit()

    time.sleep(1)
    return r


def get_booru_user(src):
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    base_url = "https://danbooru.donmai.us"
    endpoint = "artists.json"
    params = {"search[url_matches]": src}
    r = requests.get(f"{base_url}/{endpoint}", headers=headers, params=params)

    if r.status_code != requests.codes.ok:
        print(r.text)
        exit()

    time.sleep(1)
    return r.json()


if __name__ == "__main__":
    load_dotenv()
    token = os.getenv("RD_TOKEN")
    unmark = int(os.getenv("UNMARK"))
    marked = int(os.getenv("MARKED"))
    notfound = int(os.getenv("NOTFOUND"))

    with open("weneedfeed.yml", "r") as f:
        feeds = yaml.safe_load(f)

    r = get_from_raindrop(unmark, token)

    if r.json()["count"] == 0:
        print("There is no unmark raindrops")
        exit()

    raindrops = []
    not_found_ids = []
    marked_ids = []
    for item in r.json()["items"]:
        if "twitter.com" in item["domain"] or "x.com" in item["domain"]:
            user = item["link"].split("/")[3]

        if "pixiv" in item["domain"]:
            user = item["link"].split("/")[4]

        booru_user = get_booru_user(user)
        if 0 == len(booru_user):
            not_found_ids.append(item["_id"])
            continue

        booru_name = booru_user[0]["name"]
        marked_ids.append(item["_id"])

        # gelbooruのurlを生成
        query = {
            "page": "post",
            "s": "list",
            "tags": f"{booru_name}",
        }
        # encoded_query = quote(urlencode(query))
        encoded_query = urlencode(query)
        url = f"https://gelbooru.com/index.php?{encoded_query}"
        print(url)
        page = {
            "id": f"{booru_name}",
            "title": f"{booru_name}",
            "url": url,
            "item_selector": "article",
            "item_image_selector": "img",
            "item_link_selector": "a",
            "item_title_selector": "title",
        }
        feeds["pages"].append(page)

    # Sort pages
    pages = sorted(feeds["pages"], key=lambda x: x["id"])
    pages = list({page["url"]: page for page in pages}.values())
    feeds["pages"] = pages

    with open("weneedfeed.yml", "w") as f:
        yaml.dump(feeds, f, encoding="utf-8", allow_unicode=True)

    # idの移動
    print(marked_ids)
