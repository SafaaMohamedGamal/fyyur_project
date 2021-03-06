#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    artists = db.relationship("Artist", secondary="shows")
    genres = db.relationship("Genre", backref="venues")


class Artist(db.Model):
    __tablename__ = 'Artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    # genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    venues = db.relationship('Venue', secondary="shows")
    genres = db.relationship("Genre", backref="artists")


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
    __tablename__="shows"
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    artist = db.relationship("Artist", backref=db.backref("shows", cascade="all, delete"))
    venue = db.relationship("Venue", backref=db.backref("shows", cascade="all, delete"))

class Genre(db.Model):
    __tablename__ = "genres"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  city_state = db.session.query(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
  for value in city_state:
      venues = Venue.query.filter_by(city=value[0]).filter_by(state=value[1]).all()
      venues_data = []
      for venue in venues:
          venues_data.append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": len(venue.shows),
          })
      data.append({
        "city": value[0],
        "state": value[1],
        "venues": venues_data
      })
  return render_template('pages/venues.html', areas=data);


@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  venues = Venue.query.filter(Venue.name.ilike('%'+request.form.get('search_term', '')+'%')).all()
  count_venues = len(venues)
  data = []
  for venue in venues:
      num_upcoming_shows =  Show.query.join(Venue, Show.venue_id==venue.id).filter(Show.start_time>datetime.now()).count()
      venue_item = {
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": num_upcoming_shows,
      }
      data.append(venue_item)
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  response={
    "count": count_venues,
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)
  data = []
  # for artist in artists:
  genres = []
  if venue.genres is not None:
      for genre in venue.genres:
          genres.append(genre.name)
  past_shows = []
  finished_shows = Show.query.join(Venue, Show.venue_id==Venue.id)\
    .filter(Venue.id==venue_id).filter(Show.start_time<=datetime.now()).all()
  if finished_shows is not None:
      for show in finished_shows:
          artist_Obj = {
          "artist_id": show.artist.id,
          "artist_name": show.artist.name,
          "artist_image_link": show.artist.image_link,
          "start_time": str(show.start_time)
          }
          past_shows.append(artist_Obj)
  upcoming_shows =[]
  past_shows_count = Show.query.join(Venue, Show.venue_id==Venue.id)\
    .filter(Venue.id==venue_id).filter(Show.start_time<=datetime.now()).count()
  upcoming_shows_count = Show.query.join(Venue, Show.venue_id==Venue.id)\
    .filter(Venue.id==venue_id).filter(Show.start_time>datetime.now()).count()
  comming_shows = Show.query.join(Venue, Show.venue_id==Venue.id)\
    .filter(Venue.id==venue_id).filter(Show.start_time>datetime.now()).all()
  if comming_shows is not None:
      for show in comming_shows:
          show_item = {
          "artist_id": show.artist.id,
          "artist_name": show.artist.name,
          "artist_image_link": show.artist.image_link,
          "start_time": str(show.start_time)
          }
          upcoming_shows.append(show_item)
  obj ={
  'id': venue.id,
  "name": venue.name,
  "genres": genres,
  "address": venue.address,
  "city": venue.city,
  "state": venue.state,
  "phone": venue.phone,
  "website": '',
  "facebook_link": venue.facebook_link,
  "seeking_talent": True,
  "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
  "image_link": venue.image_link,
  "past_shows": past_shows,
  "upcoming_shows": upcoming_shows,
  "past_shows_count": past_shows_count,
  "upcoming_shows_count": upcoming_shows_count,
  }
  # data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]
  return render_template('pages/show_venue.html', venue=obj)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    body = {
    'name' : request.form.get('name'),
    'city' : request.form.get('city'),
    'state' : request.form.get('state'),
    'address' : request.form.get('address'),
    'phone' : request.form.get('phone'),
    'image_link' : request.form.get('image_link'),
    'facebook_link' : request.form.get('facebook_link'),
    'genres' : request.form.getlist('genres')
    }
    try:
  # TODO: insert form data as a new Venue record in the db, instead
        venue = Venue()
        venue.name = body['name']
        venue.city = body['city']
        venue.state = body['state']
        venue.address = body['address']
        venue.phone = body['phone']
        venue.image_link = body['image_link']
        venue.facebook_link = body['facebook_link']
        for item in body['genres']:
            genre = Genre(name=item)
            genre.venues = venue
        db.session.add(venue)
        db.session.commit()
  # TODO: modify data to be the data object returned from db insertion
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()
  # on successful db insert, flash success
  # flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
    if error:
        flash('An error occurred. Venue ' + body['name'] + ' could not be listed.')
    else:
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  return render_template('pages/artists.html', artists=Artist.query.all())


@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  artists = Artist.query.filter(Artist.name.ilike('%'+request.form.get('search_term', '')+'%')).all()
  count_artists = len(artists)
  data = []
  for artist in artists:
      num_upcoming_shows =  Show.query.join(Artist, Show.artist_id==artist.id).filter(Show.start_time>datetime.now()).count()
      artist_item = {
        "id": artist.id,
        "name": artist.name,
        "num_upcoming_shows": num_upcoming_shows,
      }
      data.append(artist_item)
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  response={
    "count": count_artists,
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  artist = Artist.query.get(artist_id)
  data = []
  # for artist in artists:
  genres = []
  if artist.genres is not None:
      for genre in artist.genres:
          genres.append(genre.name)
  past_shows = []
  finished_shows = Show.query.join(Artist, Show.artist_id==Artist.id)\
    .filter(Artist.id==artist_id).filter(Show.start_time<=datetime.now()).all()
  if finished_shows is not None:
      for show in finished_shows:
          venue_Obj = {
          "venue_id": show.venue.id,
          "venue_name": show.venue.name,
          "venue_image_link": show.venue.image_link,
          "start_time": str(show.start_time)
          }
          past_shows.append(venue_Obj)
  upcoming_shows =[]
  past_shows_count = Show.query.join(Artist, Show.artist_id==Artist.id)\
    .filter(Artist.id==artist_id).filter(Show.start_time<=datetime.now()).count()
  upcoming_shows_count = Show.query.join(Artist, Show.artist_id==Artist.id)\
    .filter(Artist.id==artist_id).filter(Show.start_time>datetime.now()).count()
  comming_shows = Show.query.join(Artist, Show.artist_id==Artist.id)\
    .filter(Artist.id==artist_id).filter(Show.start_time>datetime.now()).all()
  if comming_shows is not None:
      for show in comming_shows:
          show_item = {
          "venue_id": show.venue.id,
          "venue_name": show.venue.name,
          "venue_image_link": show.venue.image_link,
          "start_time": str(show.start_time)
          }
          upcoming_shows.append(show_item)
  obj ={
  'id': artist.id,
  "name": artist.name,
  "genres": genres,
  "city": artist.city,
  "state": artist.state,
  "phone": artist.phone,
  "website": '',
  "facebook_link": artist.facebook_link,
  "seeking_venue": True,
  "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
  "image_link": artist.image_link,
  "past_shows": past_shows,
  "upcoming_shows": upcoming_shows,
  "past_shows_count": past_shows_count,
  "upcoming_shows_count": upcoming_shows_count,
  }
  return render_template('pages/show_artist.html', artist=obj)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

    error = False
    body = {
    'name' : request.form.get('name'),
    'city' : request.form.get('city'),
    'state' : request.form.get('state'),
    'address' : request.form.get('address'),
    'phone' : request.form.get('phone'),
    'image_link' : request.form.get('image_link'),
    'facebook_link' : request.form.get('facebook_link'),
    'genres' : request.form.getlist('genres')
    }
    try:
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
        artist = Artist()
        artist.name = body['name']
        artist.city = body['city']
        artist.state = body['state']
        artist.address = body['address']
        artist.phone = body['phone']
        artist.image_link = body['image_link']
        artist.facebook_link = body['facebook_link']
        for item in body['genres']:
            genre = Genre(name=item)
            genre.artists = artist
        db.session.add(artist)
        db.session.commit()
  # TODO: modify data to be the data object returned from db insertion
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()
  # on successful db insert, flash success
  # flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
    if error:
        flash('An error occurred. Artist ' + body['name'] + ' could not be listed.')
    else:
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  upcoming_shows = Show.query.order_by(Show.start_time.desc()).all()
  # upcoming_shows = Show.query.filter(Show.start_time>datetime.now()).all()
  data = []
  for show in upcoming_shows:
      data.append({
        "venue_id": show.venue.id,
        "venue_name": show.venue.name,
        "artist_id": show.artist.id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": str(show.start_time)
      })
  print(data)
  print(upcoming_shows)
  return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  error = False
  body = {
  'artist_id' : request.form.get('artist_id'),
  'venue_id' : request.form.get('venue_id'),
  'start_time' : request.form.get('start_time'),
  }
  try:
      show = Show()
      show.artist_id = body['artist_id']
      show.venue_id = body['venue_id']
      show.start_time = body['start_time']
      db.session.add(show)
      db.session.commit()
  except:
      db.session.rollback()
      error = True
  finally:
      db.session.close()
  # on successful db insert, flash success
  if error:
      flash('An error occurred. Show could not be listed.')
  else:
      flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
