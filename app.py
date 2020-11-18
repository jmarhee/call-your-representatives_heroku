from flask import Flask, render_template, request, jsonify, redirect
from flask_api import status
import os
import requests
from twilio.rest import Client
from twilio.jwt.client import ClientCapabilityToken
from twilio.twiml.voice_response import VoiceResponse, Dial
import urllib
import base64
import random, string, sys
from cryptography.fernet import Fernet

# Loading these variables will come from another module at some point.
TWILIO_SID = os.environ['twilio_sid']
TWILIO_TOKEN = os.environ['twilio_token']
TWILIO_TWIML_SID = os.environ['twilio_twiml_sid']
NUMBERS_OUTBOUND = os.environ['numbers_outbound']
GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
FERNET_KEY = Fernet.generate_key()

app = Flask(__name__)

# These will need to go into their own module at some point.
def encrypt(message: bytes, key: bytes) -> bytes:
    return Fernet(key).encrypt(message)

def decrypt(token: bytes, key: bytes) -> bytes:
    return Fernet(key).decrypt(token)

def get_reps(zipCode):
    officials = []
    r = requests.get("https://www.googleapis.com/civicinfo/v2/representatives?address=%s&levels=country&levels=regional&roles=legislatorUpperBody&roles=legislatorLowerBody&offices=true&key=%s" % (zipCode, GOOGLE_API_KEY))
    for index, item in enumerate(r.json()['officials']):
        if index == 2:
            index = -1
        elif index == 1:
            index = 0
        name = item['name']
        office = r.json()['offices'][index]['name']
        party = item['party']
        photo = item['photoUrl']
        phone = "+1" + item['phones'][0].replace("(","").replace(")","").replace("-","").replace(" ","")
        unformatted_phone = item['phones'][0]
        p_phone = urllib.parse.quote(phone)
        p_unformatted_phone = urllib.parse.quote(unformatted_phone)
        p_name = urllib.parse.quote(name)
        urls = item['urls'][0]
        phone_unencoded = encrypt(phone.encode(), FERNET_KEY)
        encrypted_phone = base64.b64encode(phone_unencoded).decode('ascii')
        officials.append({'name': name, 'office': office, 'phone': phone, 'encrypted_phone': encrypted_phone, 'unformatted_phone': unformatted_phone, 'urls': urls, 'party': party, 'photo': photo, 'p_phone': p_phone, 'p_unformatted_phone': p_unformatted_phone})
    return officials

def location(zipCode):
    loc = requests.get("https://maps.googleapis.com/maps/api/geocode/json?address=%s&sensor=true&key=%s" % (zipCode, GOOGLE_API_KEY))
    place = loc.json()['results'][0]['address_components'][2]['long_name'] + ", "+ loc.json()['results'][0]['address_components'][-2]['short_name']
    return { "name": place }

def randomword(length):
   letters = string.ascii_lowercase
   return ''.join(random.choice(letters) for i in range(length))

default_client = "call-your-representatives-%s" % (randomword(8))
validation = default_client + "_" + randomword(20)

def numberVerify(zipCode, unformatted_number):
    reps = get_reps(zipCode)
    for r in reps:
        if unformatted_number in r['phone']:
            photoUrl = r['photo']
            return { 'status': 'OK', 'number': unformatted_number, 'zipCode': zipCode, 'photo': photoUrl }
        else:
            return { 'status': 'Invalid.', 'number': NUMBERS_OUTBOUND }

@app.route('/')
def hello_world():
    return render_template('index.html')

@app.route('/reps', methods=['GET', 'POST'])
def reps():
    zipCode = request.form['zip_code']
    location_name = location(zipCode)
    representatives = get_reps(zipCode)
    client = default_client
    return render_template('call.html', client=client, zipCode=zipCode, location=location_name, representatives=representatives)

@app.route('/token', methods=['GET'])
def get_token():
    capability = ClientCapabilityToken(TWILIO_SID, TWILIO_TOKEN)
    capability.allow_client_outgoing(TWILIO_TWIML_SID)
    capability.allow_client_incoming(default_client)
    token = capability.to_jwt()
    # encoded = base64.encodestring(token)
    return token

@app.route("/voice", methods=['POST'])
def call():
    """Returns TwiML instructions to Twilio's POST requests"""
    response = VoiceResponse()
    number = ""
    zipCode = ""
    dict = request.form
    for value in dict:
        if dict[value].startswith('number'):
            number = dict[value].split(":")[-1]
        if dict[value].startswith('zipCode'):
            zipCode = dict[value].split(":")[-1]
    phone_number = number #or default_client
    zip_code = zipCode
    print(phone_number)
    print(zip_code)
    # undecoded_phone = number
    # base64_bytes = undecoded_phone.encode('ascii')
    # message_bytes = base64.b64decode(base64_bytes)
    # phone_number = str(decrypt(message_bytes, FERNET_KEY)).replace("b'","").replace("'","")
    dial = Dial(callerId=NUMBERS_OUTBOUND)
    try:
        dial.number(numberVerify(zip_code, phone_number)['number'])
    except:
        dial.number(NUMBERS_OUTBOUND)
    return str(response.append(dial))