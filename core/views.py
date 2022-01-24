import os
from flask import Blueprint, render_template, jsonify
import requests,json 
from sqlalchemy import extract,asc
from models import *
import datetime
import urllib3
from pprint import pprint

core_bp = Blueprint('core_bp',__name__,template_folder='templates')

@core_bp.context_processor
def inject_now():
        return {'now': datetime.datetime.utcnow()}

@core_bp.route('/')
def index():
    days = Reservation.query.group_by(extract('year',Reservation.start), extract('month',Reservation.start), extract('day',Reservation.start)).order_by(Reservation.start.desc()).all()
    return render_template('core/index.html',days=days)


@core_bp.route('/today/',defaults={'mapa': 0})
@core_bp.route('/today/<int:mapa>',defaults={'mapa': 0})
def today(mapa):
    today = datetime.date.today()
    return day_display(today.year,today.month,today.day,mapa)

@core_bp.route('/<int:year>/<int:month>/<int:day>/',defaults={'mapa': 0})
@core_bp.route('/<int:year>/<int:month>/<int:day>/<int:mapa>')
def day_display(year,month,day,mapa):
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    previous_reservations = Reservation.query.join(Airspace).filter(extract('year',Reservation.start)==yesterday.year,extract('month',Reservation.start)==yesterday.month, extract('day',Reservation.start)==yesterday.day, extract('day',Reservation.end)==datetime.date(year=year,month=month,day=day).day).order_by(asc(Airspace.designator)).all()
    active = Reservation.query.join(Airspace).filter(extract('year',Reservation.start)==year,extract('month',Reservation.start)==month, extract('day',Reservation.start)==day,Reservation.status.has(Status.name=="ACTIVATED")).order_by(asc(Airspace.designator)).all()
    other= Reservation.query.join(Airspace).filter(extract('year',Reservation.start)==year,extract('month',Reservation.start)==month, extract('day',Reservation.start)==day, Reservation.status.has(Status.name!="ACTIVATED")).order_by(asc(Airspace.designator)).all()
    key = os.environ.get('GOOGLEMAPSAPIKEY')
    if (yesterday or active or other):
        return render_template('core/reservations.html',reservations=active, other=other, yesterday=previous_reservations,year=year,month=month,day=day,key=key,mapa=mapa)
    else:
        return index()

@core_bp.route('/airspace/<string:name>/')
@core_bp.route('/airspace/<string:name>/<int:page>')
def airspace_reservations(name,page=1):
        per_page=50
        reservations = Reservation.query.join(Airspace).filter(Airspace.designator==name).order_by(Reservation.start.desc()).paginate(page,per_page,error_out=False)
        airspace = Airspace.query.filter(Airspace.designator==name).first()
        key = os.environ.get('GOOGLEMAPSAPIKEY')
        gfx = "./static/images/strefa_"+name+".png"
        http = urllib3.PoolManager()
        points = ""
        if (len(airspace.coordinates)>1 and not os.path.exists(gfx)):
            max_lat = airspace.coordinates[0].lat
            max_lon = airspace.coordinates[0].lon
            min_lat = airspace.coordinates[0].lat
            min_lon = airspace.coordinates[0].lon
            for point in airspace.coordinates:
                if point.lat > max_lat:
                    max_lat = point.lat
                if point.lat < min_lat:
                    min_lat = point.lat
                if point.lon > max_lon:
                    max_lon = point.lon
                if point.lon < min_lon:
                    min_lon = point.lon
                points = points +"|"+str(point.lat)+','+str(point.lon)

            center_lat = (max_lat + min_lat) / 2
            center_lon = (max_lon + min_lon) / 2
            url='http://maps.googleapis.com/maps/api/staticmap?key='+key+'&center='+str(center_lat)+','+str(center_lon)+'&zoom=10&size=600x600&maptype=terrain&sensor=false&path=color:red|weight:2|fillcolor:white'+points+"|"+str(airspace.coordinates[0].lat)+","+str(airspace.coordinates[0].lon)

            response = http.request('GET', url)
            f = open(gfx, 'wb')
            f.write(response.data)
            f.close()

        return render_template('core/airspace.html',reservations=reservations,name=name,airspace=airspace,key=key)

@core_bp.route('/airspaces/')
def airspaces():
    airspaces = Airspace.query.group_by(Airspace.typ,Airspace.designator).all()
    spaces = {} 
    for airspace in airspaces:
        spaces.setdefault(airspace.typ, []).append(airspace.designator)
    return render_template('core/airspaces.html',spaces=spaces)

