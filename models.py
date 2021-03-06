from peewee import *
from flask_bcrypt import generate_password_hash
from flask_login import UserMixin


DATABASE = SqliteDatabase('journal.db')


class Entry(Model):
    title = CharField()
    slug = CharField(unique=True)
    date = DateField()
    time = IntegerField(default=0)
    learned = TextField()
    resources = TextField()

    class Meta:
        database = DATABASE


class Tag(Model):
    name = CharField(unique=True)

    class Meta:
        database = DATABASE


class EntryTag(Model):
    entry = ForeignKeyField(Entry)
    tag = ForeignKeyField(Tag)

    class Meta:
        database = DATABASE


class User(UserMixin, Model):
    email = CharField(unique=True)
    password = CharField()

    class Meta:
        database = DATABASE

    @classmethod
    def create_user(cls, email, password):
        try:
            with DATABASE.transaction():
                cls.create(
                    email=email,
                    password=generate_password_hash(password)
                )
        except IntegrityError:
            raise ValueError("User already exists!")


def initialize():
    DATABASE.connect()
    DATABASE.create_tables([Entry, Tag, EntryTag, User], safe=True)
    DATABASE.close()
