import os
import logging
from dotenv import load_dotenv
from IllustratedPrimer.Primer import Primer
import json

class AgentListener:
    def __init__(self, client):
        self.logger = logging.getLogger(__name__)
        self.stopped = False
        self.client = client
        self.primer = Primer()
        self.last_batch_messages = None

    def on_message(self, client, userdata, msg):
        try:
            message = json.loads(msg.payload)
            self.logger.debug(f"Received message: {message}")
        except json.JSONDecodeError:
            self.logger.error(f"Error decoding JSON: {msg.payload}")
            return

        output = {'messages': message}
        json_output = json.dumps(output)

        # Log the sent batched messages at INFO level
        self.logger.info(f"Sent messages: {json_output}")

        response = self.primer.generate_response(json_output)
        # response = "Hello, world!"

        # self.last_batch_messages = json_output

        topic = os.getenv('NOTIFICATION_TOPIC', 'your/input/topic/here')
        self.client.publish(topic, response)

    def stop(self):
        self.stopped = True