from flask import Blueprint, render_template, request, redirect, url_for
from app.db import get_db
from datetime import datetime
from zoneinfo import ZoneInfo

bp = Blueprint('workouts', __name__)

def get_today_pt():
    return datetime.now(ZoneInfo("Europe/Lisbon")).strftime('%Y-%m-%d')

@bp.route('/')
def index():
    db = get_db()
    workouts = db.execute(
        "SELECT * FROM workouts ORDER BY date DESC LIMIT 10"
    ).fetchall()
    return render_template('index.html', workouts=workouts)

@bp.route('/workouts', methods=['GET', 'POST'])
def list_create_workouts():
    db = get_db()
    if request.method == 'POST':
        # Se não vier preenchido pelo formulário, assume o relógio do sistema
        date = request.form.get('date') or get_today_pt()
        category = request.form.get('category')
        notes = request.form.get('notes', '')

        db.execute(
            "INSERT INTO workouts (date, category, notes) VALUES (?, ?, ?)",
            (date, category, notes)
        )
        db.commit()
        return redirect(url_for('workouts.list_create_workouts'))

    today = get_today_pt()
    workouts = db.execute("SELECT * FROM workouts ORDER BY date DESC").fetchall()
    return render_template('workouts.html', workouts=workouts, today=today)

@bp.route('/workouts/<int:workout_id>', methods=['GET', 'POST'])
def workout_detail(workout_id):
    db = get_db()
    if request.method == 'POST':
        exercise_id = request.form['exercise_id']
        reps = int(request.form['reps'])
        weight = float(request.form['weight'])

        current_sets = db.execute(
            "SELECT COUNT(*) as count FROM sets WHERE workout_id = ? AND exercise_id = ?",
            (workout_id, exercise_id)
        ).fetchone()['count']

        db.execute(
            "INSERT INTO sets (workout_id, exercise_id, set_number, reps, weight) VALUES (?, ?, ?, ?, ?)",
            (workout_id, exercise_id, current_sets + 1, reps, weight)
        )
        db.commit()
        return redirect(url_for('workouts.workout_detail', workout_id=workout_id))

    workout = db.execute("SELECT * FROM workouts WHERE id = ?", (workout_id,)).fetchone()
    exercises = db.execute("SELECT * FROM exercises ORDER BY muscle_group, name").fetchall()
    
    sets = db.execute("""
        SELECT s.id, e.name as exercise_name, s.set_number, s.reps, s.weight
        FROM sets s
        JOIN exercises e ON s.exercise_id = e.id
        WHERE s.workout_id = ?
        ORDER BY s.id ASC
    """, (workout_id,)).fetchall()

    return render_template('workout_detail.html', workout=workout, exercises=exercises, sets=sets)