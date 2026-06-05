from flask import Flask, redirect, url_for, session, request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import base64
from googletrans import Translator
from gtts import gTTS

app = Flask(__name__)
app.secret_key = "supersecretkey"

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

CLIENT_SECRETS_FILE = "client_secret_6226698.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


@app.route("/")
def home():
    return "<h2>Tamil Voice Mail App</h2><a href='/login'>Login with Google</a>"


@app.route("/login")
def login():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri="http://127.0.0.1:5000/callback"
    )

    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true"
    )

    session["state"] = state
    return redirect(auth_url)


@app.route("/callback")
def callback():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=session["state"],
        redirect_uri="http://127.0.0.1:5000/callback"
    )

    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials

    session["credentials"] = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }

    return redirect(url_for("read_email"))


@app.route("/read_email")
def read_email():
    credentials = Credentials(**session["credentials"])
    service = build("gmail", "v1", credentials=credentials)

    results = service.users().messages().list(
        userId="me",
        maxResults=1
    ).execute()

    messages = results.get("messages", [])

    if not messages:
        return "No emails found."

    msg = service.users().messages().get(
        userId="me",
        id=messages[0]["id"]
    ).execute()

    payload = msg["payload"]
    body = ""

    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                body = base64.urlsafe_b64decode(
                    part["body"]["data"]
                ).decode(errors="ignore")
                break
    else:
        body = base64.urlsafe_b64decode(
            payload["body"]["data"]
        ).decode(errors="ignore")

    # 🔥 Translate to Tamil
    translator = Translator()
    translated = translator.translate(body, dest="ta")
    tamil_text = translated.text

    # 🔊 Create Tamil Voice
    tts = gTTS(text=tamil_text, lang="ta")
    tts.save("voice.mp3")

    # 🔥 Windows auto play

    return f"<h3>Tamil Meaning:</h3><pre>{tamil_text}</pre>"


if __name__ == "__main__":
    app.run(debug=True)

