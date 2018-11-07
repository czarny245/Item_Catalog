from flask import Flask
from app import site, auth, api
from site.site import mod
from auth.auth import mod
from api.api import mod

app = Flask(__name__)

app.register_blueprint(site.site.mod)
app.register_blueprint(auth.auth.mod)
app.register_blueprint(api.api.mod)
