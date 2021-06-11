from flask import Blueprint, render_template, jsonify
import requests,json 
from sqlalchemy import extract,asc
from models import *
import datetime

core_bp = Blueprint('core_bp',__name__,template_folder='templates')

@core_bp.context_processor
def inject_now():
        return {'now': datetime.datetime.utcnow()}

@core_bp.route('/')
def index():
    days = Reservation.query.group_by(extract('year',Reservation.start), extract('month',Reservation.start), extract('day',Reservation.start)).order_by(Reservation.start.desc()).all()
    return render_template('core/index.html',days=days)


@core_bp.route('/today/')
def today():
    today = datetime.date.today()
    return day_display(today.year,today.month,today.day)

@core_bp.route('/<int:year>/<int:month>/<int:day>/')
def day_display(year,month,day):
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    previous_reservations = Reservation.query.join(Airspace).filter(extract('year',Reservation.start)==yesterday.year,extract('month',Reservation.start)==yesterday.month, extract('day',Reservation.start)==yesterday.day, extract('day',Reservation.end)==datetime.date(year=year,month=month,day=day).day).order_by(asc(Airspace.designator)).all()
    active = Reservation.query.join(Airspace).filter(extract('year',Reservation.start)==year,extract('month',Reservation.start)==month, extract('day',Reservation.start)==day,Reservation.status.has(Status.name=="ACTIVATED")).order_by(asc(Airspace.designator)).all()
    other= Reservation.query.join(Airspace).filter(extract('year',Reservation.start)==year,extract('month',Reservation.start)==month, extract('day',Reservation.start)==day, Reservation.status.has(Status.name!="ACTIVATED")).order_by(asc(Airspace.designator)).all()
    if (yesterday or active or other):
        return render_template('core/reservations.html',reservations=active, other=other, yesterday=previous_reservations,year=year,month=month,day=day)
    else:
        return index()

@core_bp.route('/airspace/<string:name>/')
@core_bp.route('/airspace/<string:name>/<int:page>')
def airspace_reservations(name,page=1):
        per_page=50
        reservations = Reservation.query.join(Airspace).filter(Airspace.designator==name).order_by(Reservation.start.desc()).paginate(page,per_page,error_out=False)
        return render_template('core/airspace.html',reservations=reservations,name=name)

@core_bp.route('/airspaces/')
def airspaces():
    airspaces = Airspace.query.group_by(Airspace.typ,Airspace.designator).all()
    return render_template('core/airspaces.html',airspaces=airspaces)

