import re
import uuid

from datetime import datetime
from sqlalchemy import Table, Column, MetaData, ForeignKey
from sqlalchemy import types, orm
from sqlalchemy.sql import select
from sqlalchemy.orm import mapper, relationship
from sqlalchemy import func
from sqlalchemy.ext.declarative import declarative_base
from slugify import slugify

import ckan.model as model
from ckan.lib.base import *

from ckan.model.package import package_table

log = __import__('logging').getLogger(__name__)

Base = declarative_base()

def make_uuid():
    return unicode(uuid.uuid4())

metadata = MetaData()

class Post(Base):
    """
    """
    __tablename__ = 'blog_post'

    id = Column(types.UnicodeText,
           primary_key=True,
           default=make_uuid)
    title     = Column(types.UnicodeText, nullable=False)
    url       = Column(types.UnicodeText, unique=True, nullable=False)
    content   = Column(types.UnicodeText, nullable=False)
    created   = Column(types.DateTime, default=datetime.now)
    user_id   = Column(types.UnicodeText, nullable=False, index=True)
    visible   = Column(types.Boolean, default=False)

    def __init__(self, title, content, user):
        self.user_id = user
        self.title = title
        self.content = content
        self.url = slugify(title)
        self.visible = True

    @classmethod
    def get(cls, id):
        return model.Session.query(cls).filter(cls.id==id).first()

    def __str__(self):
        return u"<Post: %s, url:%s, vis:%s>" % (self.user_id, self.url, self.visible)

    def __repr__(self):
        return u"<Post: %s, url:%s, vis:%s>" % (self.user_id, self.url, self.visible)

def init_tables(e):
    Base.metadata.create_all(e)
