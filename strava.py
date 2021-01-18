import requests
import json
import boto3
import time
import os
from datetime import datetime

class Strava():
  def __init__(self):
    self.s3_client = boto3.client('s3')
    self.sns_client = boto3.client('sns')
    self.phone_number = str(os.environ['PHONE_NUMBER'])
    self.s3_bucket = 'pat-f-data'
    self.token_file = 'strava_tokens.json'
    self.client_id = int(os.environ['STRAVA_CLIENT_ID'])
    self.client_secret = str(os.environ['STRAVA_CLIENT_SECRET'])
    self.refresh_token = str(os.environ['STRAVA_REFRESH_TOKEN'])
    self.distance_goal = int(os.environ['DISTANCE_GOALS'])
    self.elevation_goal = int(os.environ['ELEVATION_GOALS'])


  def refresh(self):
    result = self.s3_client.get_object(Bucket=self.s3_bucket, Key='strava/{}'.format(self.token_file)) 
    self.strava_tokens = json.loads(result["Body"].read().decode())
    if self.strava_tokens['expires_at'] < time.time():
        response = requests.post(
                            url = 'https://www.strava.com/oauth/token',
                            data = {
                                    'client_id': self.client_id,
                                    'client_secret': self.client_secret,
                                    'grant_type': 'refresh_token',
                                    'refresh_token': self.strava_tokens['refresh_token']
                                    }
                        )
        new_strava_tokens = response.json()
        json_object = 'your_json_object here'
        self.s3_client.put_object(
            Body=json.dumps(new_strava_tokens),
            Bucket=self.s3_bucket,
            Key='strava/{}'.format(self.token_file)
        )
        self.strava_tokens = new_strava_tokens

  def get_activities(self):
    self.refresh()
    url = "https://www.strava.com/api/v3/activities"
    access_token = self.strava_tokens['access_token']
    r = requests.get(url + '?access_token=' + access_token + '&per_page=200' + '&page=1'+'&after=1609462860')
    return r.json()

  def calculate_totals(self):
    starva_data = self.get_activities()
    self.data = {
      'elevation_total':0.0,
      'distance_total': 0.0,
      'distance_percent_complete':0.0,
      'elevation_percent_complete':0.0,
      'distance_ahead':0.0,
      'elevation_ahead':0.0
    }
    for i in starva_data:
      self.data['elevation_total']+=i['total_elevation_gain']
      self.data['distance_total']+=self.meters_to_miles(i['distance'])
    
    self.data['distance_percent_complete'] = round(self.data['distance_total']/self.distance_goal*100,2)
    self.data['elevation_percent_complete'] = round(self.data['elevation_total']/self.elevation_goal*100,2)
    days = self.days_of_2021()
    expected_distance = self.distance_goal/365*days
    expected_elevation = self.elevation_goal/365*days
    self.data['distance_ahead'] = self.data['distance_total'] - expected_distance
    self.data['elevation_ahead'] = self.data['elevation_total'] - expected_elevation
    message = self.format_response()
    self.send_text(message)
  
  def meters_to_miles(self, meters):
    return meters * 0.00062137

  def days_of_2021(self):
    d1 = datetime.strptime("01 Jan 21", "%d %b %y")
    return (datetime.now() - d1).days

  def format_response(self):
    if self.data['distance_ahead'] > 0:
      dist_descriptor = 'Ahead'
    else:
      dist_descriptor = 'Behind'
    
    if self.data['elevation_ahead'] > 0:
      elv_descriptor = 'Ahead'
    else:
      elv_descriptor = 'Behind'

    return '''Distance {:.2f}  {}%\n{:.2f} Miles {}\n\nElevation {:.2f}  {}%\n{:.2f} Meters {}'''.format(
        self.data['distance_total'],
        self.data['distance_percent_complete'],
        self.data['distance_ahead'],
        dist_descriptor,
        self.data['elevation_total'],
        self.data['elevation_percent_complete'],
        self.data['elevation_ahead'],
        elv_descriptor,
      )
  
  def send_text(self, message):
    self.sns_client.publish(PhoneNumber = self.phone_number, Message=message )

def handler(event, context):
    st = Strava()
    res = st.calculate_totals()