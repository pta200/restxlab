from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import backref, relationship
from sqlalchemy.dialects.postgresql import UUID
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields
from .database import Base, db_session
import uuid


class Author(Base):
    __tablename__ = "authors"
    author_uid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    books = relationship("Book", back_populates="author")

    def __init__(self, name=None):
        self.author_uid = uuid.uuid4()
        self.name = name

    def __repr__(self):
        return "<Author(name={self.name!r})>".format(self=self)

class Book(Base):
    __tablename__ = 'books'
    book_uid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    author_uid = Column(UUID(as_uuid=True), ForeignKey("authors.author_uid"))
    author = relationship("Author", back_populates="books")

    def __init__(self, title=None, author=None):
        self.book_uid = uuid.uuid4()
        self.title = title
        self.author = author


class BookSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Book
        sqla_session = db_session

class AuthorSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Author
        sqla_session = db_session

    books = fields.Nested(BookSchema, many=True)



