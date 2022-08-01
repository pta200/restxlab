from flask_restx import Namespace, Resource
from core.db_models import Book, Author, BookSchema, AuthorSchema
from core.api_models import BookRequestSchema, book_request_schema
from flask import jsonify, make_response, request
import logging
from marshmallow import ValidationError
from core.database import db_session


books_ns = Namespace('library', description='Restx lab with library schema')
logger = logging.getLogger("app.models")

@books_ns.route('/books')
class ListBooks(Resource):
    def get(self):
        book_list = Book.query.all()
        logger.info("GOT LIST")
        book_schema = BookSchema(many=True)
        return book_schema.dump(book_list)

@books_ns.route('/authors')
class ListAuthors(Resource):
    def get(self):
        book_list = Author.query.all()
        logger.info("GOT LIST")
        author_schema = AuthorSchema(many=True)
        return author_schema.dump(book_list)


@books_ns.route('/book')
class ManageBooks(Resource):
    @books_ns.doc(BookRequestSchema)
    def post(self):
        try:
            logger.info("TRY TO LOAD")
            book_request = book_request_schema.load(request.get_json())
        except ValidationError as error:
            logger.error("Error parsing payload: %s", error.messages)
            response = {
                'message': 'Invalid arguments to new show request',
                'errors': error.messages
            }
            return make_response(jsonify(response), 400)

        logger.info("SAVE TO DB")

        new_author = Author(name=request.json['author'])
        db_session.add(new_author)

        new_book = Book(title=request.json['title'], author=new_author)
        db_session.add(new_book)
        db_session.flush()

        book_schema = BookSchema()

        return book_schema.dump(new_book)
