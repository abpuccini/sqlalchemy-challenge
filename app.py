# Set up
import numpy as np
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

# Database set up
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Flask set up
app = Flask(__name__)

# Flask route

## Home route
@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Welcome to Climate API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end><br/>"
    )

## Precipitation rount
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all precipitation and date"""
    # Query all passengers
    results = session.query(Measurement.date, Measurement.prcp).all()

    session.close()

    # Create a dictionary from the row data and append to a list of all_prpc
    all_prcp = []
    for date, prcp in results:
        prcp_dict = {}
        prcp_dict['Date'] = date
        prcp_dict['Precipitation'] = prcp
        all_prcp.append(prcp_dict)

    return jsonify(all_prcp)

## Stations route 
@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all stations"""
    # Query all stations
    results = session.query(Measurement.station, Station.name).filter(Measurement.station == Station.station)\
                                                              .distinct().all()

    session.close()

    # Create a dictionary from the row data and append to a list of all_stn
    all_stn = []
    for stn_id, stn_name in results:
        stn_dict = {}
        stn_dict['Station ID'] = stn_id
        stn_dict['Stantion Name'] = stn_name
        all_stn.append(stn_dict)

    return jsonify(all_stn)

## TOBS route
@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all TOBS"""
    # Last data point
    last_date_query = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    last_date_str = last_date_query[0]
    last_date = dt.datetime.strptime(last_date_str, '%Y-%m-%d').date()

    # 1 year ago from the last data point
    yr_ago_date = last_date - dt.timedelta(days=365)
    yr_ago_date_str = yr_ago_date.strftime('%Y-%m-%d')

    # Get the most active station
    most_active = session.query(Measurement.station, func.count(Measurement.station))\
                                .group_by(Measurement.station)\
                                .order_by(func.count(Measurement.station).desc())\
                                .first()

    # Query all the data related to the most active station in the past year
    results = session.query(Measurement.date, Measurement.tobs)\
                    .filter(Measurement.date <= last_date_str)\
                    .filter(Measurement.date >= yr_ago_date_str)\
                    .filter(Measurement.station == most_active[0])\
                    .all()

    session.close()

    # Create a dictionary from the row data and append to a list of all_stn
    act_stn = []
    for act_date, act_tobs in results:
        act_stn_dict = {}
        act_stn_dict['Date'] = act_date
        act_stn_dict['TOBS'] = act_tobs
        act_stn.append(act_stn_dict)

    return jsonify(act_stn)

## Start Date route
@app.route("/api/v1.0/<start>")
def start_date(start):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Query all the data related to the most ctive station in the past year
    results = session.query(func.min(Measurement.tobs), 
                            func.max(Measurement.tobs), 
                            func.avg(Measurement.tobs))\
                            .filter(Measurement.date >= start).all()

    last_date_query = session.query(Measurement.date).order_by(Measurement.date.desc()).first()

    session.close()
    
    # Create a dictionary from the row data and append to a list of strt_data
    strt_data = [
        {
            'Start Date': start,
            'End Date': last_date_query[0]
        }
    ]
    for tmin, tmax, tavg in results:
        strt_data_dict = {}
        strt_data_dict['TMIN'] = tmin
        strt_data_dict['TMAX'] = tmax
        strt_data_dict['TAVG'] = tavg
        strt_data.append(strt_data_dict)

    return jsonify(strt_data)

## Start and End Date route
@app.route("/api/v1.0/<start>/<end>")
def period(start, end):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Query all the data related to the most ctive station in the past year
    results = session.query(func.min(Measurement.tobs), 
                            func.max(Measurement.tobs), 
                            func.avg(Measurement.tobs))\
                            .filter(Measurement.date >= start)\
                            .filter(Measurement.date <= end).all()

    session.close()

    # Create a dictionary from the row data and append to a list of period_data
    period_data = [
        {
            'Start Date': start,
            'End Date': end
        }
    ]
    
    for tmin, tmax, tavg in results:
        period_data_dict = {}
        period_data_dict['TMIN'] = tmin
        period_data_dict['TMAX'] = tmax
        period_data_dict['TAVG'] = tavg
        period_data.append(period_data_dict)
        if tavg == None:
            return jsonify({"error": f"{start} to {end} not found."}), 404 
        else:
            return jsonify(period_data)

##  app.run statement here
if __name__ == "__main__":
    app.run(debug=True)
