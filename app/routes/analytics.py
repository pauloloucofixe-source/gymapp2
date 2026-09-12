from flask import Blueprint, render_template, jsonify
from app.db import get_db

bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@bp.route('/')
def analytics_view():
    return render_template('analytics.html')

@bp.route('/api/weight-trend')
def weight_trend():
    db = get_db()
    records = db.execute(
        "SELECT date, weight FROM body_weight ORDER BY date ASC"
    ).fetchall()
    return jsonify([{'date': r['date'], 'weight': r['weight']} for r in records])

@bp.route('/api/exercise-progress/<int:exercise_id>')
def exercise_progress(exercise_id):
    db = get_db()
    # Pega na carga máxima alcançada por dia para o exercício selecionado
    records = db.execute("""
        SELECT w.date, MAX(s.weight) as max_weight
        FROM sets s
        JOIN workouts w ON s.workout_id = w.id
        WHERE s.exercise_id = ?
        GROUP BY w.date
        ORDER BY w.date ASC
    """, (exercise_id,)).fetchall()
    return jsonify([{'date': r['date'], 'max_weight': r['max_weight']} for r in records])