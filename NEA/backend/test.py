from flask import Flask, jsonify  # Flask web framework for building APIs, jsonify for converting python data to JSON
from bluesky import settings, traffic, navdb  # bluesky flight simulation model used to mimic flight, pip install "bluesky-simulator[full]", docs = 'https://github.com/TUDelft-CNS-ATM/bluesky/wiki/' 'https://github.com/TUDelft-CNS-ATM/bluesky/wiki/API-Reference', 'https://github.com/TUDelft-CNS-ATM/bluesky/blob/master/docs/python_demo.ipynb'
  # NavDatabase for managing navigation data like airports, runways, etc.
from flask_caching import Cache  # flask caching for caching responses to improve performance, pip install -U flask-caching
import random as random # used to generate random numbers
import requests # used to make HTTP requests, pip install requests
from threading import Lock # used to handle multiple requests simultaneously without conflicts, so that a request has to finish before another is made





help(navdb)
allaircraft = sorted(navdb.actypes.keys())
print("Common available aircraft types:")
for ac_type in allaircraft:
   if ac_type.startswith(('A3', 'B7', 'B7')):
        print(f"- {ac_type}")