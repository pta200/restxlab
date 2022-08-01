from marshmallow import Schema, fields


class BookRequestSchema(Schema):
    title = fields.Str(required=True)
    author = fields.Str(required=True)

book_request_schema = BookRequestSchema()