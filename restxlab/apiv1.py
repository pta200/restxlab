from flask import Blueprint
from flask_restx import Api

from apis.books import books_ns

blueprint = Blueprint('api', __name__)
api = Api(blueprint,
          title='Apis',
          version='1.0',
          description='Apis for testing')

api.add_namespace(books_ns)
