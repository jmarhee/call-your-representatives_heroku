Call Your Representatives
=

[![Deploy](https://www.herokucdn.com/deploy/button.png)](https://heroku.com/deploy?template=https://github.com/public-engineering/call-your-representatives_heroku/tree/master)

Deploys a web-based dialer, to make Twilio-powered calls to Congress from the browser. 

If you'd like to support the project and help keep these services running:
<img src="https://img.shields.io/liberapay/patrons/~1532295.svg?logo=liberapay"> <img src="https://img.shields.io/liberapay/goal/~1532295.svg?logo=liberapay"> 

Setup
---

Requires Twilio voice-capable phone number, a TwiML application SID, and an account SID and Token. Also requires a Google Civic API key for representative lookup. These should all be set as environment variables for your application:

```bash
export twilio_sid=""
export twilio_token=""
export twilio_twiml_sid=""
export numbers_outbound="+12345678"
export GOOGLE_API_KEY=""
```

Build & Run
---
Can be built on any Docker host using this Dockerfile:

```
docker build -t callyourreps .
```

and run:

```bash
docker run -d -p 5000:5000 \
-e twilio_sid="" -e twilio_token="" \
-e twilio_twiml_sid="" -e numbers_outbound="" \
-e GOOGLE_API_KEY="" \
--name call-your-reps callyourreps
```

or run on Heroku using the button above. 


