import os
import time
from urllib.parse import quote, urlencode

import requests
import yaml
from dotenv import load_dotenv


def get_raindrops(collection_id, token):
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


def fetch_tagged_raindrops(items, tags, has_tag=True):
    filtered_items = []
    for item in items:
        for tag in item["tags"]:
            if tag in tags:
                filtered_items.append(item)

    if has_tag:
        return filtered_items
    else:
        return [item for item in filtered_items if item not in items]


def tag_raindrop(items, collection, tag, token):
    url = "https://api.raindrop.io/rest/v1"
    endpoint = "/raindrops"

    tags = [tag]
    resp = requests.put(
        f"{url}{endpoint}/{collection}",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        params={"perpage": 50},
        json={
            "ids": items,
            "collectionId": collection,
            "tags": tags,
        },
    )

    if resp.status_code != requests.codes.ok:
        print(resp.text)
        exit(1)

    time.sleep(1)
    return resp


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


def fetch_user_name(item: dict):
    if "twitter.com" in item["domain"] or "x.com" in item["domain"]:
        user = item["link"].split("/")[3]
    if "pixiv" in item["domain"]:
        user = item["link"].split("/")[4]
    return user


if __name__ == "__main__":
    load_dotenv()
    token = os.getenv("RD_TOKEN")
    collection = int(os.getenv("SUBSCRIBE"))

    with open("weneedfeed.yml", "r") as f:
        feeds = yaml.safe_load(f)

    r = get_raindrops(collection, token)
    items = r.json()["items"]
    tags = ["booru_marked", "booru_notfound"]
    items = fetch_tagged_raindrops(items, tags, has_tag=False)
    print(items)

    not_found_ids = []
    marked_ids = []
    for item in items:
        user = fetch_user_name(item)
        booru_user = get_booru_user(user)

        if 0 == len(booru_user):
            not_found_ids.append(item["_id"])
            continue
        marked_ids.append(item["_id"])

        booru_name = booru_user[0]["name"]
        query = {
            "page": "post",
            "s": "list",
            "tags": f"{booru_name}",
        }
        encoded_query = urlencode(query)
        url = f"https://gelbooru.com/index.php?{encoded_query}"
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

    # Sort pages & update weneedfeed
    pages = sorted(feeds["pages"], key=lambda x: x["id"])
    pages = list({page["url"]: page for page in pages}.values())
    feeds["pages"] = pages
    with open("weneedfeed.yml", "w") as f:
        yaml.dump(feeds, f, encoding="utf-8", allow_unicode=True)

    # Add tag to raindrop
    if 0 != len(marked_ids):
        tag = "booru_marked"
        tag_raindrop(marked_ids, collection, tag, token)
    if 0 != len(not_found_ids):
        tag = "booru_notfound"
        tag_raindrop(not_found_ids, collection, tag, token)
