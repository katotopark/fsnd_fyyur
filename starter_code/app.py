import json
import dateutil.parser
import babel
import sys
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    Response,
    url_for,
)
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Venue(db.Model):
    __tablename__ = "Venue"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean())
    seeking_description = db.Column(db.String(120))

    def __repr__(self):
        return f"<Venue {self.id} {self.name}>"


class Artist(db.Model):
    __tablename__ = "Artist"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean())
    seeking_description = db.Column(db.String(120))

    def __repr__(self):
        return f"<Artist {self.id} {self.name} >"

    @property
    def search(self):
        return {
            "id": self.id,
            "name": self.name,
        }


class Show(db.Model):
    __tablename__ = "Show"
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(
        db.Integer, db.ForeignKey("Venue.id", ondelete="CASCADE"), nullable=False
    )
    artist_id = db.Column(
        db.Integer, db.ForeignKey("Artist.id", ondelete="CASCADE"), nullable=False
    )
    start_time = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Shows {self.id} {self.artist_id} {self.venue_id}>"


def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(value)
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale="en_US")


app.jinja_env.filters["datetime"] = format_datetime


@app.route("/")
def index():
    return render_template("pages/home.html")


#  Venues
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():
    data = []
    locations = db.session.query(Venue.city, Venue.state).distinct().all()
    for location in locations:
        venues = Venue.query.filter(
            Venue.city == location.city, Venue.state == location.state
        ).all()
        venue_data = []
        for venue in venues:
            num_upcoming_shows = (
                Show.query.filter(Show.venue_id == venue.id)
                .filter(Show.start_time > datetime.now())
                .count()
            )
            venue_data.append(
                {
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": num_upcoming_shows,
                }
            )
        data.append(
            {"city": location.city, "state": location.state, "venues": venue_data}
        )
    return render_template("pages/venues.html", areas=data)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    search = request.form.get("search_term", "")
    venues = Venue.query.filter(Venue.name.ilike("%" + search + "%")).all()
    venue_data = []
    for venue in venues:
        upcoming_shows = (
            Show.query.filter(Show.venue_id == venue.id)
            .filter(Show.start_time > datetime.now())
            .count()
        )
        venue_data.append(
            {"id": venue.id, "name": venue.name, "num_upcoming_shows": upcoming_shows}
        )
    response = {"count": len(venues), "data": venue_data}
    return render_template(
        "pages/search_venues.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    data = {}
    venue = Venue.query.get(venue_id)
    venue.genres = "".join(
        list(filter(lambda x: x != "{" and x != "}", venue.genres))
    ).split(",")
    past_shows = (
        Show.query.filter(Show.venue_id == venue_id)
        .filter(Show.start_time < datetime.now())
        .all()
    )
    upcoming_shows = (
        Show.query.filter(Show.venue_id == venue_id)
        .filter(Show.start_time > datetime.now())
        .all()
    )
    past_shows_data = []
    upcoming_shows_data = []
    for past_show in past_shows:
        artist = Artist.query.get(past_show.artist_id)
        past_shows_data.append(
            {
                "artist_id": artist.id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": past_show.start_time.strftime("%m/%d/%Y, %H:%M"),
            }
        )
    for upcoming_show in upcoming_shows:
        artist = Artist.query.get(upcoming_show.artist_id)
        upcoming_shows_data.append(
            {
                "artist_id": artist.id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": upcoming_show.start_time.strftime("%m/%d/%Y, %H:%M"),
            }
        )
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.city,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows_data,
        "upcoming_shows": upcoming_shows_data,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template("pages/show_venue.html", venue=data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    error = False
    form = VenueForm(obj=request.form)
    venue = Venue(
        name=form.name.data,
        city=form.city.data,
        state=form.state.data,
        address=form.address.data,
        phone=form.phone.data,
        image_link=form.image_link.data,
        genres=form.genres.data,
        facebook_link=form.facebook_link.data,
        website=form.website.data,
        seeking_talent=form.seeking_talent.data,
        seeking_description=form.seeking_description.data,
    )
    try:
        db.session.add(venue)
        db.session.commit()
        flash(f"Venue {venue.name} was successfully listed!")
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
        flash(f"An error occurred. Venue {venue.name} could not be listed.")
    finally:
        db.session.close()
    if not error:
        return render_template("pages/home.html")
    else:
        abort(400)


@app.route("/venues/<venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    error = False
    try:
        db.session.query(Venue).filter(Venue.id == venue_id).delete()
        db.session.commit()
        flash("Venue was successfully deleted!")
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
        flash("An error occurred. Venue could not be deleted.")
    finally:
        db.session.close()
    if not error:
        return render_template("pages/home.html")
    else:
        abort(400)


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)
    form = VenueForm(obj=venue)
    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    error = False
    form = VenueForm(obj=request.form)
    venue = Venue.query.get(venue_id)
    try:
        venue.name = form.name.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.address = form.address.data
        venue.phone = form.phone.data
        venue.image_link = form.image_link.data
        venue.genres = form.genres.data
        venue.facebook_link = form.facebook_link.data
        venue.website = form.website.data
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if not error:
        return redirect(url_for("show_venue", venue_id=venue_id))
    else:
        abort(400)


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    artists = Artist.query.all()
    return render_template("pages/artists.html", artists=artists)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    search = request.form.get("search_term", "")
    artists = Artist.query.filter(Artist.name.ilike("%" + search + "%")).all()
    data = []
    for artist in artists:
        data.append(artist.search)
    response = {"count": len(artists), "data": data}
    return render_template(
        "pages/search_artists.html", results=response, search_term=search
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    data = {}
    artist = Artist.query.get(artist_id)
    artist.genres = "".join(
        list(filter(lambda x: x != "{" and x != "}", artist.genres))
    ).split(",")
    past_shows = (
        Show.query.filter(Show.artist_id == artist_id)
        .filter(Show.start_time < datetime.now())
        .all()
    )
    upcoming_shows = (
        Show.query.filter(Show.artist_id == artist_id)
        .filter(Show.start_time > datetime.now())
        .all()
    )
    past_shows_data = []
    upcoming_shows_data = []
    for past_show in past_shows:
        venue = Venue.query.get(past_show.venue_id)
        past_shows_data.append(
            {
                "venue_id": venue.id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": past_show.start_time.strftime("%m/%d/%Y, %H:%M"),
            }
        )
    for upcoming_show in upcoming_shows:
        venue = Venue.query.get(upcoming_show.venue_id)
        upcoming_shows_data.append(
            {
                "venue_id": venue.id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": past_show.start_time.strftime("%m/%d/%Y, %H:%M"),
            }
        )
    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.city,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows_data,
        "upcoming_shows": upcoming_shows_data,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template("pages/show_artist.html", artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    form = ArtistForm(obj=artist)
    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    error = False
    form = ArtistForm(obj=request.form)
    artist = Artist.query.get(artist_id)
    try:
        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.genres = form.genres.data
        artist.image_link = form.image_link.data
        artist.facebook_link = form.facebook_link.data
        artist.website = form.website.data
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if not error:
        return redirect(url_for("show_artist", artist_id=artist_id))
    else:
        abort(400)


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    error = False
    form = ArtistForm(obj=request.form)
    artist = Artist(
        name=form.name.data,
        city=form.city.data,
        state=form.state.data,
        phone=form.phone.data,
        genres=form.genres.data,
        image_link=form.image_link.data,
        facebook_link=form.facebook_link.data,
        website=form.website.data,
        seeking_venue=form.seeking_venue.data,
        seeking_description=form.seeking_description.data,
    )
    try:
        db.session.add(artist)
        db.session.commit()
        flash(f"Artist {artist.name} was successfully listed!")
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
        flash(f"An error occurred. Artist {artist.name} could not be listed.")
    finally:
        db.session.close()
    if not error:
        return render_template("pages/home.html")
    else:
        abort(400)


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    data = []
    shows = (
        db.session.query(
            Show.venue_id,
            Show.start_time,
            Venue.name.label("venue_name"),
            Artist.id.label("artist_id"),
            Artist.name.label("artist_name"),
            Artist.image_link.label("artist_image_link"),
        )
        .join(Venue)
        .join(Artist)
        .all()
    )
    for show in shows:
        data.extend(
            [
                {
                    "venue_id": show.venue_id,
                    "venue_name": show.venue_name,
                    "artist_id": show.artist_id,
                    "artist_name": show.artist_name,
                    "artist_image_link": show.artist_image_link,
                    "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M"),
                }
            ]
        )
    return render_template("pages/shows.html", shows=data)


@app.route("/shows/create")
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    error = False
    form = ShowForm(obj=request.form)
    show = Show(
        artist_id=form.artist_id.data,
        venue_id=form.venue_id.data,
        start_time=form.start_time.data,
    )
    try:
        db.session.add(show)
        db.session.commit()
        flash("Show was successfully listed!")
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
        flash("An error occurred. Show could not be listed.")
    finally:
        db.session.close()
    if not error:
        return render_template("pages/home.html")
    else:
        abort(400)


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
