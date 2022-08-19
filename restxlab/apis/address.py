'''
Pure flask-restx models
'''

from datetime import datetime
import uuid
from flask_restx import Resource, Api, fields, Namespace

address_ns = Namespace('address', description='Restx lab with library schema')
logger = logging.getLogger("app.address")


address_request = address_ns.model('RequestModel', {
    'name': fields.String,
    'address': fields.String
})

address_response = address_ns.model('ResponseModel', {
    'uid': fields.String,
    'name': fields.String,
    'address': fields.String,
    'date_updated': fields.DateTime(dt_format='rfc822'),
})


@api.route('/hello')
class HelloWorld(Resource):
    @address_ns.expect(address_request, validate=True)
    @address_ns.marshal_with(address_response)
    def post(self):
        print(datetime.now())
        response = {'name':address_ns.payload['name'],'address':address_ns.payload['address'],
                    'date_updated':datetime.now(),'uid':str(uuid.uuid4())}
        return response
