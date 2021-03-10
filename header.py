import os
import requests
import urllib.parse
import pgeocode
import pandas
import json

from flask import redirect, render_template, request, session
from functools import wraps


from werkzeug import exceptions


def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

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

def lookup_by_geocode(code, country='us'):
    #  https://pypi.org/project/pgeocode/
    nomi = pgeocode.Nominatim(country)
    if not RepresentsInt(code):
        return None
    pc = nomi.query_postal_code(code).to_dict()
    if pc["latitude"] and pc["longitude"]:
        return lookup(pc["latitude"], pc["longitude"])
    else:
        return "wat"

def lookup(lat, lon, exclude=None, lang="en", units="imperial"):
    # Contact API
    lat = round(lat, 2)
    lon = round(lon, 2)
    try:
        with open("./apikey.txt") as f:
            api_key = f.readline()
            f.close()
        #  https://openweathermap.org/api/one-call-api
        if exclude:
            url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude={exclude}&lang={lang}&units={units}&appid={api_key}"
        else:
            url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&lang={lang}&units={units}&appid={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return "request execptiopn"
    try:
        quote = response.json()
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(quote, f, ensure_ascii=False, indent=4)
        return quote
    except (KeyError, TypeError, ValueError):
        return "type error r"

"""import json
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)"""

#  https://stackoverflow.com/questions/12309269/how-do-i-write-json-data-to-a-file

def return_reapply(skintone, uvi, spf):
    if not RepresentsInt(uvi) or not RepresentsInt(skintone) or not RepresentsInt(spf):
        return Exception
    uvi = int(uvi)
    spf=int(spf)
    skintone=int(skintone)
    uv = (100/spf)
    weight = uvi * uv
    weight -= 0.1 * skintone
    
    if weight < 0:
        return None
    if weight < 8:
        return 4
    if weight < 17:
        return 3
    if weight < 30:
        return 2
    else:
        return 1

