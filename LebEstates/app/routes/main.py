from flask import Blueprint, render_template, session, redirect, url_for
from app.models.users import Users

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def homepage():
    return render_template('homepage.html')


@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/consultation')
def consultation():
    return render_template('consultation.html')

@main_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    user = Users.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login_page'))
    return render_template('dashboard.html', user=user)

@main_bp.route('/control-panel')
def control_panel():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    user = Users.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login_page'))
    return render_template('control_panel.html', user=user)

@main_bp.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    user = Users.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login_page'))
    return render_template('profile.html', user=user)
