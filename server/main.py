from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
  return {'학식모지' : 'Server'}