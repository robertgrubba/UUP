from flask import Blueprint, render_template, jsonify
import requests,json 
from sqlalchemy import extract
from models import *
import datetime

api_bp = Blueprint('api_bp',__name__)

@api_bp.route('/<int:year>/<int:month>/<int:day>/')
def day_display(year,month,day):
    active = Reservation.query.filter(extract('year',Reservation.start)==year,extract('month',Reservation.start)==month, extract('day',Reservation.start)==day,Reservation.status.has(Status.name=="ACTIVATED")).all()
    planned= Reservation.query.filter(extract('year',Reservation.start)==year,extract('month',Reservation.start)==month, extract('day',Reservation.start)==day, Reservation.status.has(Status.name!="ACTIVATED")).all()
    a = []
    for item in active:
        a.append({
            'designator':item.airspace.designator,
            'type':item.airspace.typ,
            'start':item.start.strftime("%Y-%m-%dT%H:%M:%S"),
            'end':item.end.strftime("%Y-%m-%dT%H:%M:%S"),
            'upper_alt':item.upper_altitude,
            'lower_alt':item.lower_altitude,
            'status':item.status.name
            })

    p = []
    for item in planned:
        p.append({
            'designator':item.airspace.designator,
            'type':item.airspace.typ,
            'start':item.start.strftime("%Y-%m-%dT%H:%M:%S"),
            'end':item.end.strftime("%Y-%m-%dT%H:%M:%S"),
            'upper_alt':item.upper_altitude,
            'lower_alt':item.lower_altitude,
            'status':item.status.name
            })

    if (active or planned):
        return jsonify(status=200,
                active=a,
                planned=p
                )
    else:
        return jsonify(status=204)
 

@api_bp.route('/airspace/<string:name>/')
def airspace_exists(name):
    airspace = Airspace.query.filter(Airspace.designator.ilike("%"+name+"%")).first()
    if airspace:
        return jsonify(status=200)
    else:
        return jsonify(status=404)

@api_bp.route('/update/')
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
                            reservation_q.start=start
                            reservation_q.end=end
                            reservation_q.lower_altitude=reservation['lowerAltitude']
                            reservation_q.upper_altitude=reservation['upperAltitude']
                            reservation_q.remarks=remarks
                            db.session.commit()
                            updated = updated+1

        if r['geometry']:
            airspace_q = Airspace.query.filter_by(designator=r['properties']['designator'],typ=r['properties']['airspaceElementType']).first()
            if len(airspace_q.coordinates)<2:
                for point in r['geometry']['coordinates'][0]:
                    lat = point[1]
                    lon = point[0]
                    coordinate = Coordinate.query.filter_by(lat=lat,lon=lon).first()
                    if not coordinate:
                        new_coordinate = Coordinate(lat=lat,lon=lon)
                        db.session.add(new_coordinate)
                        airspace_q.coordinates.append(new_coordinate)
                    else:
                        if not Airspace.query.filter(Airspace.designator==r['properties']['designator'],Airspace.typ==r['properties']['airspaceElementType'],Airspace.coordinates.contains(coordinate)).first():
                            airspace_q.coordinates.append(coordinate)
                    db.session.commit()

        processed = processed+1
    return jsonify(status=200,updated=updated,processed=processed)




