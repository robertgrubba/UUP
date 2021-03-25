import datetime
from app import db
from sqlalchemy.sql import func

#db=SQLAlchemy()

class Airspace(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    designator = db.Column(db.String(10))
    typ = db.Column(db.String(6))
    reservations = db.relationship('Reservation',backref='airspace',lazy=True)

    def __repr__(self):
        return '<Airspace %r>' % self.id

class Section(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(10),unique=True)
    reservations = db.relationship('Reservation',backref='section',lazy=True)

    def __repr__(self):
        return '<Section %r>' % self.id

class Unit(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(10),unique=True)
    reservations = db.relationship('Reservation',backref='unit',lazy=True)

    def __repr__(self):
        return '<Unit %r>' % self.id

class Status(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(10))
    reservations = db.relationship('Reservation',backref='status',lazy=True)

    def __repr__(self):
        return '<Status %r>' % self.id

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime,nullable=False)
    end = db.Column(db.DateTime,nullable=False)
    lower_altitude = db.Column(db.String(10))
    upper_altitude = db.Column(db.String(10))
    altitude_unit = db.Column(db.String(4))
    remarks = db.Column(db.String(20))
    status_id = db.Column(db.Integer,db.ForeignKey('status.id'))
    airspace_id = db.Column(db.Integer,db.ForeignKey('airspace.id'))
    section_id = db.Column(db.Integer,db.ForeignKey('section.id'))
    unit_id = db.Column(db.Integer,db.ForeignKey('unit.id'))
    
    def __repr__(self):
        return '<Reservation %r>' % self.id


