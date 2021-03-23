from flask import Blueprint, render_template, jsonify
import requests,json 
from models import *
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

@core_bp.route('/update/')
def update():
    response = json.loads(requests.get('https://airspace.pansa.pl/map-configuration/uup').text)
    
    for r in response:
        airspace_type = None
        designator = None
        section = None
        reservations = None
    
        if r['properties']:
            if 'airspaceElementType' in r['properties']:
                airspace_type = r['properties']['airspaceElementType']
            if 'designator' in r['properties']:
                designator = r['properties']['designator']
            if 'section' in r['properties']:
                section = r['properties']['section']
            if 'airspaceReservations' in r:
                airspaceReservations = r['properties']['airspaceReservations']

            print(airspace_type)
            print(designator)
            airspace_q = Airspace.query.filter_by(designator=designator,typ=airspace_type).first()
            if not airspace_q:
                new_airspace = Airspace(designator=designator,typ=airspace_type)
                db.session.add(new_airspace)
                airspace_q = new_airspace

            section_q = Section.query.filter_by(name=section).first()
            if not section:
                new_section = Section(name=section)
                db.session.add(new_section)
                section_q = new_section

            for reservation in airspaceReservations:
                reservation = Reservation.query.filter_by(start=reservation['startDate'],end=reservation['endDate'],lower_altitude=reservation['lowerAltitude'],upper_altitude=reservation['upperAltitude'],altitude_unit=reservation['altitudeUnit'],remarks=reservation['remarks']).first()
                if not reservation:
                    status_q = Status.query.filter_by(name=reservation['status']).first()

                    if not status_q:
                        new_status = Status(name=reservation['status'])
                        db.session.add(new_status)
                        status_q = new_status

                    unit_q = Unit.query.filter_by(name=reservation['unit']).first()
                    if not unit_q:
                        new_unit = Unit(name=reservation['unit'])
                        db.session.add(new_unit)
                        unit_q = new_unit

                    new_reservation = Reservation(start=reservation['startDate'],end=reservation['endDate'],lower_altitude=reservation['lowerAltitude'],upper_altitude=reservation['upperAltitude'],altitude_unit=reservation['altitudeUnit'],remarks=reservation['remarks'],status_id=status_q.id,airspace_id=airspace_q.id,section_id=section_q.id,unit_id=unit_q.id)
                    db.session.add(new_reservation)
                    db.session.commit()
                    
            return jsonify(status=200)
    return jsonify(status=500)




