import os

from threading import Thread
from time import sleep

import utils

from dotenv import load_dotenv
from flask import Flask
from flask import request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse


load_dotenv()
# Twilio settings
account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]
client = Client(account_sid, auth_token)


def generate_and_send_reply(messages, sender_contact, receiver_contact):
    """ """
    output = utils.generate_response(messages)["choices"][0]["message"]["content"]
    # Divide output into 1500 character chunks due to WhatsApp character limit of 1600 chars
    outputs = [output[i : i + 1500] for i in range(0, len(output), 1500)]
    # Send message
    for output in outputs:
        message = client.messages.create(body=output, from_=sender_contact, to=receiver_contact)
        sleep(0.5)


def generate_reply(incoming_message: str, from_contact: str, to_contact: str) -> str:
    """
    Basic approach to prase message text and return a response
    Supports only two commands: explain and activity

    Args:
        incoming_message (str): message text

    Returns:
        str: response text
    """
    if "explain" in incoming_message.lower():
        messages = [
            {
                "role": "user",
                "content": f"###Instructions###\nYou are a helpful, kind, intelligent and polite early-year educator. Your task is to explain a concept to a 3 year old child. You must explain it in simple words that a young kid would understand. You must also be patient and never offend or be aggressive. Gendered language and any adjectives about the kid are strictly prohibited.\n\n###Question###\n{incoming_message}\n\n###Answer###\n",
            }
        ]
        response = utils.generate_response(messages)
        return response["choices"][0]["message"]["content"]
    elif "activities" in incoming_message.lower():
        messages = utils.activities_prompt(incoming_message)
        thr = Thread(target=generate_and_send_text, args=[messages, from_contact, to_contact])
        thr.start()
        return "Thank you for your question. I am thinking..."
    else:
        return 'Write "Explain <your question>" to explain a concept to a 3-year old \n\n or \n\n "Activities <your topic>" to get activity ideas'


app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello, World!"


@app.route("/text", methods=["POST"])
def text_reply():
    """Respond to incoming messages"""
    reply = generate_reply(
        incoming_message=request.form.get("Body"),
        sender_contact=request.form.get("From"),
        receiver_contact=request.form.get("To"),
    )
    resp = MessagingResponse()
    resp.message(reply)
    return str(resp)


if __name__ == "__main__":
    app.run(debug=True)
