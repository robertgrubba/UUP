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
        airspaceReservations = None
    
        if r['properties']:
            if 'airspaceElementType' in r['properties']:
                airspace_type = r['properties']['airspaceElementType']
            if 'designator' in r['properties']:
                designator = r['properties']['designator']
            if 'section' in r['properties']:
                section = r['properties']['section']
            if 'airspaceReservations' in r['properties']:
                airspaceReservations = r['properties']['airspaceReservations']
            
            
            airspace_q = Airspace.query.filter_by(designator=designator,typ=airspace_type).first()
            if not airspace_q:
                new_airspace = Airspace(designator=designator,typ=airspace_type)
                db.session.add(new_airspace)
                airspace_q = new_airspace

            section_q = Section.query.filter_by(name=section).first()
            if not section_q:
                new_section = Section(name=section)
                db.session.add(new_section)
                section_q = new_section

            for reservation in airspaceReservations:
                remarks = None
                if 'remarks' in reservation:
                    remarks = reservation['remarks']
                start = datetime.datetime.strptime(reservation['startDate'],'%Y-%m-%dT%H:%M:%SZ')
                end = datetime.datetime.strptime(reservation['endDate'],'%Y-%m-%dT%H:%M:%SZ')
                reservation_q = Reservation.query.filter_by(start=start,end=end,lower_altitude=reservation['lowerAltitude'],upper_altitude=reservation['upperAltitude'],altitude_unit=reservation['altitudeUnit'],remarks=remarks).first()
                if not reservation_q:
                    status_q = Status.query.filter_by(name=reservation['reservationStatus']).first()
                    if not status_q:
                        new_status = Status(name=reservation['reservationStatus'])
                        db.session.add(new_status)
                        status_q = new_status

                    unit_q = Unit.query.filter_by(name=reservation['unit']).first()
                    if not unit_q:
                        new_unit = Unit(name=reservation['unit'])
                        db.session.add(new_unit)
                        unit_q = new_unit

                    new_reservation = Reservation(start=start,end=end,lower_altitude=reservation['lowerAltitude'],upper_altitude=reservation['upperAltitude'],altitude_unit=reservation['altitudeUnit'],remarks=remarks)
                    db.session.add(new_reservation)
                    unit_q.reservations.append(new_reservation)
                    status_q.reservations.append(new_reservation)
                    airspace_q.reservations.append(new_reservation)
                    section_q.reservations.append(new_reservation)

                    db.session.commit()
                else:
                    if reservation['reservationStatus']!='PLANNED':
                        status_q = Status.query.filter_by(name=reservation['reservationStatus']).first()
                        if not status_q:
                            new_status = Status(name=reservation['reservationStatus'])
                            db.session.add(new_status)
                            status_q = new_status

                        reservation_q.status=status_q
                        db.session.commit()
    return jsonify(status=200)




