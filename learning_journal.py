import os
import re

from flask import (Flask, render_template, redirect, url_for,
                   send_from_directory, g, flash, request)
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
            return redirect(url_for('list'))
    return render_template('register.html', form=form)


@app.route('/')
@app.route('/list')
def list():
    entries = models.Entry.select().order_by('-date')
    return render_template('index.html', entries=entries)


@app.route('/tag')
@app.route('/tag/<name>')
def tag(name=None):
    if name is None:
        tags = models.Tag.select().order_by('name')
        return render_template('tags_list.html', tags=tags)
    tag = models.Tag.get(models.Tag.name == name)
    entries = (models.Entry
               .select()
               .join(models.EntryTag)
               .join(models.Tag)
               .where(models.EntryTag.tag == tag)
               )
    return render_template('tags.html', tag=tag, entries=entries)


@app.route('/entry', methods=('GET', 'POST'))
@app.route('/entry/<slug>', methods=('GET', 'POST'))
@login_required
def entry(slug=None):
    """Display entry form for editing an entry or creating a new entry
       If no slug is passed in, the new entry template is rendered.
       If a slug is passed in, the edit entry template is rendered.
       Both templates share EntryForm
    """
    if slug is None:
        form = forms.EntryForm()
        if form.validate_on_submit():
            entry = models.Entry.create(
                title=form.title.data,
                slug=slugify(form.title.data),
                date=form.date.data,
                time=form.time.data,
                learned=form.learned.data,
                resources=form.resources.data
            )
            tags = form.tags.data.split(',')
            for form_tag in tags:
                form_tag = form_tag.strip()
                try:
                    tag = models.Tag.get(models.Tag.name == form_tag)
                except models.DoesNotExist:
                    tag = models.Tag.create(
                        name=form_tag
                    )
                else:
                    tag.Name = form_tag
                    tag.save()
                finally:
                    models.EntryTag.create(
                        tag=tag,
                        entry=entry
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
            tags = (models.Tag
                    .select(models.Tag)
                    .join(models.EntryTag)
                    .join(models.Entry)
                    .where(models.EntryTag.entry == entry)
                    .group_by(models.Tag)
            )
            tags_string = ''
            for tag in tags:
                tags_string = '{}, {}'.format(tags_string, tag.name)
            if ',' in tags_string:
                tags_string = tags_string[2:]
            if request.method == 'GET':
                form.tags.data = tags_string
            if form.validate_on_submit():
                entry.title = form.title.data
                entry.slug = slugify(form.title.data)
                entry.time = form.time.data
                entry.date = form.date.data
                entry.learned = form.learned.data
                entry.resources = form.resources.data
                entry.save()

                delete_entry_tags(entry)

                tags = form.tags.data.split(',')
                for form_tag in tags:
                    form_tag = form_tag.strip()
                    try:
                        tag = models.Tag.get(models.Tag.name == form_tag)
                    except models.DoesNotExist:
                        tag = models.Tag.create(
                            name=form_tag
                        )
                    finally:
                        models.EntryTag.create(
                            tag=tag,
                            entry=entry
                        )

                return redirect(url_for('details', slug=entry.slug))
            return render_template('edit.html', form=form)


@app.errorhandler(404)
@app.route('/details/<slug>')
def details(slug):
    try:
        entry = models.Entry.get(models.Entry.slug == slug)
        tags = (models.Tag
                .select(models.Tag)
                .join(models.EntryTag)
                .join(models.Entry)
                .where(models.EntryTag.entry == entry)
                .group_by(models.Tag)
                )
    except models.DoesNotExist:
        return render_template('404.html'), 404
    else:
        return render_template('detail.html', entry=entry, tags=tags)


@app.route('/entry/delete/<slug>')
@login_required
def delete(slug):
    try:
        entry = models.Entry.get(models.Entry.slug == slug)
    except models.DoesNotExist:
        return render_template('404.html'), 404
    else:
        delete_entry_tags(entry)
        entry.delete_instance()
        return redirect(url_for('list'))


@app.route('/favicon.ico')
def favicon():
    """Route/view for blank favicon to avoid 404 error when loading each page"""
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


def delete_entry_tags(entry):
    """Delete all tags for an entry and any unused tags"""
    query = models.EntryTag.delete().where(models.EntryTag.entry == entry)
    query.execute()
    delete_unused_tags()


def delete_unused_tags():
    """Removes unused tags in order to keep things tidy"""
    tags = models.Tag.select()
    for tag in tags:
        if not models.EntryTag.select().where(models.EntryTag.tag == tag).count():
            tag.delete_instance()


def slugify(title, counter=None):
    """Creates a URL slug based on a title
       If a slug already exists, add -1 to the title, then -2 and so on
    """
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
