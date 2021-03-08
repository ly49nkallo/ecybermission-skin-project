import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(lat, lon, exclude, lang="en"):
    # Contact API
    try:
        with open("./apikey.txt", encoding="utf-8") as f:
            api_key = f.readline()
            f.close()
        #  https://openweathermap.org/api/one-call-api
        if exclude:
            url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude={exclude}&lang={lang}&appid={api_key}"
        else:
            url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&lang={lang}&appid={api_key}"
        
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None
    try:
        quote = response.json()
        quote >> response.json
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }
    except (KeyError, TypeError, ValueError):
        return None

