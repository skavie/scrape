import os
import requests
import operator
import re
import nltk
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import json

from stop_words import stops
from collections import Counter
from bs4 import BeautifulSoup

from rq import Queue
from rq.job import Job
from worker import conn

# initial config
app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

q = Queue(connection=conn)

from models import Result

def count_and_save_words(url):
    errors = []

    # get url that the person has entered
    try:
        r = requests.get(url)
    except:
        errors.append(
            "Unable to get URL. Please make sure it's valid and try again."
        )
        return render_template('index.html', errors=errors)
    if r:
        # text processing
        raw = BeautifulSoup(r.text, 'html.parser').get_text()
        nltk.data.path.append('./nltk_data/')  # set the path
        tokens = nltk.word_tokenize(raw)
        text = nltk.Text(tokens)
        # remove punctuation, count raw words
        nonPunct = re.compile('.*[A-Za-z].*')
        raw_words = [w for w in text if nonPunct.match(w)]
        raw_word_count = Counter(raw_words)
        # stop words
        no_stop_words = [w for w in raw_words if w.lower() not in stops]
        no_stop_words_count = Counter(no_stop_words)
        # save the results
        results = sorted(
            no_stop_words_count.items(),
            key=operator.itemgetter(1),
            reverse=True
        )
        try:
            result = Result(
                url=url,
                result_all=raw_word_count,
                result_no_stop_words=no_stop_words_count
            )
            db.session.add(result)
            db.session.commit()
            return result.id
        except:
            errors.append("Unable to add item to database.")
            return {"error": errors}

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/start', methods=['POST'])
def get_counts():
    # get url
    data = json.loads(request.data.decode())
    url = data["url"]
    if 'http://' not in url[:7]:
        url = 'http://' + url
    # start job
    job = q.enqueue_call(
        func=count_and_save_words, args=(url,), result_ttl=5000
    )
    # return created job id, which is a hash like 24a2bf9d-3b86-44a1-b840-13c4350fb748
    return job.get_id()
    
    
@app.route("/results/<job_key>", methods=['GET'])
def get_results(job_key):

    job = Job.fetch(job_key, connection=conn)
    print job.result
    print job.get_id()
    
    if job.is_finished:
        result = Result.query.filter_by(id=job.result).first()
        results = sorted(
                    result.result_no_stop_words.items(),
                    key=operator.itemgetter(1),
                    reverse=True
                )
                
        # return jsonify(result.result_no_stop_words), 200
        return jsonify(results), 200
    else:
        return "Nay!", 202
    
if __name__ == '__main__':
    app.run()