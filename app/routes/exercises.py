from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import get_db

bp = Blueprint('exercises', __name__, url_prefix='/exercises')

@bp.route('/', methods=['GET', 'POST'])
def manage_exercises():
    db = get_db()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        muscle_group = request.form.get('muscle_group', '').strip()

        if name and muscle_group:
            db.execute("""
                INSERT OR IGNORE INTO exercises (name, muscle_group)
                VALUES (?, ?)
            """, (name, muscle_group))
            db.commit()
            return redirect(url_for('exercises.manage_exercises'))

    exercises = db.execute(
        "SELECT * FROM exercises ORDER BY muscle_group ASC, name ASC"
    ).fetchall()
    return render_template('exercises.html', exercises=exercises)
