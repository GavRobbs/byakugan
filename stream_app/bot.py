import requests
import json
import time
import queue
import dbutils
from decouple import config

#Telegram exposes a rest API for bot communication

BOT_TOKEN = config("BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def get_updates(offset = None, timeout=15):
    response = requests.get(f"{BASE_URL}/getUpdates", params={
        "offset": offset,
        "timeout" : timeout
    }, timeout=15)
    return response.json()

def send_message(chat_id, msg_txt, timeout=15):
    response = requests.post(f"{BASE_URL}/sendMessage", json={
        "chat_id" : chat_id,
        "text" : msg_txt 
    }, timeout=15)

def send_message_with_img(chat_id, msg_txt, img_path, timeout=15):

    files = {
        "photo" : open(f'./thumbnails/{img_path}', 'rb')
    }

    payload = {
        "chat_id" : chat_id,
        "caption" : msg_txt,
        "parse_mode" : "Markdown"
    }

    response = requests.post(f"{BASE_URL}/sendPhoto", data=payload, files=files, timeout=timeout)

def bot_main(bot_message_queue):

    """ This is the main loop for the bot and it works by long polling. Initially, we check if the bot has connected previously. We do this indirectly by checking if we saved our chat_id in the database. If we haven't, we enter the loop waiting for the database to contain it so it can dispatch messages. We also have the functionality that displays it to the telegram user so they can enter it themselves."""

    sqlite_conn, sqlite_cursor = dbutils.load_database("byakugan")

    chat_id_db = dbutils.get_setting_value(sqlite_conn, sqlite_cursor, "BYAKUGAN_CHAT_ID")
    offset = None

    while True:
        updates = get_updates(offset, timeout=0)

        for update in updates.get("result", []):
            chat_id = update["message"]["chat"]["id"]
            text = update["message"]["text"]

            if text == "/start":
                send_message(chat_id, f"Welcome to Byakugan. Your application ID is: {chat_id}. \n\nPlease enter this value when prompted for it in the application.")
                offset = int(update["update_id"]) + 1
                break

        if chat_id_db is not None:
            try:
                message = bot_message_queue.get(timeout = 1)
                if message['type'] == "system":
                    send_message(chat_id_db, message.text)
                elif message['type'] == "alert":
                    send_message_with_img(chat_id_db, message['text'], message['image'])
            except queue.Empty:
                continue
            except Exception as e:
                print(f'Error in bot handler: {e}')
        else:
            print("Fetching ID")
            chat_id_db = dbutils.get_setting_value(sqlite_conn, sqlite_cursor, "BYAKUGAN_CHAT_ID")            
                    

if __name__ == "__main__":
    #I made it runnable as a module, just to test what happens
    offset = None
    chat_id = 0

    while True:
        print("Fetching updates")
        updates = get_updates(offset)

        print("Processing updates")
        for update in updates.get("result", []):
            chat_id = update["message"]["chat"]["id"]
            text = update["message"]["text"]

            if text == "/start":
                send_message(chat_id, f"Welcome to Byakugan. Your application ID is: {chat_id}. \n\nPlease enter this value when prompted for it in the application.")

            offset = int(update["update_id"]) + 1

        time.sleep(1)