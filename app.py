from fastapi import FastAPI
from datetime import date
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from fastapi import Request
import simplejson

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World!"}

@app.get("/demo/")
async def get_demo(a:int = 0, b:int = 0, status_code = 200):
    sum = a+b
    data = {"sum": sum, "date": date.today()}
    return JSONResponse(content=jsonable_encoder(data))

class DemoItem(BaseModel):
    a: int
    b: int

@app.post("/demo/")
async def post_demo(item: DemoItem):
    print(item)
    if item.a + item.b == 10:
        data = {"status": "OK"}
        return JSONResponse(content=jsonable_encoder(data))
    data = {"status": "ERROR"}
    return JSONResponse(content=jsonable_encoder(data))