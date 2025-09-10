from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqalchemy import SQAlechemy
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "shadow_dodge.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQAlchemy(app)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scores = db.relationship('Score', backref='player', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'total_games': len(self.scores),
            'best_score': max([s.score for s in self.scores]) if self.scores else 0,
            'average_score': sum([s.score for s in self.scores]) / len(self.scores) if self.scores else 0
        }
        
class  Score(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    shadows_created = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'player_name': self.player.name,
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
        limit = request.args.get('limit', 10, type=int)
        difficulty = request.args.get('difficulty', None)
        query = Score.query
        
        if difficulty and difficulty in ['easy', 'medium', 'hard']:
            query = query.filter_by(difficulty=difficulty)
        scores = query.order_by(Score.score.desc()).limit(limit).all()
        
        return jsonify({
            'leaderboard': [score.to_dict() for score in scores],
            'total_count': len(scores)
        })
        
    except Exception as e:
        return jsonify({'error':str(e)}), 500

@app.route('/api/player/<player_name>/stats', methods=['GET'])
def get_player_stats(player_name):
    try:
        player = Player.query.filter_by(name=player_name).first()
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        scores = Score.query.filter_by(player_id=player.id).order_by(Score.created_at.desc()).all()
        
        total_games = len(scores)
        if total_games == 0:
            return jsonify({'error': 'No games found for this player'}), 404
        best_score = max(score.score for score in scores)
        average_score = sum(score.score for score in scores) / total_games
        total_shadows = sum(score.shadows_created for score in scores)
        
        difficulty_stats = {}
        for difficulty in ['easy', 'medium', 'hard']:
            diff_scores = [s for s in scores if s.difficulty == difficulty]
            if diff_scores:
                difficulty_stats[difficulty] = {
                    'games_played': len(diff_scores),
                    'best_score': max(s.score for s in diff_scores),
                    'average_score': sum(s.score for s in diff_scores) / len(diff_scores)
                }
            else:
                difficulty_states[difficulty] = {
                    'games_played': 0,
                    'best_score': 0,
                    'average_score': 0
                }
        recent_games = [score.to_dict() for score in scores[:5]]
        return jsonify({
            'player': player.to_dict(),
            'stats': {
                'total_games': total_games,
                'best_score': best_score,
                'average_score': round(average_score, 2)
                'total_shadows_created': total_shadows,
                'difficulty_breakdown': difficulty_stats
            },
            'recent_games': recent_games
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/global-stats', methods=['GET'])
def get_global_stats():
    try:
        total_player = Player.query.count()
        total_games = Score.query.count()
        
        if total_games == 0:
            return jsonify({
                'total_players': total_players,
                'total_games': total_games,
                'global_high_score': 0,
                'average_score': 0,
                'difficulty_distribution': {'easy': 0, 'medium': 0, 'hard': 0}
            })
        global_high_score = db.session.query(db.func.max(Score.score)).scalar()
        average_score = db.session.query(db.func.avg(Score.score)).scalar()
        difficulty_counts = {}
        for difficulty in ['easy', 'medium', 'hard']:
            count = Score.query.filter_by(difficulty=difficulty).count()
            difficulty_counts[difficulty] = count
        
        top_players_query = db.session.query(
            Player.name,
            db.func.avg(Score.score).label('avg_score'),
            db.func.count(Score.id).label('game_count')
        ).join(Score).group_by(Player.id).having(
            db.func.count(Score.id) >= 5
        ).order_by(db.func.avg(Score.score).desc()).limit(3)
        
        top_players = []
        for name, avg_score, game_count in tpp_players_query:
            top_players.append({
                'name': name,
                'average_score': round(avg_score, 2),
                'total_games': game_count
            })
        return jsonify({
            'total_players': total_players,
            'total_games': total_games,
            'global_high_score': global_high_score,
            'average_score': round(average_score, 2) if average_score else 0,
            'difficulty_distribution': difficuly_counts,
            'top_consistent_players': top_players
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

app.route('/api/scores/recent', methods=['GET'])
def get_recent_scores():
    try:
        limit = request.args.get('limit', 20, type=int)
        scores = Score.query.order_by(Score.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'recent_scores': [score.to_dict() for score in scores]
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.rote('/api/reset-database', methods=['POST'])
def reset_database():
    try:
        confirm = request.get_json().get('confirm', False)
        if not confirm:
            return jsonify({'error': 'Confirmation required in order to reset database'}), 400
        db.drop_all()
        db.create_all()
        return jsonify({'message': 'Database rest successful!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server errror'}), 500

if __name__ == '__main__':
    print("Starting Shadow Dodge backend...")
    print("Avalable Endpoints: ")
    print(" GET /api/health = Health check")
    print(" POST /api/scores - Submit new score")
    print()


#future additions
