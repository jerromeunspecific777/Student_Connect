from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.serialization import load_pem_public_key
import os
import base64
import bcrypt
import secrets
import string
import yagmail
import pytz
import datetime
from dotenv import load_dotenv
from pymongo import errors
from src.database import db
from canvasapi import Canvas
from canvasapi.exceptions import CanvasException
import requests
import time
from src.logger import get_logger

logger = get_logger(__name__)

def checkEnv(value):
    load_dotenv()

    exists = os.getenv(value)

    if exists is not None:
        return True
    else:
        return False
    
def returnJWTSecret():
    load_dotenv()

    code = base64.b64decode(os.getenv("JWT_SECRET_KEY"))
    return code

def encrypt(plaintext):
    load_dotenv()

    # Load the public key
    with open("./src/public_key.pem", "rb") as key_file:
        public_key = load_pem_public_key(key_file.read())

    # Convert plaintext to bytes
    plaintext_data = plaintext.encode("utf-8")

    # Encrypt the plaintext
    encrypted_data = public_key.encrypt(
        plaintext_data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Return the encrypted data as a hex string
    return encrypted_data.hex()

def decrypt(encrypted):
    load_dotenv()

    private_pass = base64.b64decode(os.getenv("PRIVATE_PASS"))

    with open("./src/private_key.pem", "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=private_pass,
    )
        
    encrypted_data = bytes.fromhex(encrypted)

    decrypted_data = private_key.decrypt(
        encrypted_data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    decrypted_text = decrypted_data.decode("utf-8")
    
    return decrypted_text

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

def check_password(stored_hash: bytes, entered_password: str) -> bool:
    return bcrypt.checkpw(entered_password.encode('utf-8'), stored_hash)

def registerUser(name, email):
    users = db['user']

    query = {"email": email}

    if(users.find_one(query)):
        return 409

    new_user_data = {
        "name": name,
        "email": email,
        "code": "",
        "temppass": False,
        "CToken": "",
        "url": "",
        "TToken": "",
        "NToken": "",
        "NDatabase": "",
        "UseTToken": True,
        "timezone": "",
        "code_generated_at": None,
        "auto_sync": False,
        "sync_interval": None,
    }

    try:
        users.insert_one(new_user_data)
        return 200
    except errors.PyMongoError:
        return 401

def unlinkDB(email, service):
    try:
        if service == "Canvas":
            setDB(email, "CToken", "")
            setDB(email, "url", "")
        elif service == "Todoist":
            setDB(email, "TToken", "")
        elif service == "Notion":
            setDB(email, "NToken", "")
            setDB(email, "NDatabase", "")
        else:
            return 400
        return 200
    except errors.PyMongoError:
        return 401

def addSyncLog(email, added, updated, service):
    try:
        users = db['user']
        log_entry = {
            "timestamp": datetime.datetime.now(pytz.UTC).isoformat(),
            "added": added,
            "updated": updated,
            "service": service
        }
        
        # Pull from end and push to front, keeping only last 15 items
        users.update_one(
            {"email": email},
            {
                "$push": {
                    "sync_history": {
                        "$each": [log_entry],
                        "$position": 0,
                        "$slice": 2
                    }
                }
            }
        )
        return 200
    except Exception as e:
        logger.error(f"Error adding sync log: {e}")
        return 500

def can_sync(email):
    """
    Checks if the user is allowed to sync based on a 60-second cooldown.
    Returns (True, None) if allowed, (False, remaining_seconds) if not.
    """
    users = db['user']
    user = users.find_one({"email": email}, {"last_synced": 1})
    
    if not user or "last_synced" not in user:
        return True, 0
    
    last_synced = user["last_synced"]
    if last_synced.tzinfo is None:
        last_synced = last_synced.replace(tzinfo=datetime.timezone.utc)
        
    now = datetime.datetime.now(datetime.timezone.utc)
    elapsed = (now - last_synced).total_seconds()
    
    cooldown = 60
    if elapsed < cooldown:
        return False, int(cooldown - elapsed)
    
    return True, 0

def update_sync_time(email):
    """Updates the last_synced timestamp for the user."""
    users = db['user']
    now = datetime.datetime.now(datetime.timezone.utc)
    users.update_one({"email": email}, {"$set": {"last_synced": now}})

def genCode(email):
    users = db['user']

    query = {"email": email}

    user = users.find_one(query)

    if user:
       code = ''.join(secrets.choice(string.digits) for _ in range(6))
       print(code)
       
       load_dotenv()
       # Use environment variables if they exist, otherwise fallback to default
       sc_email = os.getenv("EMAIL")
       sc_pass = os.getenv("EMAIL_PASS")
       
       # Use a professional HTML body
       body = f"""
       <div style="font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 480px; margin: 0 auto; padding: 40px; border: 1px solid #f0f0f0; border-radius: 20px; color: #1a1a1a;">
           <div style="text-align: center; margin-bottom: 30px;">
               <h1 style="margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -1px; color: #000;">Student Connect</h1>
           </div>
           
           <div style="text-align: center; margin-bottom: 30px;">
               <h2 style="margin: 0 0 10px; font-size: 18px; font-weight: 600;">Verification Code</h2>
               <p style="margin: 0; font-size: 14px; color: #444;">Please use the following code to complete your login.</p>
           </div>
           
           <div style="text-align: center; margin-bottom: 30px;">
               <div style="display: inline-block; padding: 15px 30px; background-color: #000; border-radius: 12px; color: #fff; font-size: 32px; font-weight: 700; letter-spacing: 5px; box-shadow: 0 10px 20px rgba(0,0,0,0.1);">
                   {code}
               </div>
           </div>
           
           <p style="font-size: 13px; color: #888; text-align: center; line-height: 1.5;">
               If you didn't request this code, you can safely ignore this email. This code will expire soon.
           </p>
           
           <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
           
           <div style="text-align: center; font-size: 12px; color: #aaa;">
               <p style="margin: 0;">&copy; {datetime.datetime.now().year} Student Connect. All rights reserved.</p>
           </div>
       </div>
       """
       
       yag = yagmail.SMTP(user=sc_email, password=sc_pass)
       yag.send(to=email, subject=f"Your Student Connect Verification Code: {code}", contents=body)
       now = datetime.datetime.now(datetime.timezone.utc)
       update = {"$set": {"code": encrypt(code), "code_generated_at": now}}
       users.update_one(query, update)
       return 200
    else: 
       return 401
 # reminder to change the email address in the genCode function
def validLogin(email, code, timezone):
    users = db['user']

    query = {"email": email}

    user = users.find_one(query)

    if user:
       usercode = user.get('code')
       if not usercode:
           return 401
       # Check code (decrypting existing code stored encrypted? Or comparing hashes?)
       # Step 475 set: update = {"$set": {"code": encrypt(code)}}
       # So code is stored encrypted with public key.
       # validLogin receives decrypted code from user.
       # Wait, `encrypt` uses public key. `decrypt` uses private key.
       # Use `check_password`? No, that's for bcrypt hashes.
       # `encrypt(code)` -> hex string.
       # To check, we must decrypt the STORED code and compare with INPUT code?
       # BUT `encrypt` uses random padding (OAEP), so `encrypt(code) != encrypt(code)`.
       # We must DECRYPT the stored code to compare.
       # `src/utils.py` has `decrypt(encrypted)`.
       
       # So: `decoded_stored_code = decrypt(usercode)`
       # `if decoded_stored_code == code:`
       
       # Step 475 implementation used: `if check_password(usercode, decrypt(code)):`
       # But `check_password` uses `bcrypt.checkpw`.
       # Did `genCode` store it as a HASH?
       # Step 475 `genCode`: `update = {"$set": {"code": encrypt(code)}}`
       # Use `encrypt` (RSA). NOT `hash_password`.
       # So `check_password` (bcrypt) would FAIL vs RSA string.
       
       # If I use RSA to store it, I must decrypt it to verify.
       try:
           stored_code_plain = decrypt(usercode)
           code_at = user.get('code_generated_at')
           
           if code_at:
               # Ensure code_at is timezone-aware
               if code_at.tzinfo is None:
                   code_at = code_at.replace(tzinfo=datetime.timezone.utc)
               
               now = datetime.datetime.now(datetime.timezone.utc)
               diff = now - code_at
               if diff > datetime.timedelta(minutes=10):
                   print("Code Expired")
                   return 403
       except Exception as e:
           print(f"Login validation error: {e}")
           return 401
           
       if stored_code_plain == code:
           # Note: app.py passes `decrypt(encryptedTimezone)`. So `timezone` arg here IS decrypted.
           # Wait, app.py: `validLogin(decrypt(encryptedEmail), decrypt(encryptedCode), decrypt(encryptedTimezone))`
           # So `timezone` is plaintext here.
           # Storing directly? `update = {"$set": {"timezone": timezone}}`
           update = {"$set": {"timezone": timezone}}
           users.update_one(query, update)
           return 200
       else:
           return 401
    else: 
       return 401
    

def validCToken(token, university, email):
    university_urls = {
    "USF": "https://usflearn.instructure.com/",
    "UF": "https://ufl.instructure.com/",
    "UCF": "https://ucf.instructure.com/",
    "FSU": "https://fsu.instructure.com/"
    }

    url = university_urls.get(university)
    
    canvas = Canvas(url, token)

    try:
    # Get the current user's profile
        user = canvas.get_user("self")  # "self" refers to the authenticated user
        logger.info("API link and token are working!")
        logger.info(f"User Profile: {user.name}")
        users = db['user']

        query = {"email": email}

        update = {"$set": {"url": url, "CToken": encrypt(token)}}
   
        result = users.update_one(query, update)
        if result.matched_count > 0:
            logger.info("Successfully Set Notion Token")
            return 200
        else:
            logger.warning("User not found")
            return 400
    except CanvasException as e:
        logger.error(e)
        return e
    except Exception as e:
        logger.error(e)
        return e

def validTToken(token, email):
    load_dotenv()
    client_id = os.getenv("TODOIST_CLIENT_ID")
    client_secret = os.getenv("TODOIST_CLIENT_SECRET")
    token_url = "https://todoist.com/oauth/access_token"
    token_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': token,
        "redirect_uri": "https://localhost:5000/api/todist-api-link"
    }

    try:
        response = requests.post(token_url, data=token_data)
    except requests.RequestException as e:
        return {"error": f"Request failed: {e}"}
    
    if response.status_code != 200:
        return {"error": response.json().get("error"), "details": response.json()}

    users = db['user']

    query = {"email": email}

    update = {"$set": {"TToken": encrypt(response.json().get('access_token'))}}
   
    result = users.update_one(query, update)

    if result.matched_count > 0:
        logger.info("Successfully Set Notion Token")
        return response.json()
    else:
        logger.warning("User not found")
        return 400

def validNDB(access_token, email):
    headers = {
    "Authorization": f"Bearer {access_token}",
    "Notion-Version": "2022-06-28"
    }
    url = "https://api.notion.com/v1/search"
    payload = {
    "filter": {
        "property": "object",
        "value": "database"
        }
    }
    users = db['user']
    query = {"email": email}
    database_id = None
    try:
        time.sleep(3)
        response = requests.post(url, json=payload, headers=headers)
    except requests.RequestException as e:
        return {"error": f"Request failed: {e}"}
    
    data = response.json()
    for result in data["results"]:
        # Log titles only if needed for debugging Notion structure
        # logger.debug(result['title'][0]['plain_text'])
        if result['title'][0]['plain_text'] == "Student Connect Notion Template":
            database_id = result['id'].replace("-", "")
    
    if database_id == None:
        return 101

    update = {"$set": {"NDatabase": encrypt(database_id)}}
    result = users.update_one(query, update)

    if result.matched_count > 0:
        return 200
    else:
        print("User not found")
        return 101
    

def validNToken(token, email):
    load_dotenv()
    token_url = "https://api.notion.com/v1/oauth/token"
    headers = {"Content-Type": "application/json"}
    payload = {
        "grant_type": "authorization_code",
        "code": token,
        "redirect_uri": "https://localhost:5000/api/notion-api-link",
    }

    client_id = os.getenv("NOTION_CLIENT_ID")
    client_secret = os.getenv("NOTION_CLIENT_SECRET")

    try:
        response = requests.post(token_url, auth=(client_id, client_secret), json=payload, headers=headers)
    except requests.RequestException as e:
        return 400
    
    if response.status_code != 200:
        return 400

    users = db['user']

    query = {"email": email}

    access_token = response.json().get('access_token')

    update = {"$set": {"NToken": encrypt(access_token)}}
   
    result = users.update_one(query, update)

    if result.matched_count > 0:
        logger.info("Successfully Set Notion Token")
        return response.json()
    else:
        logger.warning("User not found")
        return 400


def CheckTokensDB(email, field):
    users = db['user']

    query = {"email": email, field: {"$ne": ""}}

    document = users.find_one(query)

    if document:
        return "True"
    else: 
        return "False"

def getDB(email, field):
    users = db['user']

    query = {"email": email}

    document = users.find_one(query)

    if document:
        return document.get(field)
    else:
        return "None"
    
def setDB(email, field, newvalue):
    users = db['user']

    query = {"email": email}

    update = {"$set": {field: newvalue}}

    users.update_one(query, update)

def updateSettings(email, api):
    try:
        if api == "todoist":
            setDB(email, "UseTToken", True)
            return 200
        elif api == "notion":
            setDB(email, "UseTToken", False)
            return 200
    except errors.PyMongoError:
        return 401