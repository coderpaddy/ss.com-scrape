import json
import os
import re
import smtplib
import time
from email.mime.text import MIMEText

import requests
from bs4 import BeautifulSoup

import mycreds


def send_email(unique_count, message):
    sender = mycreds.sender
    sender_password = mycreds.sender_password
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(sender, sender_password)
    msg = MIMEText("\n".join([x["description"] for x in message.values()]), _charset='UTF-8')
    msg["Subject"] = f"{unique_count} Unique lens's"
    msg["From"] = sender
    msg["To"] = sender
    server.sendmail(sender, sender, msg.as_string())
    server.close()

def load_products():
    with open('data.json', 'r') as load_file:
        data = json.load(load_file)
    load_file.close()
    return data

def save_products(data):
    with open('data.json', 'w') as save_file:
        json.dump(data, save_file, sort_keys=True, indent=4)
    save_file.close()

def get_soup(url):
    request = requests.get(url)
    soup = BeautifulSoup(request.content, 'lxml')
    return soup

def check_spam(description):
    bad_words = ["fotoveikals", "garantiju"]
    for x in bad_words:
        if x in description:
            return True
    return False

def check_brand(item_brand):
    bad_brands = ["Sony", "Canon", "Canon ef", "Sigma", "Olympus", "Pentax", "Samyang", "Panasonic"]
    for brand in bad_brands:
        if item_brand == brand:
            return True
    return False


def scrape(url, sleep_time):
    time.sleep(sleep_time)
    soup = get_soup(url)
    all_rows = soup.find_all("tr", id=re.compile("tr_"))
    all_items = {}
    for a_row in all_rows:
        item_id = a_row.select_one("input[type='checkbox']").attrs["id"]
        a_row_cols = a_row.find_all("td")
        description = a_row.find("a", class_="am").get_text()
        item = {
            "description": description,
            "brand": a_row_cols[3].get_text(),
            "model": a_row_cols[4].get_text(),
            "price": a_row_cols[5].get_text().replace(" €", ""),
            "scam_mark": check_spam(description),
            "bad_brand": check_brand(a_row_cols[3].get_text()),
        }
        all_items[item_id] = item
    #-- Test Email --
    #send_email(len(all_items.keys()), all_items)
    safe_items = {}
    for key in all_items.keys():
        if all_items[key]["bad_brand"] is False and all_items[key]["scam_mark"] is False:
            safe_items[key] = all_items[key]

    return safe_items


if __name__ == "__main__":
    url = "https://www.ss.com/lv/electronics/photo-optics/objectives/today-2/sell/filter/riga_f/"
    scrape_count = 1
    while True:
        sleep_time = 0 if scrape_count == 1 else 600
        new_items = scrape(url, sleep_time)
        if os.path.isfile('data.json'):
            old_items = load_products()
            unique_items = {}
            for new_item_key in new_items.keys():
                if new_item_key in old_items:
                    continue
                else:
                    unique_items[new_item_key] = new_items[new_item_key]
            if len(unique_items) > 0:
                send_email(len(unique_items), unique_items)
                print(f"Scrape Count: {scrape_count}. {len(unique_items)} New Items, Email sent!")
            else:
                print(f"Scrape Count: {scrape_count}. No New Products")
        else:
            print(" -- No Old Data: will compare next time --")
        save_products(new_items)
        scrape_count += 1
