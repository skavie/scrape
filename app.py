from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import os


app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#from models import Result
from sqlalchemy.dialects.postgresql import JSON

class Result(db.Model):
    __tablename__ = 'result'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String())
    result_all = db.Column(JSON)
    result_no_stop_words = db.Column(JSON)

    def __init__(self, url, result_all, result_no_stop_words):
        self.url = url
        self.result_all = result_all
        self.result_no_stop_words = result_no_stop_words

    def __repr__(self):
        return '<id {}>'.format(self.id)


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/<name>')
def hello_name(name):
    print(os.environ['APP_SETTINGS'])
    print(os.environ['DATABASE_URL'])
    return "Hello {}!".format(name)


if __name__ == '__main__':
    app.run()
