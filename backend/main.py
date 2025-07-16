from typing import Union
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Server is on!"}

@app.get("/health")
def check_server():
    return {"Status": "Ok"}
