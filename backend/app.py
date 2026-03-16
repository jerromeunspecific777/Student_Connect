from flask import Flask, jsonify, request, make_response, redirect
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token, 
    jwt_required, get_jwt_identity, get_csrf_token, 
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies
)
from src.database import db 
import secrets
import os
import base64
from datetime import timedelta
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from src.utils import checkEnv, returnJWTSecret, decrypt, registerUser, genCode, validLogin, validCToken, validTToken, validNDB, validNToken, CheckTokensDB, getDB, updateSettings, unlinkDB, addSyncLog, can_sync, update_sync_time
from src.sync import sync_CanvasTodist, sync_CanvasNotion
from src.email_service import send_sync_email
from src.scheduler import init_scheduler, schedule_sync, remove_schedule, get_schedule
from src.logger import get_logger
import threading

logger = get_logger(__name__)


app = Flask(__name__)

if not checkEnv("JWT_SECRET_KEY"):
    secret_key = secrets.token_bytes(64)
    secret_key_b64 = base64.b64encode(secret_key).decode("utf-8")
    with open('.env', "a") as f:
        f.write(f"\nJWT_SECRET_KEY={secret_key_b64}\n")

app.config['JWT_SECRET_KEY'] = returnJWTSecret()
app.config['JWT_TOKEN_LOCATION'] = ['cookies']  # Look for token in cookies
app.config["JWT_CSRF_IN_COOKIES"] = True        # Enable CSRF in cookies
app.config["JWT_COOKIE_CSRF_PROTECT"] = True
app.config['JWT_ACCESS_COOKIE_NAME'] = 'token'  # Set the cookie name to 'token'
app.config["JWT_COOKIE_SECURE"] = True
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=3)
app.config['JWT_REFRESH_COOKIE_NAME'] = 'refresh_token'
app.config['JWT_REFRESH_COOKIE_PATH'] = '/api/refresh'  # Security: only send to refresh endpoint

CORS(app, supports_credentials=True, origins=["https://localhost:5173", "https://localhost:5174"])

@app.before_request
def log_request_info():
    if request.path != '/api/public-key':
        logger.info(f"Request: {request.method} {request.path}")

jwt = JWTManager(app)

# Initialize the background scheduler
init_scheduler(app)

if not os.path.exists('./src/private_key.pem'):

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    private_pass = secrets.token_bytes(64)
    private_pass_b64 = base64.b64encode(private_pass).decode("utf-8")

    with open('.env', "a") as f:
        f.write(f"\nPRIVATE_PASS={private_pass_b64}\n")

    with open("./src/private_key.pem", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(private_pass)
        ))

    public_key = private_key.public_key()
    with open("./src/public_key.pem", "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

# Missing token
@jwt.unauthorized_loader
def unauthorized_callback(error):
    return jsonify({"error": "Token is missing"}), 401

# Invalid token (e.g., malformed or wrong signature)
@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({"error": "Invalid token"}), 401

# Expired token
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    response = make_response(jsonify({"error": "Please Login Again"})) 
    response.delete_cookie('token', path='/')
    response.delete_cookie('csrf_access_token', path='/')
    response.delete_cookie('user', path='/')
    return response, 401

@app.route('/api/public-key', methods=['GET'])
def get_public_key():
    with open("./src/public_key.pem", "rb") as f:
        public_key_data = f.read()
    logger.info("Sent Public Key Data")    
    return public_key_data

@app.route('/api/validate-token', methods=['GET'])
@jwt_required()
def checkToken():
    response = make_response(jsonify({"message": "Token Is Valid"}))
    return response, 200

@app.route('/api/register', methods=['POST'])
def routeRegister():
     data = request.json
     encryptedName = data.get('name')
     encryptedEmail = data.get('email')

     response = registerUser(decrypt(encryptedName), decrypt(encryptedEmail))
     if response == 200:
          logger.info("Successfully Registered New User")
          return jsonify({'message': 'Login successful', 'token': 'abc123'}), 200
     elif response == 409:
          logger.info("User Already Exists")
          return jsonify({'error': 'Email Is Already Registered'}), 401
     elif response == 401:
          logger.error("PyMongo Error during registration")
          return jsonify({'error': 'Error Registering User, Try Again Later'}), 401

@app.route('/api/code', methods=['POST'])
def routeCode():
    data = request.json
    encryptedEmail = data.get('email')
    # print(decrypt(encryptedEmail)) # Kept commented or removed for privacy
    checkCode = genCode(decrypt(encryptedEmail))
    if checkCode == 200:
        logger.info("Code Generated Successfully")
        return jsonify({'message': 'Code Generated Successfully'}), 200
    elif checkCode == 401:
        logger.warning("Email Not Registered")
        return jsonify({'error': 'Email Not Registered, Please Register First'}), 401


@app.route('/api/login', methods=['POST'])
def routeLogin():
    data = request.json
    encryptedEmail = data.get('email')
    encryptedTimezone = data.get('timezone')
    encryptedCode = data.get('code')

    checkLogin = validLogin(decrypt(encryptedEmail), decrypt(encryptedCode), decrypt(encryptedTimezone))

    if checkLogin == 200:
            user_email = decrypt(encryptedEmail)
            access_token = create_access_token(identity=user_email)
            response = make_response(jsonify({"message": "Login Successful"}))
            set_access_cookies(response, access_token)
            
            remember_me = data.get('rememberMe', False)
            if remember_me:
                refresh_token = create_refresh_token(identity=user_email)
                set_refresh_cookies(response, refresh_token)
            
            response.set_cookie('user', encryptedEmail, httponly=True, secure=True, samesite='None', path='/')
            print("Login Successful")
            return response, 200
    elif checkLogin == 401:
            print("Invalid Code")
            return jsonify({'error': 'Invalid Code'}), 401
    elif checkLogin == 403:
            print("Code Expired")
            return jsonify({'error': 'Code Expired, Please Login Again'}), 403

@app.route('/api/refresh', methods=['POST'])
@jwt_required(refresh=True)
def routeRefresh():
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    response = make_response(jsonify({'refresh': True}))
    set_access_cookies(response, access_token)
    return response, 200

@app.route('/api/logout', methods=['GET'])
@jwt_required()
def routeLogout():
    response = make_response(jsonify({"message": "Logout Successful"}))
    unset_jwt_cookies(response)
    response.delete_cookie('user', path='/')
    return response, 200


@app.route('/api/token-protected', methods=['GET']) # this is for after the user login in
@jwt_required() #
def routeProtected():
    current_user = get_jwt_identity()
    print("Canvas Token", CheckTokensDB(current_user, "CToken"))
    print("Todist Token", CheckTokensDB(current_user, "TToken"))
    print("Notion Token", CheckTokensDB(current_user, "NToken"))
    tpass = "False";
    if(getDB(current_user, "temppass")):
        tpass = "True"
    if(getDB(current_user, "UseTToken")):
        print("use todist token")
        return jsonify({"User": getDB(current_user, "name"), "CToken": CheckTokensDB(current_user, "CToken"), "TToken": CheckTokensDB(current_user, "TToken"), "Temppass": tpass}), 200
    else:
        print("use notion token")
        both_valid = CheckTokensDB(current_user, "NToken") and CheckTokensDB(current_user, "NDatabase")
        return jsonify({"User": getDB(current_user, "name"), "CToken": CheckTokensDB(current_user, "CToken"), "NToken": both_valid, "Temppass": tpass}), 200
        

@app.route('/api/canvas-api-link', methods=['POST'])
@jwt_required()
def routeCanvasAPI():
     current_user = get_jwt_identity()
     data = request.json
     university = data.get("University")
     encryptedCToken = data.get('CToken')
     if validCToken(decrypt(encryptedCToken), university, current_user) == 200: 
        return jsonify({"message": "Successfully Linked Canvas Account"}), 200
     else:
        return jsonify({'error': 'Invalid Token'}), 401

@app.route('/api/todist-api-link', methods=['GET'])
def routeTodistAPI():
    token = request.args.get('code')
    state = request.args.get('state')

    cookie_state = request.cookies.get("oauth_state")
    email = decrypt(request.cookies.get("user"))

    if not token or not state:
        return redirect("https://localhost:5173/dashboard?status=400")
    if state != cookie_state:
        return redirect("https://localhost:5173/dashboard?status=400")
    
    token_response = validTToken(token, email)
    if token_response.get("error") or token_response == 400:
        errorresponse = make_response(redirect("https://localhost:5173/dashboard?status=400"))
        errorresponse.delete_cookie('oauth_state')  # Delete the cookie
        return errorresponse
    
    response = make_response(redirect("https://localhost:5173/dashboard?status=200"))
    response.delete_cookie('oauth_state')  # Delete the cookie
    return response

@app.route('/api/notion-api-link', methods=['GET'])
def routeNotionAPI():
    token = request.args.get('code')
    state = request.args.get('state')  # Optional: Verify state parameter if used

    cookie_state = request.cookies.get("oauth_state")
    email = decrypt(request.cookies.get("user"))

    if not token or not state:
        return redirect("https://localhost:5173/dashboard?status=400")
    
    if state != cookie_state:
        return redirect("https://localhost:5173/dashboard?status=400")

    # Step 2: Exchange the authorization code for an access token
    token_response = validNToken(token, email)
    if token_response == 400:
        errorresponse = make_response(redirect("https://localhost:5173/dashboard?status=400"))
        errorresponse.delete_cookie('oauth_state')  # Delete the cookie
        return errorresponse
    
    database_response = validNDB(decrypt(getDB(email, "NToken")), email)

    if database_response == 101:
        errorresponse = make_response(redirect("https://localhost:5173/dashboard?status=101"))
        errorresponse.delete_cookie('oauth_state')  # Delete the cookie
        return errorresponse
    
    response = make_response(redirect("https://localhost:5173/dashboard?status=200"))
    response.delete_cookie('oauth_state')  # Delete the cookie
    return response

@app.route('/api/settings', methods=['POST'])
@jwt_required()
def routeSettings():
    current_user = get_jwt_identity()
    data = request.json
    whichapi = decrypt(data.get("api"))
    if updateSettings(current_user, whichapi) == 200:
        return jsonify({"message": f"Successfully Updated API to {whichapi.capitalize()}"}), 200
    else:
        return jsonify({'error': 'Not Able To Update Settings'}), 401

@app.route('/api/unlink', methods=['POST'])
@jwt_required()
def routeUnlink():
    current_user = get_jwt_identity()
    data = request.json
    service = data.get("service") # Expecting "Canvas", "Todoist", or "Notion"
    
    if unlinkDB(current_user, service) == 200:
        return jsonify({"message": f"Successfully Unlinked {service}"}), 200
    else:
        return jsonify({'error': f'Failed to unlink {service}'}), 400

@app.route('/api/sync', methods=['GET'])
@jwt_required()
def routeSync():
    current_user = get_jwt_identity()
    
    # Check for sync cooldown
    allowed, remaining = can_sync(current_user)
    if not allowed:
        return jsonify({
            'error': 'Sync is cooling down',
            'remaining': remaining,
            'message': f'Please wait {remaining} seconds before syncing again.'
        }), 429
    whichT = getDB(current_user, "UseTToken")
    url = getDB(current_user, "url")
    
    try:
        raw_ctoken = getDB(current_user, "CToken")
        if not raw_ctoken:
            return jsonify({'error': 'Canvas token not found. Please link your Canvas account.'}), 400
        CToken = decrypt(raw_ctoken)
    except Exception as e:
        print(f"Error decrypting CToken: {e}")
        return jsonify({'error': 'Failed to decrypt Canvas token. Please re-link your Canvas account.'}), 500

    response = None
    if(whichT == True):
        try:
            raw_ttoken = getDB(current_user, "TToken")
            if not raw_ttoken:
                return jsonify({'error': 'Todoist token not found. Please link your Todoist account.'}), 400
            TToken = decrypt(raw_ttoken)
            stored_timezone = getDB(current_user, "timezone")
            response = sync_CanvasTodist(CToken, TToken, url, stored_timezone)
        except Exception as e:
            print(f"Error decrypting TToken: {e}")
            return jsonify({'error': 'Failed to decrypt Todoist token. Please re-link your Todoist account.'}), 500
    else:
        try:
            raw_ntoken = getDB(current_user, "NToken")
            raw_ndb = getDB(current_user, "NDatabase")
            if not raw_ntoken or not raw_ndb:
                return jsonify({'error': 'Notion credentials incomplete. Please re-link Notion.'}), 400
            
            NToken = decrypt(raw_ntoken)
            NDatabase = decrypt(raw_ndb)
            Ntimezone = getDB(current_user, "timezone")
            response = sync_CanvasNotion(CToken, NToken, NDatabase, Ntimezone , url)
        except Exception as e:
            print(f"Error decrypting Notion credentials: {e}")
            return jsonify({'error': 'Failed to decrypt Notion credentials. Please re-link Notion.'}), 500
            
    # Log the sync event and send email if successful
    if response and isinstance(response, dict):
        # Record sync timestamp
        update_sync_time(current_user)
        
        service_name = "Todoist" if whichT else "Notion"
        added = response.get("Added", "0")
        updated = response.get("Updated", "0")
        new_assignments = response.get("newDB", [])
        updated_assignments = response.get("updateDB", [])
        
        addSyncLog(current_user, added, updated, service_name)
        
        # Send sync completion email asynchronously
        thread = threading.Thread(
            target=send_sync_email,
            args=(current_user, added, updated, new_assignments, updated_assignments, service_name)
        )
        thread.daemon = True
        thread.start()
        
        # Strip internal data from frontend response
        frontend_response = {"Added": added, "Updated": updated}
        return jsonify(frontend_response), 200

    return jsonify({'error': 'Sync failed to produce a response'}), 500

@app.route('/api/sync-history', methods=['GET'])
@jwt_required()
def routeSyncHistory():
    current_user = get_jwt_identity()
    history = getDB(current_user, "sync_history")
    if history is None:
        history = []
    return jsonify(history), 200

@app.route('/api/schedule', methods=['GET'])
@jwt_required()
def routeGetSchedule():
    current_user = get_jwt_identity()
    schedule_info = get_schedule(current_user)
    return jsonify(schedule_info), 200

@app.route('/api/schedule', methods=['POST'])
@jwt_required()
def routeSetSchedule():
    current_user = get_jwt_identity()
    data = request.json
    enabled = data.get("enabled", False)
    interval = data.get("interval")  # Hours: 4, 8, or 12
    
    if enabled:
        if not interval or interval not in [24, 72, 168]:
            return jsonify({"error": "Invalid interval. Choose 1 day, 3 days, or 1 week."}), 400
        
        success = schedule_sync(current_user, interval)
        if success:
            logger.info(f"Auto-sync enabled for {current_user} every {interval}h")
            return jsonify({"message": f"Auto-sync enabled every {interval} hours"}), 200
        else:
            return jsonify({"error": "Failed to enable auto-sync"}), 500
    else:
        remove_schedule(current_user)
        logger.info(f"Auto-sync disabled for {current_user}")
        return jsonify({"message": "Auto-sync disabled"}), 200


if __name__ == "__main__":
    app.run(debug=True, ssl_context=('./src/localhost+2.pem', './src/localhost+2-key.pem'),port=5000)  # Run the Flask app on port 5000
