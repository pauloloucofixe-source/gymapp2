from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.db import get_db
from datetime import datetime
from zoneinfo import ZoneInfo

bp = Blueprint('body', __name__, url_prefix='/body')

def get_today_pt():
    return datetime.now(ZoneInfo("Europe/Lisbon")).strftime('%Y-%m-%d')

def wants_json():
    return request.headers.get('X-Requested-With') == 'fetch'

@bp.route('/', methods=['GET', 'POST'])
def body_tracking():
    db = get_db()
    if request.method == 'POST':
        date = request.form.get('date') or get_today_pt()
        weight = float(request.form['weight'])
        notes = request.form.get('notes', '')

        db.execute("""
            INSERT INTO body_weight (date, weight, notes)
            VALUES (?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET weight=excluded.weight, notes=excluded.notes
        """, (date, weight, notes))
        db.commit()

        if wants_json():
            record = db.execute("SELECT * FROM body_weight WHERE date = ?", (date,)).fetchone()
            return jsonify({
                'id': record['id'],
                'date': record['date'],
                'weight': record['weight'],
                'notes': record['notes']
            })
        return redirect(url_for('body.body_tracking'))

    today = get_today_pt()
    records = db.execute("SELECT * FROM body_weight ORDER BY date DESC LIMIT 30").fetchall()
    return render_template('body.html', records=records, today=today)

@bp.route('/<int:record_id>', methods=['DELETE'])
def delete_record(record_id):
    db = get_db()
    db.execute("DELETE FROM body_weight WHERE id = ?", (record_id,))
    db.commit()
    return jsonify({'ok': True})
