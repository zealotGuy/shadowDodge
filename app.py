frmo flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "shadow_dodge.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQAlchemy(app)
class Player(db.Model):
    id = db.Column(db.Integer, primar_key=True)
    name = db.Column(db.String(50), nullable=False)
    created_at = sb.Column(db.DateTime, default=datetime.utcnow)
    scores = db.relationship('Score', backref='player', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'total_games': len(self.scores),
            'best_score': max((score.value for score in self.scores), default=0)
        }
class Score(db.Model):
    id = db.column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id', nullable=False))
    score = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    shadows_created = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'player_id': self.player_id,
            'score': self.score,
            'difficulty': self.difficulty,
            'shadows_created': self.shadows_created,
            'created_at': self.created_at.isoformat()
        }

with app.app_context():
    db.create_all()

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        limit = request = args.get('limit', 10, type=int)
        difficulty = reques.args.get('difficulty', None)
        
        query = Score.query
        
        if difficulty and difficulty in ['easy', 'medium', 'hard']:
            query = query.filter_by(difficulty=difficulty)



#unfinished
