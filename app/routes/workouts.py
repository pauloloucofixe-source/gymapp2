from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.db import get_db
from datetime import datetime
from zoneinfo import ZoneInfo

bp = Blueprint('workouts', __name__)

def get_today_pt():
    return datetime.now(ZoneInfo("Europe/Lisbon")).strftime('%Y-%m-%d')

def wants_json():
    return request.headers.get('X-Requested-With') == 'fetch'

def greeting_for(hour):
    if hour < 6:
        return "Boa madrugada"
    if hour < 12:
        return "Bom dia"
    if hour < 20:
        return "Boa tarde"
    return "Boa noite"

@bp.route('/')
def index():
    db = get_db()
    workouts = db.execute(
        "SELECT * FROM workouts ORDER BY date DESC LIMIT 10"
    ).fetchall()
    now = datetime.now(ZoneInfo("Europe/Lisbon"))
    greeting = greeting_for(now.hour)
    return render_template('index.html', workouts=workouts, greeting=greeting)

@bp.route('/workouts', methods=['GET', 'POST'])
def list_create_workouts():
    db = get_db()
    if request.method == 'POST':
        # Se não vier preenchido pelo formulário, assume o relógio do sistema
        date = request.form.get('date') or get_today_pt()
        category = request.form.get('category')
        notes = request.form.get('notes', '')

        cur = db.execute(
            "INSERT INTO workouts (date, category, notes) VALUES (?, ?, ?)",
            (date, category, notes)
        )
        db.commit()

        if wants_json():
            return jsonify({
                'id': cur.lastrowid,
                'date': date,
                'category': category,
                'notes': notes
            })
        return redirect(url_for('workouts.list_create_workouts'))

    today = get_today_pt()
    workouts = db.execute("SELECT * FROM workouts ORDER BY date DESC").fetchall()
    return render_template('workouts.html', workouts=workouts, today=today)

@bp.route('/workouts/<int:workout_id>', methods=['DELETE'])
def delete_workout(workout_id):
    db = get_db()
    db.execute("DELETE FROM workouts WHERE id = ?", (workout_id,))
    db.commit()
    return jsonify({'ok': True})

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

        set_number = current_sets + 1
        cur = db.execute(
            "INSERT INTO sets (workout_id, exercise_id, set_number, reps, weight) VALUES (?, ?, ?, ?, ?)",
            (workout_id, exercise_id, set_number, reps, weight)
        )
        db.commit()

        if wants_json():
            exercise = db.execute("SELECT name FROM exercises WHERE id = ?", (exercise_id,)).fetchone()
            return jsonify({
                'id': cur.lastrowid,
                'exercise_name': exercise['name'] if exercise else '',
                'set_number': set_number,
                'reps': reps,
                'weight': weight
            })
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

    # Exercícios já usados neste treino, com a última carga/reps, do mais recente para o mais antigo
    # (a extensão do SQLite garante que reps/weight vêm da mesma linha do MAX(s.id))
    used_exercises = db.execute("""
        SELECT e.id, e.name, e.muscle_group, s.reps as last_reps, s.weight as last_weight,
               MAX(s.id) as last_set_id
        FROM sets s
        JOIN exercises e ON s.exercise_id = e.id
        WHERE s.workout_id = ?
        GROUP BY s.exercise_id
        ORDER BY last_set_id DESC
    """, (workout_id,)).fetchall()

    last_set = None
    if sets:
        last_row = max(sets, key=lambda s: s['id'])
        last_exercise_id = db.execute(
            "SELECT exercise_id FROM sets WHERE id = ?", (last_row['id'],)
        ).fetchone()['exercise_id']
        last_set = {
            'exercise_id': last_exercise_id,
            'exercise_name': last_row['exercise_name'],
            'reps': last_row['reps'],
            'weight': last_row['weight']
        }

    return render_template(
        'workout_detail.html', workout=workout, exercises=exercises, sets=sets,
        used_exercises=used_exercises, last_set=last_set
    )

@bp.route('/workouts/<int:workout_id>/sets/<int:set_id>', methods=['DELETE'])
def delete_set(workout_id, set_id):
    db = get_db()
    db.execute("DELETE FROM sets WHERE id = ? AND workout_id = ?", (set_id, workout_id))
    db.commit()
    return jsonify({'ok': True})
