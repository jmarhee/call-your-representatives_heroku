from flask import Flask, render_template, request, jsonify
import os
import requests
from twilio.rest import Client
from twilio.jwt.client import ClientCapabilityToken
from twilio.twiml.voice_response import VoiceResponse, Dial
import urllib
import base64
import random, string

# Loading these variables will come from another module at some point.
TWILIO_SID = os.environ['twilio_sid']
TWILIO_TOKEN = os.environ['twilio_token']
TWILIO_TWIML_SID = os.environ['twilio_twiml_sid']
NUMBERS_OUTBOUND = os.environ['numbers_outbound']
GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']

app = Flask(__name__)

# These will need to go into their own module at some point.
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
        officials.append({'name': name, 'office': office, 'phone': phone, 'unformatted_phone': unformatted_phone, 'urls': urls, 'party': party, 'photo': photo, 'p_phone': p_phone, 'p_unformatted_phone': p_unformatted_phone})
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
    nums_found = []
    for r in reps:
        if unformatted_number in r['unformatted_phone']:
            nums_found.append(r['name'])
            photoUrl = r['photo']
    if len(nums_found) != 0:
        return { 'status': 'OK', 'zipCode': zipCode, 'name': nums_found[0], 'photo': photoUrl }
    else:
        return { 'status': 'FAILED' }

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
    dict = request.form
    for value in dict:
        if dict[value].startswith('number'):
            number = dict[value].split(":")[-1]
    phone_number = request.args.get('number:%s' %(number)) or default_client
    dial = Dial(callerId=NUMBERS_OUTBOUND)
    print(number)
    dial.number(number)
    return str(response.append(dial))