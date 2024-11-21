import os
from typing import Any


from fastapi import FastAPI, Depends
from datetime import date


from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from firebase_admin import credentials, messaging
from pydantic import BaseModel
from fastapi import Request
import simplejson
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

import firebase_admin


uri = "mongodb+srv://lubowie118:lbw811010@cluster0.jcya7.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(uri, server_api=ServerApi('1'))
db = client["chatdata"]
collection_cr = db["chatrooms"]
collection_msg = db["messages"]
collection_tk = db["tokens"]
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/get_chatrooms/")
async def get_chatrooms(request: Request):
    query_params = request.query_params
    if len(query_params)>0:
        data = {"status": "ERROR", "message": "Excess Parameters Received!"}
        return JSONResponse(content=jsonable_encoder(data))
    chatroom_list = {"data": [], "status": "OK"}
    for x in collection_cr.find():
        data = {"id": x["id"], "name": x["name"]}
        chatroom_list["data"].append(data)
    return JSONResponse(content=jsonable_encoder(chatroom_list))

@app.get("/get_messages/")
async def get_messages(request: Request, chatroom_id: int = -1, status_code=200):
    query_params = request.query_params
    extra_params = set(query_params.keys()) - {"chatroom_id"}
    if len(extra_params) > 0:
        data = {"status": "ERROR", "message": "Excess Parameters Received!"}
        return JSONResponse(content=jsonable_encoder(data))
    print(chatroom_id)
    if chatroom_id == -1:
        data = {"status": "ERROR", "message": "Insufficient Parameters!"}
        return JSONResponse(content=jsonable_encoder(data))
    crid = False
    for x in collection_cr.find():
        if x["id"] == chatroom_id:
            crid = True
            break
    if not crid:
        data = {"status": "ERROR", "message": "Chatroom Id Not Found!"}
        return JSONResponse(content=jsonable_encoder(data))
    data = {"data": {"messages": []}, "status": "OK"}
    for x in collection_msg.find():
        if x["chatroom_id"] == chatroom_id:
            message = {"message": x["message"], "name": x["name"], "message_time": x["message_time"], "user_id": x["user_id"]}
            data["data"]["messages"].append(message)
    return JSONResponse(content=jsonable_encoder(data))

class MessageItem(BaseModel):
    message: str
    name: str
    message_time: str
    user_id: int
    chatroom_id: int

    def to_dict(self):
        return{
            "message": self.message,
            "name": self.name,
            "message_time": self.message_time,
            "user_id": self.user_id,
            "chatroom_id": self.chatroom_id
        }

@app.post("/send_message/")
async def get_messages(msg: MessageItem):
    print(msg)
    if(len(msg.name)>20):
        data = {"status": "ERROR", "message": "Name Is Too Long!"}
        return JSONResponse(content=jsonable_encoder(data))
    if (len(msg.message) > 200):
        data = {"status": "ERROR", "message": "Message Is Too Long!"}
        return JSONResponse(content=jsonable_encoder(data))
    for x in collection_cr.find():
        if(x["id"] == msg.chatroom_id):
            data = {"status": "OK", "messgae": "Message Sent!"}
            collection_msg.insert_one(msg.to_dict())
            token=""
            for y in collection_tk.find():
                if y["user_id"] == msg.user_id:
                    token = y["token"]
            title=x["name"]
            initialize_firebase()
            send_fcm_notification(token=token, title=title, body=msg.message)
            print(token, title, msg.message)
            return JSONResponse(content=jsonable_encoder(data))
    data = {"status": "ERROR", "message": "Chatroom Doesn't Exist!"}
    return JSONResponse(content=jsonable_encoder(data))

class TokenItem(BaseModel):
    user_id: int
    token: str

    def to_dict(self):
        return{
            "user_id":self.user_id,
            "token":self.token
        }

@app.post("/submit_push_token/")
async def submit_token(tk: TokenItem):
    print(tk)
    for x in collection_tk.find():
        if x["user_id"] == tk.user_id:
            data = {"status": "OK", "messgae": "Token Sent!"}
            query = {"user_id": tk.user_id}
            update = {"$set":{"token": tk.token}}
            collection_tk.find_one_and_replace(query, update)
            return JSONResponse(content=jsonable_encoder(data))
    collection_tk.insert_one(tk.to_dict())
    data = {"status": "OK", "messgae": "Token Sent!"}
    return JSONResponse(content=jsonable_encoder(data))


def initialize_firebase():
    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if not service_account_json:
            raise ValueError("Environment variable 'FIREBASE_SERVICE_ACCOUNT_JSON' is not set.")
    cred_dict = json.loads(service_account_json)    
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

def send_fcm_notification(token, title, body):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        token=token,
    )
    print(type(message))
    try:
        response = messaging.send(message)
        print(f"Successfully sent message:{response}")
    except Exception as e:
        print(f"Failed to send message:{e}")

