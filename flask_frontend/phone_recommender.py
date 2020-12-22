from flask import Flask, render_template, session, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired
import pymongo

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'

bootstrap = Bootstrap(app)
moment = Moment(app)

client = pymongo.MongoClient([URI_MONGODB])
db = client["Amazon"]
ProductCollection = db["Productos"] 


class NameForm(FlaskForm):
    name = IntegerField('¿Precio máximo?', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    result = []
    precio_usuario = form.name.data
    if form.validate_on_submit():
        result = list(client['Amazon']['Productos'].aggregate([
        {
        '$match': {
        'Precio': {
        '$lte': precio_usuario
        },
        'Score': {
        '$exists': True
        }
        }
        }, {
        '$sort': {
        'Score': -1
        }
        }, {
        '$limit': 10
        }
        ])) 
    for resultado in result:
        if resultado["Marca"] is None:
            resultado["Marca"]="Marca sin especificar" 
    for i in result:
        print(i['Nombre'])
    
    return render_template('index.html', form=form, resultados=result)