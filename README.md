### Requirements
- Python 3.8+
- Pip packages: `fastapi`, `uvicorn`, `pandas`, `openpyxl`

### Install Dependencies
- pip install -r requirements.txt

### To run on the local host
- unicorn main:app --reload

## To run in the network
- uvicorn main:app --host 0.0.0.0 --port 8000 --reload
- http://<your-ip>:8000
