from flask import Blueprint, render_template

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
