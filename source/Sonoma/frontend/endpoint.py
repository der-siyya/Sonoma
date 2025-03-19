
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash, send_from_directory, Response, make_response, abort
import werkzeug
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import jwt
import datetime
import os
import base64
import hashlib
import hmac
import json
import random
import string
import time
import uuid
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = ''.join(random.choices(string.ascii_letters + string.digits, k=64))
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=30)

def obfuscated_token_generator(length=128):
    return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=length))

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Missing token'}), 401
        try:
            data = jwt.decode(token.split(" ")[1], app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['user']
        except:
            return jsonify({'message': 'Invalid token'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/api/v1/login', methods=['POST'])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required"'})
    
    hashed_password = hashlib.sha512(auth.password.encode()).hexdigest()
    if auth.username == 'admin' and hashed_password == os.getenv('ADMIN_PASSWORD_HASH'):
        token = jwt.encode({'user': auth.username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({'token': token})
    
    return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required"'})

@app.route('/api/v1/protected', methods=['GET'])
@require_auth
def protected(current_user):
    return jsonify({'message': f'Hello {current_user}!', 'timestamp': int(time.time()), 'nonce': str(uuid.uuid4())})

@app.route('/api/v1/data/<path:filename>')
@require_auth
def serve_file(current_user, filename):
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', filename):
        abort(400)
    try:
        return send_from_directory('data', filename)
    except:
        abort(404)

@app.route('/api/v1/upload', methods=['POST'])
@require_auth
def upload_file(current_user):
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if file:
        filename = str(uuid.uuid4()) + '_' + werkzeug.utils.secure_filename(file.filename)
        file.save(os.path.join('data', filename))
        return jsonify({'message': 'File uploaded successfully', 'filename': filename})
@app.route('/api/v1/process', methods=['POST'])
@require_auth
def process_data(current_user):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    processed = base64.b64encode(hmac.new(
        app.config['SECRET_KEY'].encode(),
        json.dumps(data, sort_keys=True).encode(),
        hashlib.sha512
    ).digest()).decode()
    
    return jsonify({
        'result': processed,
        'timestamp': int(time.time()),
        'signature': hmac.new(
            app.config['SECRET_KEY'].encode(),
            processed.encode(),
            hashlib.sha512
        ).hexdigest()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
