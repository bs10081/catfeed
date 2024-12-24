from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///catfeed.db'
db = SQLAlchemy(app)

class FeedingRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    food_type = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(10), default='g')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    records = FeedingRecord.query.order_by(FeedingRecord.timestamp.desc()).all()
    return render_template('index.html', records=records)

@app.route('/add_record', methods=['POST'])
def add_record():
    food_type = request.form.get('food_type')
    amount = float(request.form.get('amount'))
    notes = request.form.get('notes')
    
    new_record = FeedingRecord(
        food_type=food_type,
        amount=amount,
        notes=notes
    )
    
    db.session.add(new_record)
    db.session.commit()
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
