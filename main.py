import fastapi
import uvicorn
from pydantic import BaseModel

data = [
    {
        "vin_number": "SA4784",
    },
    {
        "vin_number": "V410Z8",
    },
    {
        "vin_number": "CZ1094",
    }
]


def search(vin):
    for v in data:
        if v['vin_number'] == vin:
            return v


class VinNumber(BaseModel):
    vin_number: str


app = fastapi.FastAPI()


@app.get("/")
def hello_world():
    return {}


@app.post("/")
def validate_vin(vin_number: VinNumber):
    if search(vin_number.vin_number):
        return True
    return False


if __name__ == '__main__':
    uvicorn.run(app, port=8080, host="0.0.0.0")
