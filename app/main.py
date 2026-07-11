from fastapi import FastAPI, UploadFile, File
from app.services.ocr import extract_text
import shutil
import os

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def root():
    return {"message": "CAFLOW OCR Backend is running!"}

@app.post("/ocr")
async def ocr(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = extract_text(file_path)

    return {
        "filename": file.filename,
        "text": text
    }