from flask import Blueprint, render_template, jsonify
import requests,json 
from sqlalchemy import extract
from models import *
import datetime

core_bp = Blueprint('core_bp',__name__,template_folder='templates')

@core_bp.context_processor
def inject_now():
        return {'now': datetime.datetime.utcnow()}

@core_bp.route('/')
def index():
        return render_template('core/index.html')


@core_bp.route('/echo/')
def echo():
    r = requests.get('https://airspace.pansa.pl/map-configuration/uup').text
    return jsonify(r)

@core_bp.route('/html/')
def html():
    r = json.loads(requests.get('https://airspace.pansa.pl/map-configuration/uup').text)
    return render_template('core/uup.html',uup=r)

@core_bp.route('/<int:year>/<int:month>/<int:day>/')
def day_display(year,month,day):
    reservations = Reservation.query.filter(extract('year',Reservation.start)==year,extract('month',Reservation.start)==month, extract('day',Reservation.start)==day,Reservation.status.has(Status.name=="ACTIVATED")).all()
    other= Reservation.query.filter(extract('year',Reservation.start)==year,extract('month',Reservation.start)==month, extract('day',Reservation.start)==day, Reservation.status.has(Status.name!="ACTIVATED")).all()
    if (reservations or other):
        return render_template('core/reservations.html',reservations=reservations, other=other)
    else:
        return render_template('index.html')


@core_bp.route('/update/')
def update():
    response = json.loads(requests.get('https://airspace.pansa.pl/map-configuration/uup').text)
    updated = 0    
    processed = 0
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
                    updated = updated+1
                else:
                    if reservation['reservationStatus']!='PLANNED':
                        status_q = Status.query.filter_by(name=reservation['reservationStatus']).first()
                        if not status_q:
                            new_status = Status(name=reservation['reservationStatus'])
                            db.session.add(new_status)
                            status_q = new_status
                        if reservation_q.status != status_q:
                            reservation_q.status = status_q
                            db.session.commit()
                            updated = updated+1
        processed = processed+1
    return jsonify(status=200,updated=updated,processed=processed)




