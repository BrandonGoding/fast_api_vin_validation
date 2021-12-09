import fastapi
import uvicorn
import databases
import sqlalchemy
from pydantic import BaseModel
from decouple import config
from starlette.middleware.cors import CORSMiddleware as CORSMiddleware


class VinNumber(BaseModel):
    vin_number: str


class VinResponse(BaseModel):
    exists: bool


DATABASE_URL = f"mysql+pymysql://{config('MYSQL_USER')}:{config('MYSQL_PASSWORD')}@{config('MYSQL_HOST')}/{config('MYSQL_DB')}"

database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()

vin_numbers = sqlalchemy.Table(
    "vinNumbers",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("vin_number", sqlalchemy.String(100), index=True, unique=True),
)


engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)


app = fastapi.FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/")
async def hello_world():
    return {"Hello": "World"}


@app.post("/", response_model=VinResponse)
async def validate_vin(vin_number: VinNumber):
    query = f"SELECT * FROM vinNumbers WHERE vin_number = :vin_number"
    result = await database.fetch_one(
        query=query, values={"vin_number": vin_number.vin_number}
    )
    if result:
        return {"exists": True}
    return {"exists": False}


if __name__ == "__main__":
    uvicorn.run(app, port=8000, host="0.0.0.0")
