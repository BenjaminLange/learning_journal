import os
import re

from flask import (Flask, render_template, redirect, url_for,
                   send_from_directory, g, flash)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from flask_bcrypt import check_password_hash

import models
import forms


app = Flask(__name__)
app.secret_key = 'aljhgLI&TYOL&Ut likP(O*^&&tg lLK<UYJHFGVHN)'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@app.before_request
def before_request():
    g.db = models.DATABASE
    g.db.connect()
    g.user = current_user


@app.after_request
def after_request(response):
    g.db.close()
    return response


@login_manager.user_loader
def load_user(userid):
    try:
        return models.User.get(models.User.id == userid)
    except models.DoesNotExist:
        return None


@app.route('/login', methods=('GET', 'POST'))
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.email == form.email.data)
        except models.DoesNotExist:
            flash("Your email or password doesn't match!", "error")
        else:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("Logged in successfully!", "success")
                return redirect(url_for('list'))
            else:
                flash("Your email or password doesn't match!", "error")
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('list'))


@app.route('/register', methods=('GET', 'POST'))
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():
        try:
            models.User.create_user(form.email.data, form.password.data)
        except ValueError:
            flash("That email address already has an associated account!", "error")
            return render_template('register.html', form=form)
        else:
            flash("You've been registered!", "success")
            return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/')
@app.route('/list')
def list():
    entries = models.Entry.select().order_by('-date')
    return render_template('index.html', entries=entries)


@app.route('/entry', methods=('GET', 'POST'))
@app.route('/entry/<slug>', methods=('GET', 'POST'))
@login_required
def entry(slug=None):
    if slug is None:
        form = forms.EntryForm()
        if form.validate_on_submit():
            models.Entry.create(
                title=form.title.data,
                slug=slugify(form.title.data),
                date=form.date.data,
                time=form.time.data,
                learned=form.learned.data,
                resources=form.resources.data
            )
            return redirect(url_for('list'))
        return render_template('new.html', form=form)
    else:
        try:
            entry = models.Entry.get(models.Entry.slug == slug)
        except models.DoesNotExist:
            return render_template('404.html'), 404
        else:
            form = forms.EntryForm(obj=entry)
            if form.validate_on_submit():
                entry.title = form.title.data
                entry.slug = slugify(form.title.data)
                entry.time = form.time.data
                entry.date = form.date.data
                entry.learned = form.learned.data
                entry.resources = form.resources.data
                entry.save()
                return redirect(url_for('details', slug=entry.slug))
            return render_template('edit.html', form=form)


@app.errorhandler(404)
@app.route('/details/<slug>')
def details(slug):
    try:
        entry = models.Entry.get(models.Entry.slug == slug)
    except models.DoesNotExist:
        return render_template('404.html'), 404
    else:
        return render_template('detail.html', entry=entry)


@app.route('/entry/delete/<slug>')
@login_required
def delete(entry_id):
    try:
        entry = models.Entry.get(models.Entry.slug == slug)
    except models.DoesNotExist:
        return render_template('404.html'), 404
    else:
        entry.delete_instance()
        return redirect(url_for('list'))


@app.route('/favicon.ico')
def favicon():
    """Route/view for blank favicon to avoid 404 error when loading each page"""
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


def slugify(title, counter=None):
    if counter:
        slug = re.sub('[^\w]+', '-', title.lower())
        slug = "{}-{}".format(slug, counter)
    else:
        counter = 0
        slug = re.sub('[^\w]+', '-', title.lower())
    entries = models.Entry.select().where(models.Entry.slug == slug).count()
    if entries > 0:
        return slugify(title, counter + 1)
    return slug


if __name__ == '__main__':
    models.initialize()
    app.run()
