import requests
import json
import time
import queue
import dbutils
import threading
import qrcode
from enum import Enum
from decouple import config
from io import BytesIO
import base64

#Telegram exposes a rest API for bot communication

#I decided to have the bot thread run as a finite state machine

class BotState:
    """ This is the base class of the telegram bot state, every other state must implement the run method,
    and at the very least pass the owner"""
    def __init__(self, owner):
        self.owner = owner

    def run(self):
        return None
    
    @property
    def state():
        """ A string name to help identify the state """
        return "default"

class BotStartupState(BotState):

    """ The telegram bot will always pass through this state. This is where we check if the necessary fields are in the database. If not, we mvoe into the setup state, otherwise we move into our main operational state."""

    def __init__(self, owner):
        super().__init__(owner)
        owner.chat_id = dbutils.get_setting_value(owner.sqlite_conn, owner.sqlite_cursor, "BOT_CHAT_ID")

    def run(self):
        if self.owner.chat_id is not None:
            return BotMainState(self.owner)
        else:
            return BotSetupState(self.owner)
        
    @property
    def state(self):
        return "startup"

class BotSetupState(BotState):

    """ The run function checks until both the bot token and the chat id have been set. Note that we discard any message that does not have a name of bot_token or bot_chat_id. """

    def __init__(self, owner):
        super().__init__(owner)
        self.owner.chat_id = dbutils.get_setting_value(owner.sqlite_conn, owner.sqlite_cursor, "BOT_CHAT_ID")

    def run(self):

        try:
            task = self.owner.messages.get(timeout=1)
            if task["name"] == "bot_chat_id":
                self.owner.chat_id = task["value"]
                dbutils.update_setting_value(self.owner.sqlite_conn, self.owner.sqlite_cursor, "BOT_CHAT_ID", self.owner.chat_id)
        except queue.Empty:
            pass

        if self.owner.chat_id is not None:
            return BotMainState(self.owner)
        else:
            return None
        
    @property
    def state(self):
        return "setup"

class BotMainState(BotState):

    """ This is the workhorse of the bot"""
    def __init__(self, owner):
        super().__init__(owner)

    def send_message_with_img(self, msg_txt, img_path, timeout=60):

        print("Sending message with image")

        files = {
            "photo" : open(f'/app/thumbnails/{img_path}', 'rb')
        }

        payload = {
            "chat_id" : self.owner.chat_id,
            "caption" : msg_txt,
            "parse_mode" : "Markdown"
        }

        try:
            response = requests.post(f"{self.owner.BASE_URL}/sendPhoto", data=payload, files=files, timeout=timeout)
        except requests.exceptions.Timeout:
            print("Timed out trying to send message with image", flush=True)
    
    def send_message(self, msg_txt, timeout=60):
        print("Sending plain text message")

        try:
            response = requests.post(f"{self.owner.BASE_URL}/sendMessage", json={
                "chat_id" : self.owner.chat_id,
                "text" : msg_txt 
            }, timeout=timeout)
        except:
            print("Timed out trying to send message without image", flush=True)
    
    def run(self):
        try:
            message = self.owner.messages.get_nowait()
            print(f"Reading message from telegram bot queue: {message}", flush=True)
            if message['name'] == "alert":
                self.send_message_with_img(message['text'], message['image'])
            elif message['name'] == "system":
                self.send_message(message["text"])
        except queue.Empty:
            pass
        except Exception as e:
            print(f'Error in main bot state: {e}', flush=True)

    @property
    def state(self):
        return "main"


class TelegramBotThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.token_id = config("BYAKUGAN_BOT_TOKEN")
        print(self.token_id, flush=True)
        self.chat_id = None
        self.messages = queue.Queue(maxsize=10)
        self.sqlite_conn, self.sqlite_cursor = None, None

    @property
    def BASE_URL(self):
        return f"https://api.telegram.org/bot{self.token_id}"

    def send_message(self, chat_id, msg_txt, timeout=15):
        return requests.post(f"{self.BASE_URL}/sendMessage", json={
            "chat_id" : chat_id,
            "text" : msg_txt 
        }, timeout=timeout)

    def get_qr_code_b64(self):
        response =requests.get(f"https://api.telegram.org/bot{self.token_id}/getMe")

        if response.status_code == 200:
            data = response.json()
            
            if data.get("ok"):
                botname = data["result"]["username"]

                bot_url = f"https://t.me/{botname}"
                code = qrcode.make(bot_url)

                img = code.make_image(fill="black", back_color="white")

                buffer = BytesIO()
                img.save(buffer, format="PNG")

                # Encode image to Base64
                qr_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
                
                return qr_b64


    def get_updates(self, offset = None, timeout=5):
        #print("Getting updates", flush=True)
        try:
            response = requests.get(f"{self.BASE_URL}/getUpdates", params={
                "offset": offset,
                "timeout" : timeout
            }, timeout=timeout)
            return response.json() 
        except requests.exceptions.ReadTimeout:
            return {}  

    def run(self):

        if self.sqlite_conn is None or self.sqlite_cursor is None:
            self.sqlite_conn, self.sqlite_cursor = dbutils.load_database()
            self.current_state = BotStartupState(self)

        offset = 0

        while True:
            updates = self.get_updates(offset = offset)
            #print(self.current_state.state, flush=True)

            for update in updates.get("result", []):
                last_chat_id = update["message"]["chat"]["id"]
                text = update["message"]["text"]

                if text == "/start":
                    self.send_message(last_chat_id, f"Welcome to Byakugan. Your application ID is: {last_chat_id}. \n\nPlease enter this value when prompted for it in the application.")
                    offset = int(update["update_id"]) + 1
                    break

            if self.current_state is not None:
                new_state = self.current_state.run()
                if new_state is not None:
                    self.current_state = new_state

            time.sleep(1)

    def add_message_to_queue(self, message):
        try:
            self.messages.put_nowait(message)
            #print(f"Adding message to queue {message}")
        except queue.Full:
            print("Telegram bot queue is full", flush=True)