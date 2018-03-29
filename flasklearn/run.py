from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_bootstrap import Bootstrap
from jianzhi import JianZhi


class NameFrom(FlaskForm):
    city = StringField('所在市名：', validators=[DataRequired()])
    district = StringField('所在区县名：', validators=[DataRequired()])
    submit = SubmitField('确认')


from flask import Flask, render_template, request, session, flash, redirect, url_for

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sdadasd'
bootstrap = Bootstrap(app)


@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameFrom()
    city = None
    distinct = None
    if form.validate_on_submit():
        session['city'] = form.city.data
        session['district'] = form.district.data
        return redirect(url_for('result'))
    return render_template('index.html', form=form, city=city, distinct=distinct)


@app.route('/result', methods=['GET', 'POST'])
def result():
    city = session['city']
    district = session['district']
    jz = JianZhi(city, district)
    results = jz.get_jobs()
    if isinstance(results, str):
        flash(results)
        return redirect(url_for('index'))
    return render_template('result.html', results=results)



if __name__ == '__main__':
    app.run(debug=True)
