from flask import Flask, jsonify, request, Response
import json
import datetime
from BookModel import Book
from UserModel import User
from settings import app
import jwt

from functools import wraps

# books = [
#     {
#         'name': 'Green Eggs and Ham',
#         'price': 7.99,
#         'isbn': 11
#     },
#     {
#         'name': 'The Cat In The Hat',
#         'price': 5.99,
#         'isbn': 12
#     },
#     {
#         'name': 'Steave Jobs Biography',
#         'price': 25.00,
#         'isbn': 40
#     },
#     {
#         'name': 'How to do somth meaningfull',
#         'price': 4.00,
#         'isbn': 50
#     }
# ]


# books = Book.get_all_books()



@app.route('/login', methods=['POST'])
def get_token():
    try:
        request_data = request.get_json()
        login = request_data['username']
        password = request_data['password']
        
        match = User.username_password_match(login, password)

        if match:
            expiration_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=100)
            token = jwt.encode({'exp': expiration_date}, app.config['SECRET_KEY'], algorithm='HS256')
            return token
        else:
            return Response('', 401, mimetype='application/json')
    except:
        return Response('', 401, mimetype='application/json')
    
    
@app.route('/')
def index():
    return "Flask home view;"


def token_required(f):
    """decorator for token validation"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.args.get('token')
        try:
            jwt.decode(token, app.config['SECRET_KEY'])
            return f(*args, **kwargs)
        except:
            return jsonify({"error": "Need a valid token to view this page"}), 401
    return wrapper


# GET /books?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1ODU4NTE2OTd9.rLuhABUHpQueIrV724JPO-Mg_0dnNrcsTPsTlymhEZ4
@app.route('/books')
def get_books():
    # token = request.args.get('token')
    # try:
    #     jwt.decode(token, app.config['SECRET_KEY'])
    # except:
    #     return jsonify({'error': 'Need a valid token to view ths page'}), 401
    return jsonify({'books': Book.get_all_books()})
    

# GET /books/3432
@app.route('/books/<int:isbn>')
def get_books_by_isbn(isbn):
    return_value = Book.get_book(isbn)
    return jsonify(return_value)


# POST /books
# {
#     'name': 'New book name',
#     'price': 1.25,
#     'isbn': 100
# }
@app.route('/books', methods=['POST'])
@token_required
def add_book():
    request_data = request.get_json(force=True)
    if validBookObject(request_data):
        Book.add_book(request_data['name'], request_data['price'], request_data['isbn'])
        response = Response("", "201", mimetype="application/json")
        response.headers['Location'] = "/books/" + str(request_data['isbn'])
        return response
    else:
        invalidBookObjectErrorMsg = {
            "error": "Wrong book object passed in request",
            "helpString": "Data passed in similar to this {'name': bookName, 'price': 4.99, 'isbn': 453}"
        }
        response = Response(json.dumps(invalidBookObjectErrorMsg), 400, mimetype='application/json')
    return response


def validBookObject(bookObject):
    if 'name' in bookObject and \
        'price' in bookObject and \
        'isbn' in bookObject:
        return True
    else:
        return False


# PUT /books/3432
# {
#     'name': 'The new name',
#     'price': 0.99
# }
@app.route('/books/<int:isbn>', methods=['PUT'])
@token_required
def set_book(isbn):
    request_data = request.get_json(force=True)
    if (not valid_put_request_data(request_data)):
        invalidBookObjectErrorMsg = {
            "error": "Wrong book object passed in request",
            "helpString": "Data passed in similar to this {'name': bookName, 'price': 4.99}"
        }
        response = Response(json.dumps(invalidBookObjectErrorMsg), 400, mimetype='application/json')
        return response
    Book.replace_book(isbn, request_data['name'], request_data['price'])
    response = Response("", status=204)
    return response


# PATCH /books/3432
# {
#     'name': 'The new name' (or 'price', or both)
# }
@app.route('/books/<int:isbn>', methods=['PATCH'])
@token_required
def update_book(isbn):
    request_data = request.get_json(force=True)
    if('name' in request_data):
        is_updated = Book.update_book_name(isbn, _name=request_data['name'])
    if('price' in request_data):
        is_updated = Book.update_book_price(isbn, _price=request_data['price'])
    if is_updated:
        response = Response("", 204)
        response.headers['Location'] = '/books/' + str(isbn)
        return response
    invalidRequestObject = {
        "error": "Book with ISBN number that was provided was not found"
    }
    return Response(json.dumps(invalidRequestObject), status=404, mimetype="application/json")


def valid_put_request_data(request_data):
    if ('name' in request_data and 'price' in request_data):
        return True
    else:
        return False


@app.route('/books/<int:isbn>', methods=['DELETE'])
@token_required
def delete_book(isbn):
    if Book.delete_book(isbn):
        response = Response("", status=204)
        return response
    invalidBookObjectErrorMsg = {
        'error': 'Book with the ISBN number that was provided was not found, so therefore unable to delete'
    }
    response = Response(json.dumps(invalidBookObjectErrorMsg), status=404, mimetype='application/json')
    return response


app.run(port=5000, debug=True)
