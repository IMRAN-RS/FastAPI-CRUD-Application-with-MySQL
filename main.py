from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List

# FastAPI app initialization
app = FastAPI()

# Define the MySQL connection URL (with proper encoding for special characters in password)
SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://root:Password@127.0.0.1:3306/employee_db"

# Create SQLAlchemy engine to connect to MySQL
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_size=10, max_overflow=20)

# Create SQLAlchemy engine to connect to MySQL
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our models
Base = declarative_base()

# Define the SQLAlchemy ORM model for the "employees" table
class EmployeeDB(Base): 
    __tablename__ = "employees"    # Table name in MySQL

    id = Column(Integer, primary_key=True, index=True)        # Primary Key
    name = Column(String, index=True)                         # Employee name
    email = Column(String, unique=True, index=True)           # Unique email 
    department = Column(String)                               # Department name
    age = Column(Integer)                                     # Age
    salary = Column(Float)                                    # Salary

# Define the Pydantic schema (used for request/response validation)
class Employee(BaseModel):
    id: int
    name: str
    email: str
    department: str
    age: int
    salary: float

    class Config:
        orm_mode = True  # This tells Pydantic to treat the SQLAlchemy model as a dictionary

# Create tables in the database
Base.metadata.create_all(bind=engine)

# Dependency that returns a DB session (and ensures it's closed after request)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# CREATE operation: Add a new employee 
@app.post("/employees", response_model=Employee)
def create_employee(emp: Employee, db: Session = Depends(get_db)):
    db_emp = EmployeeDB(**emp.dict())    # Convert Pydantic model to ORM model
    db.add(db_emp)                       # Add new employee object to session
    db.commit()                          # Commit changes to the database
    db.refresh(db_emp)                   # Refresh instance with DB-generated fields (like auto IDs)
    return db_emp                        # Return the created employee


# READ operation: Get all employees
@app.get("/employees", response_model=List[Employee])
def get_all_employees(db: Session = Depends(get_db)):
    return db.query(EmployeeDB).all()

# READ operation: Get one employee by ID
@app.get("/employees/{emp_id}", response_model=Employee)
def get_employee(emp_id: int, db: Session = Depends(get_db)):
    db_emp = db.query(EmployeeDB).filter(EmployeeDB.id == emp_id).first()
    if db_emp is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_emp

# UPDATE - Update an employee by ID
@app.put("/employees/{emp_id}", response_model=Employee)
def update_employee(emp_id: int, emp: Employee, db: Session = Depends(get_db)):
    db_emp = db.query(EmployeeDB).filter(EmployeeDB.id == emp_id).first()
    if db_emp is None:
        raise HTTPException(status_code=404, detail="Employee not found")
     # Update the fields with values from the request
    for key, value in emp.dict().items():
        setattr(db_emp, key, value)
    
    db.commit()
    db.refresh(db_emp)
    return db_emp

# DELETE operation: Delete an employee by ID
@app.delete("/employees/{emp_id}")
def delete_employee(emp_id: int, db: Session = Depends(get_db)):
    db_emp = db.query(EmployeeDB).filter(EmployeeDB.id == emp_id).first()
    if db_emp is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    db.delete(db_emp)
    db.commit()
    return {"message": "Employee deleted successfully"}

