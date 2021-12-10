import datetime
from typing import Optional
import fastapi
import uvicorn
import databases
import sqlalchemy
from pydantic import BaseModel, EmailStr
from decouple import config
from sqlalchemy import func
from starlette.middleware.cors import CORSMiddleware as CORSMiddleware


class VehicleIdentificationNumber(BaseModel):
    vehicle_identification_number: str


class VinResponse(BaseModel):
    exists: bool


class TrailerOwner(BaseModel):
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    mobile_phone_number: Optional[str]


class WarrantyRegistration(BaseModel):
    owner: TrailerOwner
    vehicle_identification_number: str
    purchase_date: datetime.date



DATABASE_URL = f"mysql+pymysql://{config('MYSQL_USER')}:{config('MYSQL_PASSWORD')}@{config('MYSQL_HOST')}/{config('MYSQL_DB')}"

database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()

vin_numbers = sqlalchemy.Table(
    "vehicle_identification_numbers",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("vehicle_identification_number", sqlalchemy.String(100), index=True, unique=True),
)

trailer_owners = sqlalchemy.Table(
    "trailer_owners",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("email", sqlalchemy.String(100), unique=True),
    sqlalchemy.Column("first_name", sqlalchemy.String(65), nullable=True),
    sqlalchemy.Column("last_name", sqlalchemy.String(65), nullable=True),
    sqlalchemy.Column("address", sqlalchemy.String(65), nullable=True),
    sqlalchemy.Column("city", sqlalchemy.String(65), nullable=True),
    sqlalchemy.Column("state", sqlalchemy.String(65), nullable=True),
    sqlalchemy.Column("country", sqlalchemy.String(65), nullable=True),
    sqlalchemy.Column("mobile_phone_number", sqlalchemy.String(65), nullable=True),
)


warranty_registration = sqlalchemy.Table(
    "warranty_registrations",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("vin_id", sqlalchemy.ForeignKey('vehicle_identification_numbers.id'), nullable=False, index=True),
    sqlalchemy.Column("trailer_owner_id", sqlalchemy.ForeignKey('trailer_owners.id'), nullable=False, index=True),
    sqlalchemy.Column("purchase_date", sqlalchemy.Date, nullable=False),
    sqlalchemy.Column("date_registered", sqlalchemy.DateTime, server_default=func.now())
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
async def validate_vin(vin: VehicleIdentificationNumber):
    query = f"SELECT * FROM vehicleIdentificationNumbers WHERE vehicle_identification_number = :vin"
    result = await database.fetch_one(
        query=query, values={"vin": vin.vehicle_identification_number}
    )
    if result:
        return {"exists": True}
    return {"exists": False}


if __name__ == "__main__":
    uvicorn.run(app, port=8000, host="0.0.0.0")
