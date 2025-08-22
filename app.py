from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash, get_flashed_messages
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-change-me')

from blueprints.chatbot import chatbot_bp
from blueprints.Predict import predict_bp

app.register_blueprint(chatbot_bp)
app.register_blueprint(predict_bp)
@app.route('/')
def hello_world():  # put application's code here
    return render_template('base.html')

@app.route('/team')
def team():
    return render_template('team.html')

@app.route('/predict')
def predict():
    return render_template('predict.html')

if __name__ == '__main__':
    app.run()
