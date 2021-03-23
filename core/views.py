from flask import Blueprint, render_template, jsonify
import requests,json 
#from models import Page
#from sqlalchemy import extract

core_bp = Blueprint('core_bp',__name__,template_folder='templates')

@core_bp.route('/')
def index():
        return render_template('index.html')


@core_bp.route('/echo/')
def echo():
    r = requests.get('https://airspace.pansa.pl/map-configuration/uup').text
    return jsonify(r)

@core_bp.route('/html/')
def html():
    r = json.loads(requests.get('https://airspace.pansa.pl/map-configuration/uup').text)
    return render_template('core/uup.html',uup=r)

