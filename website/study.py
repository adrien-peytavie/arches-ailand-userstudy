# -*- encoding: utf-8 -*-

import random
import os
import time
import json
from datetime import datetime
from flask import Flask, render_template, redirect, request, jsonify
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__, template_folder="templates") 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///userstudy.db'
app.config['SECRET_KEY'] = 'please, tell nobody, ok???234523523'
db = SQLAlchemy(app)

VIDEOS_URL = 'https://perso.liris.cnrs.fr/eric.guerin/US/'

LANG_DIR = 'language'
DEFAULT_LANGUAGE = 'en'
TEXTS = {}
for file in os.listdir(LANG_DIR):
    if file.endswith('.json'):
        lang = file.split('.')[0]
        with open(os.path.join(LANG_DIR, file), encoding='utf-8') as f:
            TEXTS[lang] = json.load(f)


class UserSession(db.Model):  # participant session identifier
    id  = db.Column(db.Integer, primary_key=True)
    ini = db.Column(db.DateTime, default=datetime.utcnow)
    end = db.Column(db.DateTime, nullable=True)
    lang = db.Column(db.String(12), default='en')
    group = db.Column(db.String(32), default='')
    hikingFreq = db.Column(db.Integer, default=0)
    gamingFreq = db.Column(db.Integer, default=0)
    comments = db.Column(db.Text, default='')

class PairedChoice(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('user_session.id'), nullable=False)
    task       = db.Column(db.Integer)     # task number
    qnumber    = db.Column(db.Integer)     # question number
    choice1    = db.Column(db.String(255)) # first option
    choice2    = db.Column(db.String(255)) # second option
    answer     = db.Column(db.String(255)) # chosen option
    datetime   = db.Column(db.DateTime, default=datetime.utcnow)



''' root 
    Welcome page
'''
@app.route("/")
@app.route("/<string:lang>")
def root(lang=DEFAULT_LANGUAGE):
    db.create_all()
    return render_template('index.html', **TEXTS[lang]["index"], **TEXTS[lang]["headers"],
                            group=request.args.get('g', ''), lang=lang)


''' start page
    Launch the user study
    Generates a random session ID for shuffling
'''
@app.route("/start")
@app.route("/<string:lang>/start")
def start(lang=DEFAULT_LANGUAGE):
    session = UserSession()
    session.ini = datetime.utcnow()
    session.lang = lang
    try:
        session.group = request.args.get('group', '')
    except:
        session.group = ''
    db.session.add(session)
    db.session.commit()
    return redirect(lang + '/initial?s='+str(session.id))


@app.route("/initial", methods=['GET', 'POST'])
@app.route("/<string:lang>/initial", methods=['GET', 'POST'])
def initial(lang=DEFAULT_LANGUAGE):

    session_id = request.args.get('s', '')
    if session_id != '':
        try:
            session = UserSession.query.get(session_id)
        except:
            session = None
    else:
        session = None
        
    if not session:
        return redirect('/' + lang + '/')
    
    if request.form and 'submit' in request.form:
        try:           
            session.hikingFreq = int(request.form['freqHike'])
        except:
            session.hikingFreq = 0
        try:
            session.gamingFreq = int(request.form['freqGame'])
        except:
            session.gamingFreq = 0
            
        try:
            db.session.commit()
            return redirect(lang + '/task1/0?s='+str(session.id))
        except:
            pass
    
    return render_template('demographics.html',
                           **TEXTS[lang]["demographics"], **TEXTS[lang]["headers"])



''' results page
    Shows the summary of all results
'''
@app.route("/results", methods=['GET', 'POST'])
@app.route("/<string:lang>/results", methods=['GET', 'POST'])
def results(lang=DEFAULT_LANGUAGE):
    session_id = request.args.get('s', '')
    monitored = request.args.get('m', False)
    if session_id != '':
        try:
            session = UserSession.query.get(session_id)
            if not session.end:
                session.end = datetime.utcnow()
                db.session.commit()
                
            if request.form and 'submit' in request.form:
                if 'comments' in request.form and request.form['comments'] and len(request.form['comments']) > 0:  
                    session.comments = request.form['comments']
                    db.session.commit()
                
            data = PairedChoice.query.filter_by(session_id=session_id, task=1).all()
        except Exception as e:
            raise e
            data = []
            
    else:
        #data = PairedChoice.query.filter(task=1).all()
        data = []
    if not monitored:
        data = []
        
    return render_template('results.html', **TEXTS[lang]["results"], **TEXTS[lang]["headers"],
                           summary=data)

 


''' Task 1: 2AFC
    Show a pair of images, select the most realistic one
'''

CHOICES = {
    'VD': ['US0', 'US1', 'US2', 'US3', 'US4', 'US5', 'US6', 'US7', 'US8'],
    'B': ['US9', 'US10', 'US11', 'US12', 'US13', 'US14', 'US15', 'US16', 'US17'],
    'V': ['US18', 'US19', 'US20', 'US21', 'US22', 'US23', 'US24', 'US25', 'US26'],
    'D': ['US27', 'US28', 'US29', 'US30', 'US31', 'US32', 'US33', 'US34', 'US35'],
    'VDE': ['US36', 'US37', 'US38', 'US39', 'US40', 'US41', 'US42', 'US44', 'US45']
}

def buildTask1Pairs(rndSeed, controlReps=0):
    
    rng = random.Random(rndSeed)
    
    # shuffle each row (key) independently
    keys = []
    vals = []
    for k,v in CHOICES.items():
        vv = v.copy()
        rng.shuffle(vv)
        vals.append(vv)
        keys.append(k)
    numSets = len(keys)

    # set combinations
    pairCombis = []
    for i in range(numSets):
        for j in range(i+1, numSets):
            pairCombis.append((i, j))
            
    # build pairs
    pairs = []
    emptySet = False
    available = [len(v) for v in vals]
    numFullSets = 0
    while not emptySet:
        # try to build a full set of combinations
        tempPairs = []
        for i,j in pairCombis:
            p1 = available[i] - 1
            p2 = available[j] - 1
            if p1 < 0 or p2 < 0:
                emptySet = True
                break
            available[i] -= 1
            available[j] -= 1
            t1 = vals[i][p1] + '_' + keys[i]
            t2 = vals[j][p2] + '_' + keys[j]
            tempPairs.append((t1, t2)) 
            
        # only append pairs to final list if we got all combinations
        if not emptySet:
            numFullSets += 1
            for p in tempPairs:
                if rng.random() < 0.5:
                    pairs.append((p[0], p[1]))
                else:
                    pairs.append((p[1], p[0]))
                
    rng.shuffle(pairs)
    
    if controlReps > 0:
        nthird = int(len(pairs)/3)
        repSrc = rng.sample(list(range(nthird)), k=controlReps)
        repDst = rng.sample(list(range(len(pairs)-nthird, len(pairs))), k=controlReps)
        
        for i in range(controlReps):
            p1,p2 = pairs[repSrc[i]]
            pairs.insert(repDst[i], (p2,p1))
            
    return pairs


@app.route("/task1/<int:question_id>", methods=['GET', 'POST'])
@app.route("/<string:lang>/task1/<int:question_id>", methods=['GET', 'POST'])
def task1(question_id, lang=DEFAULT_LANGUAGE):

    CONTROL_REPS = 2 # repeated questions just to be sure about participant's answers

    session_id = request.args.get('s', '')
    pairs = buildTask1Pairs(session_id, CONTROL_REPS)
    
    # if we finished all the questions, move to the next task (or end page)
    if question_id == len(pairs):
        return redirect(lang + '/results' + '?s=' + session_id)
            
    option1 = pairs[question_id][0]
    option2 = pairs[question_id][1]
    error = ''
    
    if question_id < len(pairs) - 1:
        prefetch1 = pairs[question_id + 1][0]
        prefetch2 = pairs[question_id + 1][1]
    else:
        prefetch1 = None
        prefetch2 = None
    
    if request.form and 'submit' in request.form:
        if 'choice' in request.form and request.form['choice'] and len(request.form['choice']) > 0:
            try:
                userchoice = PairedChoice()
                userchoice.session_id = session_id
                userchoice.task = 1
                userchoice.qnumber = question_id
                userchoice.choice1 = option1
                userchoice.choice2 = option2
                userchoice.answer  = request.form['choice']
                db.session.add(userchoice)
                db.session.commit()
                
                return redirect(lang + '/task1/' + str(question_id+1) + '?s=' + session_id)
            except Exception as e:
                error = str(e)
        else:
            error = TEXTS[lang]["paired"]["error_no_option"]
        
    return render_template('paired.html', **TEXTS[lang]["paired"], **TEXTS[lang]["headers"],
                            questionIndex='%d/%d'%(question_id+1, len(pairs)), 
                            videosUrl = VIDEOS_URL,
                            option1=option1, option2=option2, 
                            prefetch1=prefetch1, prefetch2=prefetch2,
                            error=error)
    
    
    
if __name__ == "__main__":
    db.create_all()  # make our sqlalchemy tables
    app.run()
    #app.run(host="0.0.0.0", debug=True)
