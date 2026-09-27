from fastapi import FastAPI

app = FastAPI(title="FinTech Intelligence API")

@app.get("/")
async def root():
    return {"message": "Welcome to the Enterprise FinTech Intelligence API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
