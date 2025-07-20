from flask import Flask, jsonify  # Flask web framework for building APIs, jsonify for converting python data to JSON
from bluesky import simulation  # bluesky flight simulation model

backend = Flask(__name__)  # creates flask webserver
sim = simulation.Sim()  # creates a bluesky simulation object


