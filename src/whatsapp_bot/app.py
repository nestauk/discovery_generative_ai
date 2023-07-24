from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv
import os
import utils
from threading import Thread
from time import sleep

load_dotenv()
# Twilio settings
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)

def background_worker(messages, from_contact, to_contact):
    """
    This function will run in background
    """
    output = utils.generate_response(messages)['choices'][0]['message']['content']
    # Divide output into 1500 character chunks
    outputs = [output[i:i+1500] for i in range(0, len(output), 1500)]
    # Send message
    for output in outputs:
        message = client.messages \
                        .create(
                            body=output,
                            from_=to_contact,
                            to=from_contact
                        )
        sleep(0.5)    


def message_parser(msg: str, from_contact: str, to_contact: str) -> str:
    """
    Basic approach to prase message text and return a response
    Supports only two commands: explain and activity
    
    Args:
        msg (str): message text
    
    Returns:
        str: response text
    """
    if "explain" in msg.lower():
        messages = [
            {"role": "user", "content": f"###Instructions###\nYou are a helpful, kind, intelligent and polite early-year educator. Your task is to explain a concept to a 3 year old child. You must explain it in simple words that a young kid would understand. You must also be patient and never offend or be aggressive. Gendered language and any adjectives about the kid are strictly prohibited.\n\n###Question###\n{msg}\n\n###Answer###\n"}
        ]
        response = utils.generate_response(messages)     
        return response['choices'][0]['message']['content']
    elif "activities" in msg.lower():
        messages = utils.activities_prompt(msg)
        thr = Thread(target=background_worker, args=[messages, from_contact, to_contact])
        thr.start()  
        return "Thank you for your question. I am thinking..."
    else:
        return 'Write "Explain <your question>" to explain a concept to a 3-year old \n\n or \n\n "Activities <your topic>" to get activity ideas'

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, World!"

@app.route("/sms", methods=['POST'])
def sms_reply():
    """Respond to incoming calls with a simple text message."""
    # Fetch the message
    msg = request.form.get('Body')
    # Create reply
    resp = MessagingResponse()
    # resp.message("You said: {}".format(msg))
    resp.message(message_parser(msg, request.form.get('From'), request.form.get('To')))
    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)