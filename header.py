import os
import requests
import urllib.parse
import pgeocode
import pandas
import flask_mail
import json
import SQL
import sqlite3
import datetime 

from flask import redirect, render_template, request, session
from functools import wraps

from werkzeug import exceptions

db = SQL.SQL("sqlite:///users.db")
wdb = SQL.SQL("sqlite:///weather_cache.db")

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



def lookup_by_geocode(code, user, country='us'):
    #  https://pypi.org/project/pgeocode/
    nomi = pgeocode.Nominatim(country)
    if not RepresentsInt(code):
        raise Exception
    pc = nomi.query_postal_code(code).to_dict()
    if pc["latitude"] and pc["longitude"]:
        return lookup(pc["latitude"], pc["longitude"], user)
    else:
        return "wat"

def lookup(lat, lon, user, exclude=None, lang="en", units="imperial"):
    # Contact API
    lat = round(lat, 2)
    lon = round(lon, 2)
    # look for data already in cache if exists
    user_offset = db.execute("SELECT offset FROM users WHERE id=?", user)[0]["offset"]
    dt = datetime.datetime.now() 
    utc_time = dt.replace(tzinfo = datetime.timezone.utc) 
    utc_timestamp = round(utc_time.timestamp())
    utc_hour = round(utc_timestamp/3600)*3600
    data = wdb.execute("SELECT * FROM hourly_forecast WHERE lat=? AND lon=? AND gmt_dt=?", lat, lon, utc_hour)
    #if data != None:
    #    d = data[0]
    #    return {"lat": d["lat"], "lon": d["lon"], "gmt_dt": d["gmt_dt"], "temp": d["temp"], "uvi": d["uvi"], "weather": [{"id": d["weather"]}], "clouds": d["clouds"]}
    #if :

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
        for hour in quote["hourly"]:
            if not wdb.execute("SELECT * FROM hourly_forecast WHERE lat=?, AND lon=?, AND gmt_dt=?", lat, lon, utc_hour):
                wdb.execute("INSERT INTO hourly_forecast (lat, lon, gmt_dt, temp, uvi, weather, clouds) VALUES (?,?,?,?,?,?,?)",
                    lat, lon, hour["dt"], hour["temp"], hour["uvi"], hour["weather"][0]["id"], hour["clouds"])
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(quote, f, ensure_ascii=False, indent=4)
        return quote
    except (KeyError, TypeError, ValueError):
        return "type error r"

"""import json
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)"""

