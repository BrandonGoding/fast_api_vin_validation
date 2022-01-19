from typing import Optional, List

import fastapi
import pymysql.err
import uvicorn
import databases
import sqlalchemy
from fastapi import HTTPException
from pydantic import BaseModel
from decouple import config
from starlette.middleware.cors import CORSMiddleware as CORSMiddleware


class VehicleIdentificationNumber(BaseModel):
    vehicle_identification_number: str


class VehicleIdentificationNumberWithID(VehicleIdentificationNumber):
    id: int


class VinResponse(BaseModel):
    exists: bool


class VinInsertResponse(BaseModel):
    inserted_vins: List[VehicleIdentificationNumberWithID]
    failed_inserts: List[VehicleIdentificationNumber]


DATABASE_URL = f"mysql+pymysql://{config('MYSQL_USER')}:{config('MYSQL_PASSWORD')}@{config('MYSQL_HOST')}/{config('MYSQL_DB')}"

database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()

vin_table = sqlalchemy.Table(
    "vehicleIdentificationNumbers",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column(
        "vehicle_identification_number", sqlalchemy.String(100), index=True, unique=True
    ),
)


engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)


app = fastapi.FastAPI()


app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/", include_in_schema=False)  # RETURNS 200 RESPONSE FOR AWS LOAD BALANCER STATUS CHECKER
async def heart_beat():
    return {"Heart Beat": "Ba Bump... Ba Bump... Ba Bump"}


@app.post("/", response_model=VinResponse, tags=["Validation"])
async def validate_vehicle_identification_number(vin: VehicleIdentificationNumber):
    query = f"SELECT * FROM vehicleIdentificationNumbers WHERE vehicle_identification_number = :vin"
    result = await database.fetch_one(
        query=query, values={"vin": vin.vehicle_identification_number}
    )
    if result:
        return {"exists": True}
    return {"exists": False}


@app.post("/insert", response_model=VehicleIdentificationNumberWithID, tags=["CRUD"])
async def insert_vehicle_identification_number(vin: VehicleIdentificationNumber):
    try:
        query = vin_table.insert()
        result = await database.execute(
            query=query,
            values={"vehicle_identification_number": vin.vehicle_identification_number},
        )
    except pymysql.err.IntegrityError:
        return HTTPException(
            status_code=418, detail="Bitch I'm a Teapot!, GET YOUR OWN DAMN COFFEE!"
        )
    return {**vin.dict(), "id": result}


@app.post("/insert/multiple", response_model=VinInsertResponse, tags=["CRUD"])
async def insert_multiple_vehicle_identification_numbers(
    vins: List[VehicleIdentificationNumber],
):
    results_list = {"inserted_vins": [], "failed_insert": []}

    for vin_number in vins:
        try:
            query = vin_table.insert()
            result = await database.execute(
                query=query,
                values={
                    "vehicle_identification_number": vin_number.vehicle_identification_number
                },
            )
            results_list.get("inserted_vins").append(
                {**vin_number.dict(), "id": result}
            )
        except pymysql.err.IntegrityError:
            results_list.get("failed_inserts").append(vin_number)
    return results_list


@app.delete("/delete", tags=['CRUD'], status_code=204, response_model=VehicleIdentificationNumber)
async def remove_vehicle_identification_number(vin: VehicleIdentificationNumberWithID):
    query = vin_table.select().filter(vin_table.c.id == vin.id, vin_table.c.vehicle_identification_number == vin.vehicle_identification_number)
    vin_to_delete = await database.fetch_one(query=query)
    if vin_to_delete is None:
        raise HTTPException(status_code=404)
    query = vin_table.delete().where(vin_table.c.id == vin.id, vin_table.c.vehicle_identification_number == vin.vehicle_identification_number)
    await database.execute(query=query)
    return {"vehicle_identification_number": vin.id}


if __name__ == "__main__":
    uvicorn.run(app, port=8000, host="0.0.0.0")
