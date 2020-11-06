# Set up
import numpy as np
import datetime as dt
import pandas as pd

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
        f"Welcome to Honolulu Climate API!<br/>"
        f"{'*'*30}<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start=YYYY-MM-DD<br/>"
        f"/api/v1.0/start=YYYY-MM-DD/end=YYYY-MM-DD<br/>"
    )

## Precipitation rount
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all precipitation and date"""
    # Query precipitation data
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
    most_active = session.query(Measurement.station, Station.name, func.count(Measurement.station))\
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

    # Create a dictionary from the row data and append to a list of the most active station
    act_stn = [
        {
            'StationID': most_active[0],
            'StationName': most_active[1]
        }
    ]
    for act_date, act_tobs in results:
        act_stn_dict = {}
        act_stn_dict['Date'] = act_date
        act_stn_dict['TOBS'] = act_tobs
        act_stn.append(act_stn_dict)

    return jsonify(act_stn)

## Start Date route
@app.route("/api/v1.0/start=<start>")
def start_date(start):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Query all the data related to the most ctive station in the past year
    results = session.query(func.min(Measurement.tobs), 
                            func.max(Measurement.tobs), 
                            func.avg(Measurement.tobs))\
                            .filter(Measurement.date >= start).all()

    first_date = session.query(Measurement.date).order_by(Measurement.date).first()
    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()

    session.close()
    
    # Creat a date list of dataset
    date_list = pd.date_range(start=first_date[0] ,end=last_date[0])

    # Create a dictionary from the row data and append to a list of strt_data
    strt_data = []
    for tmin, tmax, tavg in results:
        strt_data_dict = {
            'Start Date': start,
            'End Date': last_date[0]
        }
        strt_data_dict['TMIN'] = tmin
        strt_data_dict['TMAX'] = tmax
        strt_data_dict['TAVG'] = tavg
        strt_data.append(strt_data_dict)
        
        # If statement for date input in API search
        if start in date_list:
            return jsonify(strt_data)
        else:
            return jsonify({
                "error": f"Date: {start} not found. Date must be between {first_date[0]} and {last_date[0]}"
            }), 404    

## Start and End Date route
@app.route("/api/v1.0/start=<start>/end=<end>")
def period(start, end):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Query all the data related to the most ctive station in the past year
    results = session.query(func.min(Measurement.tobs), 
                            func.max(Measurement.tobs), 
                            func.avg(Measurement.tobs))\
                            .filter(Measurement.date >= start)\
                            .filter(Measurement.date <= end).all()

    first_date = session.query(Measurement.date).order_by(Measurement.date).first()
    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()

    session.close()

    # Create a dictionary from the row data and append to a list of period_data
    date_list = pd.date_range(start=first_date[0] ,end=last_date[0])

    period_data = []

    for tmin, tmax, tavg in results:
        period_data_dict = {
            'Start Date': start,
            'End Date': end
        }
        period_data_dict['TMIN'] = tmin
        period_data_dict['TMAX'] = tmax
        period_data_dict['TAVG'] = tavg
        period_data.append(period_data_dict)

        # If statement for date input in API search
        if start and end in date_list:
            if start <= end:
                return jsonify(period_data)
            elif start > end:
                return jsonify({
                    "error": f'{start} is greater than {end}'
                })                
        else:
            return jsonify({
                "error": f"Date: {start} to {end} not found. Date must be between {first_date[0]} and {last_date[0]}"
            }), 404    

        
##  app.run statement here
if __name__ == "__main__":
    app.run(debug=True)
