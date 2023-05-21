# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2023 Emanuel Erben
# SPDX-FileCopyrightText: 2023 Felix Nützel

from queue import Queue
from threading import Thread

from slack_sdk.errors import SlackApiError

from base_agent import BaseAgent
from slack_sdk import WebClient
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt import App
import re
from dotenv import load_dotenv
import os

load_dotenv("../tokens.env")
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SIGNING_SECRET = os.getenv("SIGNING_SECRET")


class QAAgent(BaseAgent):

    def __init__(self):
        super().__init__()
        self.app = App(token=SLACK_TOKEN)
        self.client = WebClient(token=SLACK_TOKEN)
        self.handler = SocketModeHandler(self.app, SLACK_APP_TOKEN)

        # Create a dictionary to hold say functions for each user
        self.say_functions = {}

        # Create a queue to hold responses
        self.response_queue = Queue()

        # Create a worker thread to send responses
        self.response_worker = Thread(target=self.send_responses)
        self.response_worker.start()

    def send_responses(self):
        while True:
            # Get a response from the queue and send it
            response = self.response_queue.get()
            user_id, answer = response
            say = self.say_functions.get(user_id)
            if say is not None:
                say(answer)

    def receive_question(self, question, user_id):
        self.api_interface.listen_for_requests(question, self, user_id)

    def receive_answer(self, answer, user_id):
        # Put the answer and user_id in the queue instead of sending it directly
        self.response_queue.put((user_id, answer))

    def process_question(self, body, say):
        text = body['event']['text']
        user_id = body['event']['user']
        print(text)

        # Store the say function for this user
        self.say_functions[user_id] = say

        # Use a separate thread to call receive_question
        thread = Thread(target=self.receive_question, args=(text, user_id))
        thread.start()

    def start(self):
        self.handler.app.message(re.compile('.*'))(self.process_question)
        self.handler.start()

    def delete_messages(self, channel_id):

        # Get conversation history
        result = self.client.conversations_history(channel=channel_id)

        messages = result.data.get('messages')

        # Loop through all messages
        for msg in messages:
            try:
                # If it is a bot message...
                if msg.get('bot_profile') is not None:
                    ts = msg.get('ts')
                    # ...delete a message
                    self.client.chat_delete(
                        channel=channel_id,
                        ts=ts
                    )
                    print(f"Deleted bot message with ts={ts}")
            except SlackApiError as e:
                print(f"Error deleting message: {e}")


if __name__ == '__main__':
    agent = QAAgent()
    agent.start()
