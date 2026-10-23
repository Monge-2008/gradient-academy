from flask import Flask, render_template, request, jsonify, send_file, session
import sqlite3, os, json, re, urllib.request, urllib.error, secrets, hashlib
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv('GRADIENT_DB_PATH', BASE / 'gradient_academy.db'))
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-this-secret-before-deploying-' + secrets.token_hex(8))

MODULES = [
 {"id":1,"title":"Fondations mathématiques","subtitle":"Fonctions, variables et variations","description":"Comprendre ce qu'une fonction fait avant d'étudier comment elle varie.","skills":["Évaluer une fonction","Calculer une variation","Interpréter un taux de variation"],"lessons":[{"title":"Une fonction associe une entrée à une sortie","body":"Une fonction f prend une entrée x et renvoie une valeur f(x). Pour f(x)=x², l'entrée 3 donne f(3)=3²=9.","example":"f(4)=4²=16","question":"Pour f(x)=x², calcule f(5). Explique brièvement ton calcul.","answer":"25","hint":"Remplace x par 5, puis calcule 5 au carré.","concept":"substitution"},{"title":"Variation d'une fonction","body":"La variation Δf entre deux entrées est la valeur finale moins la valeur initiale : Δf=f(x₂)-f(x₁).","example":"Pour f(x)=x² entre 3 et 4 : Δf=16-9=7.","question":"Pour f(x)=x², quelle est la variation de f lorsque x passe de 2 à 3 ? Donne le calcul.","answer":"5","hint":"Calcule f(3)=9 et f(2)=4, puis fais 9−4.","concept":"variation"},{"title":"Taux de variation","body":"Le taux de variation moyen est Δf/Δx. Il mesure la variation moyenne de la sortie par unité de variation de l'entrée sur un intervalle.","example":"De x=3 à x=3,1 pour x² : Δf=0,61, Δx=0,1, donc le taux vaut 6,1.","question":"Pour f(x)=x² entre x=1 et x=2, calcule le taux de variation moyen.","answer":"3","hint":"f(2)=4, f(1)=1, Δx=1. Le taux est (4−1)/(2−1).","concept":"taux"}]},
 {"id":2,"title":"Comprendre la dérivée","subtitle":"Pente locale et règles de dérivation","description":"Passer du taux moyen à la variation instantanée.","skills":["Interpréter une dérivée","Dériver des fonctions simples","Relier pente et variation"],"lessons":[{"title":"La dérivée mesure une variation locale","body":"La dérivée f′(a) est la limite du taux de variation lorsque le second point se rapproche de a, si cette limite existe. Géométriquement, c'est la pente de la tangente au graphe en ce point.","example":"Pour f(x)=x², f′(x)=2x, donc f′(3)=6.","question":"Si f(x)=x² et f′(x)=2x, quelle est la dérivée en x=4 ? Explique le remplacement.","answer":"8","hint":"Remplace x par 4 dans 2x.","concept":"derivee"},{"title":"Règle de puissance","body":"Pour f(x)=xⁿ, la dérivée est f′(x)=n·xⁿ⁻¹. Par exemple, la dérivée de x³ est 3x².","example":"d(x⁴)/dx=4x³.","question":"Quelle est la dérivée de f(x)=x³ ? Écris l'expression complète.","answer":"3x^2","hint":"Multiplie par l'exposant 3 puis diminue l'exposant de 1.","concept":"regle_puissance"}]},
 {"id":3,"title":"Découvrir le gradient","subtitle":"Dérivées partielles et vecteurs","description":"Construire et interpréter le gradient d'une fonction à plusieurs variables.","skills":["Calculer des dérivées partielles","Construire un gradient","Interpréter ses composantes"],"lessons":[{"title":"Dérivées partielles","body":"Pour une fonction de plusieurs variables, une dérivée partielle mesure la variation selon une variable en gardant les autres constantes.","example":"Si f(x,y)=x²+y², alors ∂f/∂x=2x et ∂f/∂y=2y.","question":"Pour f(x,y)=x²+y², quelle est la dérivée partielle par rapport à x ?","answer":"2x","hint":"Traite y² comme une constante et dérive x².","concept":"partielle"},{"title":"Construire le gradient","body":"Le gradient rassemble les dérivées partielles dans un vecteur : ∇f=(∂f/∂x, ∂f/∂y). Il pointe vers la direction de plus forte augmentation locale pour une fonction différentiable, dans la géométrie euclidienne usuelle.","example":"Pour f=x²+y², ∇f=(2x,2y). En (1,2), le gradient vaut (2,4).","question":"Pour f(x,y)=x²+y², calcule le gradient au point (3,1). Donne ses deux composantes.","answer":"6,2","hint":"Le gradient est (2x,2y). Remplace x par 3 et y par 1.","concept":"gradient"}]},
 {"id":4,"title":"Géométrie du gradient","subtitle":"Courbes de niveau et points critiques","description":"Comprendre la géométrie et les limites de l'intuition du gradient.","skills":["Lire les courbes de niveau","Identifier les points critiques","Distinguer minimum et point selle"],"lessons":[{"title":"Courbes de niveau","body":"Une courbe de niveau rassemble les points où f garde la même valeur. Quand le gradient est non nul et les conditions régulières sont réunies, il est perpendiculaire à la courbe de niveau.","example":"Pour f=x²+y², les courbes de niveau sont des cercles centrés à l'origine.","question":"Pour f(x,y)=x²+y², quelle est la valeur de f au point (3,4) ?","answer":"25","hint":"Calcule 3²+4².","concept":"niveau"},{"title":"Points critiques","body":"Un point critique est typiquement un point où le gradient est nul, ou où la dérivabilité échoue. Un gradient nul ne garantit pas un minimum : il peut aussi s'agir d'un maximum ou d'un point selle.","example":"f(x,y)=x²−y² possède un point selle à (0,0).","question":"Le gradient nul garantit-il toujours un minimum global ? Réponds et justifie en une phrase.","answer":"non","hint":"Pense aux points selles et aux maxima.","concept":"point_critique"}]},
 {"id":5,"title":"Descente de gradient","subtitle":"Minimiser une fonction de perte","description":"Mettre à jour des paramètres pour réduire une fonction objectif.","skills":["Expliquer la mise à jour","Calculer une itération","Choisir un taux d'apprentissage"],"lessons":[{"title":"Pourquoi soustraire le gradient ?","body":"La mise à jour θ suivant = θ − η∇L(θ) utilise le sens opposé au gradient pour chercher une diminution locale de la perte. Cela ne garantit pas que chaque étape baisse la perte si le taux est inadapté.","example":"Si θ=3, ∇L(θ)=4 et η=0,1, alors θ suivant=3−0,4=2,6.","question":"Avec θ=5, gradient=2 et taux d'apprentissage η=0,1, quel est le nouveau paramètre ?","answer":"4.8","hint":"Calcule 5−0,1×2.","concept":"mise_a_jour"},{"title":"Taux d'apprentissage","body":"Le taux η détermine la taille du pas. Trop faible : apprentissage lent. Trop élevé : dépassements, oscillations ou divergence possibles.","example":"Une grande pente multipliée par un taux élevé produit un grand déplacement.","question":"Quel risque peut causer un taux d'apprentissage trop élevé ? Cite un risque précis.","answer":"divergence","hint":"La perte peut augmenter sans contrôle au lieu de se stabiliser.","concept":"learning_rate"}]},
 {"id":6,"title":"Gradient et machine learning","subtitle":"Modèles et fonctions de perte","description":"Relier les calculs de gradient à l'apprentissage supervisé.","skills":["Définir une fonction de perte","Comprendre les paramètres","Expliquer la régression"],"lessons":[{"title":"Fonction de perte","body":"Une fonction de perte quantifie l'écart entre les prédictions d'un modèle et les cibles. L'entraînement cherche souvent des paramètres qui minimisent cette perte sur les données d'entraînement.","example":"En régression linéaire, une perte courante est l'erreur quadratique moyenne.","question":"À quoi sert une fonction de perte pendant l'entraînement d'un modèle ? Réponds avec tes mots.","answer":"mesurer l erreur","hint":"Elle quantifie à quel point les prédictions diffèrent des cibles.","concept":"perte"}]},
 {"id":7,"title":"Réseaux de neurones et backpropagation","subtitle":"Calcul efficace des gradients","description":"Distinguer gradient, descente de gradient et rétropropagation.","skills":["Expliquer la rétropropagation","Distinguer trois notions","Comprendre la règle de chaîne"],"lessons":[{"title":"Trois notions différentes","body":"Le gradient est une collection de dérivées. La descente de gradient est une règle d'optimisation qui met à jour les paramètres. La rétropropagation applique efficacement la règle de chaîne pour calculer les gradients dans un réseau.","example":"Backpropagation calcule les gradients ; l'optimiseur les utilise pour modifier les poids.","question":"Quelle est la différence entre rétropropagation et descente de gradient ?","answer":"calculer les gradients","hint":"La rétropropagation calcule les gradients ; la descente de gradient utilise ces gradients pour mettre à jour les paramètres.","concept":"backprop"}]},
 {"id":8,"title":"Optimiseurs avancés","subtitle":"SGD, Momentum, RMSProp et Adam","description":"Comprendre les variantes utilisées pour entraîner les modèles modernes.","skills":["Comparer les optimiseurs","Comprendre les mini-lots","Décrire Adam"],"lessons":[{"title":"SGD et mini-lots","body":"La descente par lots utilise toutes les données disponibles pour calculer le gradient. SGD utilise souvent un exemple à la fois, et les mini-lots un petit sous-ensemble, ce qui équilibre coût et bruit du gradient.","example":"Un mini-lot de 32 exemples calcule une estimation du gradient sur 32 exemples.","question":"Quel est l'avantage pratique fréquent des mini-lots par rapport à un lot complet ?","answer":"mémoire","hint":"Ils réduisent le volume de données traité en une seule mise à jour.","concept":"sgd"},{"title":"Adam","body":"Adam combine une moyenne mobile des gradients et une moyenne mobile de leurs carrés pour adapter les tailles de pas par paramètre. Il est pratique mais n'assure pas une solution globalement optimale.","example":"Adam est couramment disponible dans les bibliothèques de deep learning.","question":"Adam adapte-t-il les pas à partir d'informations sur les gradients ? Réponds oui ou non et explique brièvement.","answer":"oui","hint":"Adam maintient des estimations des moyennes et des carrés des gradients.","concept":"adam"}]},
 {"id":9,"title":"Python et calcul automatique","subtitle":"NumPy, visualisation et PyTorch","description":"Vérifier les calculs mathématiques avec du code.","skills":["Calculer avec NumPy","Programmer une mise à jour","Comprendre autograd"],"lessons":[{"title":"Calculer un gradient en NumPy","body":"Pour f(x,y)=x²+y², le gradient vaut (2x,2y). NumPy permet de représenter les composantes et d'effectuer les calculs numériques.","example":"import numpy as np; x,y=3,1; grad=np.array([2*x,2*y])","question":"Pour x=2 et y=5, quelles sont les composantes du gradient de x²+y² ?","answer":"4,10","hint":"Applique (2x,2y).","concept":"numpy"},{"title":"Autograd","body":"Les bibliothèques comme PyTorch construisent un graphe de calcul et calculent les dérivées nécessaires automatiquement lorsque l'on demande backward().","example":"loss.backward() calcule les gradients des tenseurs suivis.","question":"Dans PyTorch, à quoi sert généralement loss.backward() ?","answer":"calculer les gradients","hint":"Cette instruction propage les dérivées dans le graphe de calcul.","concept":"autograd"}]},
 {"id":10,"title":"Oral universitaire et synthèse","subtitle":"Expliquer, calculer et défendre son raisonnement","description":"Vérifier la maîtrise conceptuelle, numérique et appliquée.","skills":["Définir le gradient rigoureusement","Justifier la descente de gradient","Expliquer les limites"],"lessons":[{"title":"Définition rigoureuse","body":"Pour une fonction différentiable f de plusieurs variables, le gradient est le vecteur des dérivées partielles dans les coordonnées usuelles. Il représente la direction de plus forte augmentation locale au sens euclidien.","example":"Pour f(x,y)=x²+y², ∇f=(2x,2y).","question":"Définis le gradient et explique son rôle dans l'apprentissage d'un réseau de neurones, avec tes propres mots.","answer":"gradient","hint":"Mentionne les dérivées partielles, le vecteur et le calcul des mises à jour des paramètres.","concept":"oral"}]}
]

def connect():
    con=sqlite3.connect(DB_PATH); con.row_factory=sqlite3.Row
    con.execute('''CREATE TABLE IF NOT EXISTS learners(id INTEGER PRIMARY KEY, learner_key TEXT UNIQUE, name TEXT DEFAULT 'Étudiant', created_at TEXT, updated_at TEXT)''')
    con.execute('''CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY, learner_key TEXT, module_id INTEGER, lesson_index INTEGER, question TEXT, answer TEXT, feedback TEXT, score REAL, correct INTEGER, concept TEXT, created_at TEXT)''')
    con.execute('''CREATE TABLE IF NOT EXISTS mastery(learner_key TEXT, concept TEXT, attempts INTEGER DEFAULT 0, score_sum REAL DEFAULT 0, last_score REAL DEFAULT 0, updated_at TEXT, PRIMARY KEY(learner_key,concept))''')
    con.execute('''CREATE TABLE IF NOT EXISTS completions(learner_key TEXT, module_id INTEGER, completed_at TEXT, PRIMARY KEY(learner_key,module_id))''')
    con.commit(); return con

def learner_key():
    if 'learner_key' not in session: session['learner_key']=secrets.token_urlsafe(18)
    key=session['learner_key']; con=connect(); now=datetime.now(timezone.utc).isoformat()
    con.execute('INSERT OR IGNORE INTO learners(learner_key,created_at,updated_at) VALUES(?,?,?)',(key,now,now)); con.commit(); con.close(); return key

def normalize(s):
    s=(s or '').lower().strip().replace('²','^2').replace('−','-').replace('×','*').replace('é','e').replace('è','e').replace('ê','e').replace('à','a').replace('ù','u').replace('ç','c')
    return re.sub(r'\s+',' ',s)

def evaluate_rule(lesson, answer):
    a=normalize(answer); concept=lesson['concept']; expected=lesson['answer']; ok=False
    numeric = re.findall(r'-?\d+(?:[.,]\d+)?', a)
    if concept in ('substitution','variation','taux','derivee','mise_a_jour','niveau','numpy'):
        target=float(expected.replace(',','.')) if re.fullmatch(r'-?\d+(?:\.\d+)?',expected) else None
        vals=[float(v.replace(',','.')) for v in numeric]
        ok=target is not None and any(abs(v-target)<1e-8 for v in vals)
    elif concept=='gradient':
        # In French, (6, 2) commonly denotes vector components; don't parse that comma as a decimal separator.
        vector_match = re.search(r'6\s*[,;]\s*2', a) or re.search(r'6\s+(?:et|and)\s+2', a) or re.search(r'\(\s*6\s*[,;]\s*2\s*\)', a)
        vals=[float(v.replace(',','.')) for v in numeric]
        ok=bool(vector_match) or (len(vals)>=2 and abs(vals[-2]-6)<1e-8 and abs(vals[-1]-2)<1e-8)
    elif concept=='regle_puissance': ok=('3x^2' in a or '3x2' in a or ('3' in a and 'x' in a and '2' in a))
    elif concept=='partielle': ok=('2x' in a or '2*x' in a)
    elif concept=='point_critique': ok=a.startswith('non') or 'pas toujours' in a or 'point selle' in a or 'point selle' in a
    elif concept=='learning_rate': ok=any(w in a for w in ['diverg','oscill','depasse','augmente','instable'])
    elif concept=='perte': ok=any(w in a for w in ['mesur','ecart','erreur','difference','predictions'])
    elif concept=='backprop': ok=('calcul' in a and ('gradient' in a or 'derive' in a)) or ('mise a jour' in a and 'gradient' in a)
    elif concept=='sgd': ok=any(w in a for w in ['memoire','mémoire','moins','petit','rapide','cout','coût'])
    elif concept=='adam': ok=a.startswith('oui') or ('gradient' in a and any(w in a for w in ['moyenne','adapt','pas']))
    elif concept=='autograd': ok='gradient' in a and any(w in a for w in ['calcul','derive','backward'])
    elif concept=='oral': ok=len(a)>45 and 'gradient' in a and any(w in a for w in ['derive','vecteur','param','partielle'])
    else: ok=normalize(expected) in a
    return ok

def ai_feedback(question, answer, lesson, correct):
    key=os.getenv('OPENAI_API_KEY','').strip()
    if not key:
        if correct:
            return {'feedback':"Bonne réponse. Tu as identifié l'idée attendue. Pour consolider ta maîtrise, essaie aussi d'expliquer pourquoi la méthode fonctionne, pas seulement le résultat.",'score':8.0,'source':'règles pédagogiques locales'}
        return {'feedback':f"Pas encore tout à fait. {lesson['hint']}\n\nRéessaie en montrant les étapes de ton raisonnement.",'score':3.0,'source':'règles pédagogiques locales'}
    endpoint=os.getenv('OPENAI_BASE_URL','https://api.openai.com/v1').rstrip('/')+'/chat/completions'
    model=os.getenv('OPENAI_MODEL','gpt-4o-mini')
    prompt=f'''Tu es un tuteur de mathématiques exigeant et encourageant pour un étudiant. Évalue la réponse à cette question de gradient/IA. Question: {question}\nRéponse de l'étudiant: {answer}\nContexte du cours: {lesson['body']}\nRéponse/indice attendu: {lesson['answer']} / {lesson['hint']}\nÉvaluation automatique indicative: {'correcte' if correct else 'à revoir'}.\nRetourne uniquement un JSON valide avec les clés score (nombre 0-10), correct (booléen), feedback (français, expliquer précisément ce qui est juste/faux, ne pas juste donner une note), next_question (question de suivi courte pour vérifier la compréhension), misconception (courte chaîne vide si aucune). Si la réponse est partiellement correcte, reconnais-le. Ne surestime pas la maîtrise.'''
    payload=json.dumps({'model':model,'temperature':0.2,'messages':[{'role':'system','content':'Tu es un professeur particulier rigoureux. Réponds en JSON valide uniquement.'},{'role':'user','content':prompt}]}).encode()
    req=urllib.request.Request(endpoint,data=payload,headers={'Content-Type':'application/json','Authorization':'Bearer '+key},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=35) as resp: data=json.loads(resp.read().decode())
        content=data['choices'][0]['message']['content']; content=re.sub(r'^```(?:json)?\s*|\s*```$','',content.strip())
        parsed=json.loads(content); parsed['score']=max(0,min(10,float(parsed.get('score',5)))); parsed['source']='IA configurée'; return parsed
    except Exception as e:
        return {'feedback':f"Le service IA n'a pas pu répondre ({type(e).__name__}). L'évaluation locale reste disponible : {lesson['hint']}",'score':8.0 if correct else 3.0,'source':'règles locales (secours)'}

@app.get('/')
def index():
    key=learner_key(); con=connect(); learner=con.execute('SELECT * FROM learners WHERE learner_key=?',(key,)).fetchone()
    attempts=con.execute('SELECT COUNT(*) n, AVG(score) avg FROM attempts WHERE learner_key=?',(key,)).fetchone()
    completed={r['module_id'] for r in con.execute('SELECT module_id FROM completions WHERE learner_key=?',(key,)).fetchall()}
    mastery={r['concept']:{'attempts':r['attempts'],'average':round(r['score_sum']/r['attempts'],1) if r['attempts'] else 0,'last':r['last_score']} for r in con.execute('SELECT * FROM mastery WHERE learner_key=?',(key,)).fetchall()}
    con.close(); return render_template('index.html',modules=MODULES,learner=learner,completed=sorted(completed),attempt_count=attempts['n'],average=round(attempts['avg'] or 0,1),mastery=mastery)

@app.post('/api/name')
def save_name():
    key=learner_key(); name=(request.json or {}).get('name','').strip()[:80] or 'Étudiant'; con=connect(); con.execute('UPDATE learners SET name=?,updated_at=? WHERE learner_key=?',(name,datetime.now(timezone.utc).isoformat(),key)); con.commit(); con.close(); return jsonify(ok=True,name=name)

@app.post('/api/answer')
def answer():
    key=learner_key(); data=request.get_json(force=True); mid=int(data.get('module_id',1)); li=int(data.get('lesson_index',0)); ans=str(data.get('answer','')).strip()
    if not ans: return jsonify(error='Écris une réponse avant de valider.'),400
    module=next((m for m in MODULES if m['id']==mid),None)
    if not module or li<0 or li>=len(module['lessons']): return jsonify(error='Exercice introuvable.'),404
    lesson=module['lessons'][li]; correct=evaluate_rule(lesson,ans); result=ai_feedback(lesson['question'],ans,lesson,correct); score=float(result.get('score',8 if correct else 3)); judged=bool(result.get('correct',correct))
    feedback=str(result.get('feedback',''))[:5000]; now=datetime.now(timezone.utc).isoformat(); con=connect()
    con.execute('INSERT INTO attempts(learner_key,module_id,lesson_index,question,answer,feedback,score,correct,concept,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)',(key,mid,li,lesson['question'],ans,feedback,score,int(judged),lesson['concept'],now))
    old=con.execute('SELECT * FROM mastery WHERE learner_key=? AND concept=?',(key,lesson['concept'])).fetchone()
    if old: con.execute('UPDATE mastery SET attempts=attempts+1,score_sum=score_sum+?,last_score=?,updated_at=? WHERE learner_key=? AND concept=?',(score,score,now,key,lesson['concept']))
    else: con.execute('INSERT INTO mastery(learner_key,concept,attempts,score_sum,last_score,updated_at) VALUES(?,?,1,?,?,?)',(key,lesson['concept'],score,score,now))
    con.execute('UPDATE learners SET updated_at=? WHERE learner_key=?',(now,key)); con.commit(); con.close()
    return jsonify(ok=True,correct=judged,score=score,feedback=feedback,next_question=result.get('next_question','Explique pourquoi cette méthode fonctionne.'),misconception=result.get('misconception',''),source=result.get('source','règles locales'),hint=lesson['hint'])

@app.post('/api/complete-module')
def complete_module():
    key=learner_key(); mid=int((request.json or {}).get('module_id',0)); module=next((m for m in MODULES if m['id']==mid),None)
    if not module: return jsonify(error='Module introuvable'),404
    con=connect(); rows=con.execute('SELECT score FROM attempts WHERE learner_key=? AND module_id=?',(key,mid)).fetchall()
    # Validate using the latest score for each lesson, not the average of all historical attempts.
    # Earlier mistakes remain in the report but do not permanently penalize a learner who has improved.
    by_lesson=con.execute("""
        SELECT a.lesson_index, a.score
        FROM attempts AS a
        JOIN (
            SELECT lesson_index, MAX(id) AS latest_id
            FROM attempts
            WHERE learner_key=? AND module_id=?
            GROUP BY lesson_index
        ) AS latest ON a.id=latest.latest_id
        WHERE a.learner_key=? AND a.module_id=?
    """,(key,mid,key,mid)).fetchall()
    latest_scores={int(r['lesson_index']):float(r['score']) for r in by_lesson}
    failed_lessons=[i for i in range(len(module['lessons'])) if latest_scores.get(i,0)<7]
    enough=not failed_lessons
    if enough: con.execute('INSERT OR IGNORE INTO completions(learner_key,module_id,completed_at) VALUES(?,?,?)',(key,mid,datetime.now(timezone.utc).isoformat())); con.commit()
    con.close(); return jsonify(ok=enough, failed_lessons=failed_lessons, message='Module validé.' if enough else 'Il reste des exercices à consolider. Tu vas revenir directement au premier exercice à reprendre.')

@app.get('/api/report')
def report():
    key=learner_key(); con=connect(); learner=con.execute('SELECT * FROM learners WHERE learner_key=?',(key,)).fetchone(); attempts=con.execute('SELECT * FROM attempts WHERE learner_key=? ORDER BY created_at',(key,)).fetchall(); master=con.execute('SELECT * FROM mastery WHERE learner_key=?',(key,)).fetchall(); completed=con.execute('SELECT module_id,completed_at FROM completions WHERE learner_key=?',(key,)).fetchall(); con.close()
    total=len(attempts); avg=round(sum(a['score'] for a in attempts)/total,2) if total else 0
    concepts=[]
    for r in master:
        av=round(r['score_sum']/r['attempts'],2) if r['attempts'] else 0
        level='À travailler' if av<5 else ('En progression' if av<7 else ('Maîtrisé' if av<8.5 else 'Très bien maîtrisé'))
        concepts.append({'concept':r['concept'],'attempts':r['attempts'],'average':av,'last_score':r['last_score'],'level':level})
    data={'title':'Rapport de progression — Gradient Academy','learner':learner['name'] if learner else 'Étudiant','generated_at':datetime.now().astimezone().isoformat(timespec='seconds'),'summary':{'attempts':total,'average_score':avg,'modules_completed':len(completed),'modules_total':len(MODULES),'completion_percent':round(100*len(completed)/len(MODULES))},'mastery':concepts,'modules':[{'id':m['id'],'title':m['title'],'completed':any(c['module_id']==m['id'] for c in completed),'lessons':len(m['lessons'])} for m in MODULES],'attempt_history':[{'module_id':a['module_id'],'module_title':next(m['title'] for m in MODULES if m['id']==a['module_id']),'question':a['question'],'answer':a['answer'],'feedback':a['feedback'],'score':a['score'],'correct':bool(a['correct']),'concept':a['concept'],'created_at':a['created_at']} for a in attempts], 'interpretation':'Ce rapport synthétise les tentatives enregistrées dans cette installation. Les scores automatisés et les commentaires de l’IA sont des indicateurs pédagogiques, pas une certification universitaire indépendante.'}
    return jsonify(data)

@app.post('/api/report/analysis')
def report_analysis():
    key=learner_key(); con=connect(); learner=con.execute('SELECT name FROM learners WHERE learner_key=?',(key,)).fetchone()
    attempts=con.execute('SELECT module_id,question,answer,feedback,score,correct,concept FROM attempts WHERE learner_key=? ORDER BY created_at',(key,)).fetchall()
    mastery=con.execute('SELECT * FROM mastery WHERE learner_key=?',(key,)).fetchall()
    completed=con.execute('SELECT module_id FROM completions WHERE learner_key=?',(key,)).fetchall(); con.close()
    scores=[float(a['score']) for a in attempts]; avg=round(sum(scores)/len(scores),2) if scores else 0
    skills=[{'concept':r['concept'],'attempts':r['attempts'],'average':round(r['score_sum']/r['attempts'],1) if r['attempts'] else 0,'last':r['last_score']} for r in mastery]
    evidence=[{'module':next(m['title'] for m in MODULES if m['id']==a['module_id']),'concept':a['concept'],'answer':a['answer'][:500],'score':a['score'],'correct':bool(a['correct']),'feedback':a['feedback'][:500]} for a in attempts[-80:]]
    api_key=os.getenv('OPENAI_API_KEY','').strip()
    if not api_key:
        strengths=[s['concept'] for s in skills if s['average']>=7]
        weaknesses=[s['concept'] for s in skills if s['average']<7]
        narrative={'source':'synthèse locale (aucune API IA configurée)','overall_assessment':f"{learner['name']} a enregistré {len(attempts)} tentative(s), avec une moyenne de {avg}/10 et {len(completed)}/{len(MODULES)} modules validés. Ce bilan est descriptif ; il ne suffit pas à prouver à lui seul une maîtrise indépendante.",'strengths':strengths or ['Pas encore assez de données pour identifier une force stable.'],'priorities':weaknesses or ['Continuer à tester les acquis avec des questions variées.'],'recommended_plan':['Reprendre les notions dont la moyenne est inférieure à 7/10.','Refaire les calculs à la main sans regarder les exemples.','Expliquer oralement la différence entre gradient, descente de gradient et rétropropagation.'],'oral_questions':['Définis le gradient et interprète ses composantes.','Pourquoi la descente de gradient soustrait-elle le gradient ?','Pourquoi un gradient nul ne garantit-il pas un minimum global ?'],'caveat':'Cette synthèse est produite par des règles locales, pas par un modèle IA externe. Configure OPENAI_API_KEY pour une analyse sémantique générée par IA.'}
        return jsonify(narrative)
    endpoint=os.getenv('OPENAI_BASE_URL','https://api.openai.com/v1').rstrip('/')+'/chat/completions'; model=os.getenv('OPENAI_MODEL','gpt-4o-mini')
    prompt={'learner':learner['name'],'summary':{'attempts':len(attempts),'average_score':avg,'modules_completed':len(completed),'modules_total':len(MODULES)},'skills':skills,'evidence':evidence}
    instruction='Analyse ce dossier pédagogique en français. Utilise uniquement les preuves fournies, ne prétends pas certifier une maîtrise que les données ne démontrent pas. Repère les forces, lacunes, erreurs récurrentes, et donne un plan de révision concret et 3 questions d’oral adaptées. Retourne JSON valide avec les clés overall_assessment (string), strengths (array de strings), priorities (array), recommended_plan (array de strings), oral_questions (array de strings), caveat (string). Distingue clairement preuve d’exercice réussi et compréhension transférable.'
    payload=json.dumps({'model':model,'temperature':0.2,'messages':[{'role':'system','content':instruction},{'role':'user','content':json.dumps(prompt,ensure_ascii=False)}]}).encode()
    req=urllib.request.Request(endpoint,data=payload,headers={'Content-Type':'application/json','Authorization':'Bearer '+api_key},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=45) as resp: data=json.loads(resp.read().decode())
        content=re.sub(r'^```(?:json)?\s*|\s*```$','',data['choices'][0]['message']['content'].strip()); out=json.loads(content); out['source']='analyse générée par IA'; return jsonify(out)
    except Exception as e:
        return jsonify(error=f"Impossible de générer l'analyse IA ({type(e).__name__}). Vérifie la configuration API.",source='erreur IA'),502

@app.get('/report')
def report_page(): return render_template('report.html')

@app.get('/certificate')
def certificate():
    key=learner_key(); con=connect(); learner=con.execute('SELECT name FROM learners WHERE learner_key=?',(key,)).fetchone(); count=con.execute('SELECT COUNT(*) n FROM completions WHERE learner_key=?',(key,)).fetchone()['n']; avg=con.execute('SELECT AVG(score) a FROM attempts WHERE learner_key=?',(key,)).fetchone()['a']; con.close()
    eligible=count==len(MODULES) and (avg or 0)>=7
    return render_template('certificate.html',name=learner['name'] if learner else 'Étudiant',eligible=eligible,completed=count,total=len(MODULES),average=round(avg or 0,1),date=datetime.now().strftime('%d/%m/%Y'),code=hashlib.sha256(learner_key().encode()).hexdigest()[:8].upper())

@app.get('/api/health')
def health(): return jsonify(ok=True,ai_configured=bool(os.getenv('OPENAI_API_KEY')),modules=len(MODULES))

if __name__=='__main__':
    app.run(host=os.getenv('HOST','0.0.0.0'),port=int(os.getenv('PORT','5000')),debug=os.getenv('FLASK_DEBUG','0')=='1')
