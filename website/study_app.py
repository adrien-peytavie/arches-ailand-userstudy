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
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'please, tell nobody, ok???234523523'
db = SQLAlchemy(app)


VIDEOS_URL = 'https://perso.liris.cnrs.fr/eric.guerin/VideosUS/'

LANG_DIR = 'mysite/language'
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
    timing     = db.Column(db.Integer)     # time to answer the question after the loading of the video



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
    return redirect('/' + lang + '/initial?s='+str(session.id))


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
            return redirect('/' + lang + '/task1/0?s='+str(session.id))
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

CHOICES_Old = {
    'VD': ['US0', 'US1', 'US2', 'US3', 'US4', 'US5', 'US6', 'US7', 'US8'],
    'B': ['US9', 'US10', 'US11', 'US12', 'US13', 'US14', 'US15', 'US16', 'US17'],
    'V': ['US18', 'US19', 'US20', 'US21', 'US22', 'US23', 'US24', 'US25', 'US26'],
    'D': ['US27', 'US28', 'US29', 'US30', 'US31', 'US32', 'US33', 'US34', 'US35'],
    'VDE': ['US36', 'US37', 'US38', 'US39', 'US40', 'US41', 'US42', 'US44', 'US45']
}


# R : real, G : Generated, C : CGAN2017
CHOICES = {
    'Canyon': {
		'R' : ['CR0', 'CR1', 'CR2', 'CR3', 'CR4', 'CR5', 'CR6', 'CR7', 'CR8', 'CR9'], # Canyon Real
		'G' : ['CG0', 'CG1', 'CG2', 'CG3', 'CG4', 'CG5', 'CG6', 'CG7', 'CG8', 'CG9'], # Canyon Generated
		'C' : ['CC0', 'CC1', 'CC2', 'CC3', 'CC4', 'CC5', 'CC6', 'CC7', 'CC8', 'CC9'], # Canyon CGAN
		},
    'Flat': {
		'R' : ['FR0', 'FR1', 'FR2', 'FR3', 'FR4', 'FR5', 'FR6', 'FR7', 'FR8', 'FR9'], # Flat Real
		'G' : ['FG0', 'FG1', 'FG2', 'FG3', 'FG4', 'FG5', 'FG6', 'FG7', 'FG8', 'FG9'], # Flat Generated
		'C' : ['FC0', 'FC1', 'FC2', 'FC3', 'FC4', 'FC5', 'FC6', 'FC7', 'FC8', 'FC9'], # Flat CGAN
		},
    'Hilly': {
		'R' : ['HR0', 'HR1', 'HR2', 'HR3', 'HR4', 'HR5', 'HR6', 'HR7', 'HR8', 'HR9'], # Hilly Real
		'G' : ['HG0', 'HG1', 'HG2', 'HG3', 'HG4', 'HG5', 'HG6', 'HG7', 'HG8', 'HG9'], # Hilly Generated
		'C' : ['HC0', 'HC1', 'HC2', 'HC3', 'HC4', 'HC5', 'HC6', 'HC7', 'HC8', 'HC9'], # Hilly CGAN
		},
    'Mountaineous': {
		'R' : ['MR0', 'MR1', 'MR2', 'MR3', 'MR4', 'MR5', 'MR6', 'MR7', 'MR8', 'MR9'], # Moutain Real
		'G' : ['MG0', 'MG1', 'MG2', 'MG3', 'MG4', 'MG5', 'MG6', 'MG7', 'MG8', 'MG9'], # Moutain Generated
		'C' : ['MC0', 'MC1', 'MC2', 'MC3', 'MC4', 'MC5', 'MC6', 'MC7', 'MC8', 'MC9'], # Moutain CGAN
		},
}

#CHOICES = {
#    'Canyon': {
#		'R' : ['US0_VD', 'US0_VD', 'US0_VD', 'US0_VD', 'US0_VD', 'US0_VD', 'US0_VD', 'US0_VD', 'US0_VD', 'US0_VD', 'US0_VD', 'US0_VD'], # Canyon Real
#		'G' : ['US1_VD', 'US1_VD', 'US1_VD', 'US1_VD', 'US1_VD', 'US1_VD', 'US1_VD', 'US1_VD', 'US1_VD', 'US1_VD', 'US1_VD', 'US1_VD'], # Canyon Generated
#		},
#    'Flat': {
#		'R' : ['US2_VD', 'US2_VD', 'US2_VD', 'US2_VD', 'US2_VD', 'US2_VD', 'US2_VD', 'US2_VD', 'US2_VD', 'US2_VD', 'US2_VD', 'US2_VD'], # Flat Real
#		'G' : ['US3_VD', 'US3_VD', 'US3_VD', 'US3_VD', 'US3_VD', 'US3_VD', 'US3_VD', 'US3_VD', 'US3_VD', 'US3_VD', 'US3_VD', 'US3_VD'], # Flat Generated
#		},
#    'Hilly': {
#		'R' : ['US4_VD', 'US4_VD', 'US4_VD', 'US4_VD', 'US4_VD', 'US4_VD', 'US4_VD', 'US4_VD', 'US4_VD', 'US4_VD', 'US4_VD', 'US4_VD'], # Hilly Real
#		'G' : ['US5_VD', 'US5_VD', 'US5_VD', 'US5_VD', 'US5_VD', 'US5_VD', 'US5_VD', 'US5_VD', 'US5_VD', 'US5_VD', 'US5_VD', 'US5_VD'], # Hilly Generated
#		},
#    'Mountaineous': {
#		'R' : ['US6_VD', 'US6_VD', 'US6_VD', 'US6_VD', 'US6_VD', 'US6_VD', 'US6_VD', 'US6_VD', 'US6_VD', 'US6_VD', 'US6_VD', 'US6_VD'], # Moutain Real
#		'G' : ['US7_VD', 'US7_VD', 'US7_VD', 'US7_VD', 'US7_VD', 'US7_VD', 'US7_VD', 'US7_VD', 'US7_VD', 'US7_VD', 'US7_VD', 'US7_VD'], # Moutain Generated
#		},
#}

def getRandomPair(rng, realTab, generatedTab, number=6):
	# Init
	rrTab = realTab.copy()
	ggTab = generatedTab.copy()

	# Shuffle the order inside table
	rng.shuffle(rrTab)
	rng.shuffle(ggTab)

	# Define pairs
	pairsC = []
	numPair = min(number, min(len(rrTab), len(ggTab)))
	for i in range(numPair):
		# Shuffle the pair
		pair = [rrTab[i],ggTab[i]]
		rng.shuffle(pair)

		pairsC.append((pair[0],pair[1]))

	return pairsC


def getRandomPair2(rng, TabReal, TabGenerated, TabCGan, number=6):
	# Init
	rrTab = TabReal.copy()
	ggTab = TabGenerated.copy()
	ccTab = TabCGan.copy()

	# Shuffle the order inside table
	rng.shuffle(rrTab)
	rng.shuffle(ggTab)
	rng.shuffle(ccTab)

	# Define pairs
	pairsC = []
	numPair = min(int(number/3), min(len(rrTab), len(ggTab)))
	for i in range(numPair):
		# Shuffle the pair
		pairA = [rrTab[3*i+0],ggTab[3*i+0]]
		pairB = [ggTab[3*i+1],ccTab[3*i+1]]
		pairC = [rrTab[3*i+2],ccTab[3*i+2]]

		rng.shuffle(pairA)
		rng.shuffle(pairB)
		rng.shuffle(pairC)

		pairsC.append((pairA[0],pairA[1]))
		pairsC.append((pairB[0],pairB[1]))
		pairsC.append((pairC[0],pairC[1]))

	return pairsC

def buildTask1Pairs(rndSeed, numberByCat=6, shuffleCategory=False, controlReps=0):

    rng = random.Random(rndSeed)

    pairsC = []
    for k,v in CHOICES.items():
        currentPairs = getRandomPair2(rng, v.get("R"), v.get("G"), v.get("C"), numberByCat)
        pairsC.extend(currentPairs)

    if shuffleCategory :
        rng.shuffle(pairsC)

    if controlReps > 0:
        nthird = int(len(pairsC)/3)
        repSrc = rng.sample(list(range(nthird)), k=controlReps)
        repDst = rng.sample(list(range(len(pairsC)-nthird, len(pairsC))), k=controlReps)

        for i in range(controlReps):
            p1,p2 = pairsC[repSrc[i]]
            pairsC.insert(repDst[i], (p2,p1))

    return pairsC


@app.route("/task1/<int:question_id>", methods=['GET', 'POST'])
@app.route("/<string:lang>/task1/<int:question_id>", methods=['GET', 'POST'])
def task1(question_id, lang=DEFAULT_LANGUAGE):

    global pairs

    CONTROL_REPS = 2 # repeated questions just to be sure about participant's answers
    NUMBER_BY_CATEGORY = 6
    SHUFFLE_CATEGORY = True

    session_id = request.args.get('s', '')
    pairs = buildTask1Pairs(session_id, NUMBER_BY_CATEGORY, SHUFFLE_CATEGORY, CONTROL_REPS)

    # if we finished all the questions, move to the next task (or end page)
    if question_id == len(pairs):
        return redirect('/' + lang + '/results' + '?s=' + session_id)

    option1 = pairs[question_id][0]
    option2 = pairs[question_id][1]
    error = ''
    #error = str(pairs) # Debug pairs

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
                userchoice.timing  = request.form['timing']
                db.session.add(userchoice)
                db.session.commit()

                return redirect('/' + lang + '/task1/' + str(question_id+1) + '?s=' + session_id)
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
    app.run(port=8080)
    #app.run(host="0.0.0.0", port=8080, debug=True)
