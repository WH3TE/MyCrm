from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# --- 1. 数据库配置 (SQLite + SQLAlchemy) ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./customers.db"

# create_engine: 创建数据库引擎
# check_same_thread=False 是 SQLite 必须的配置，允许在不同线程中使用连接
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# SessionLocal: 数据库会话工厂，用于创建会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base: 所有数据库模型的基类
Base = declarative_base()

# --- 2. 定义数据库模型 (ORM Model) ---
class CustomerDB(Base):
    __tablename__ = "customers"  # 数据库表名

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    company = Column(String)
    position = Column(String)
    last_contact = Column(String)

# 创建所有表 (如果不存在的话)
Base.metadata.create_all(bind=engine)

# --- 3. 定义 Pydantic 数据模型 (用于接口请求/响应) ---
class CustomerCreate(BaseModel):
    name: str
    company: str
    position: str
    last_contact: str

class Customer(CustomerCreate):
    id: int

    # ConfigDict (Pydantic v2) 或 class Config (Pydantic v1)
    # from_attributes = True 让 Pydantic 能读取 ORM 对象
    class Config:
        from_attributes = True

# --- 4. FastAPI 应用 ---
app = FastAPI()

# 依赖项: 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 5. 接口实现 ---

# GET /customers (查看所有客户)
@app.get("/customers", response_model=List[Customer])
def get_customers(db: Session = Depends(get_db)):
    # 使用 SQLAlchemy 查询所有客户
    customers = db.query(CustomerDB).all()
    return customers

# POST /customers (添加客户)
@app.post("/customers", response_model=Customer)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    # 创建 ORM 对象
    db_customer = CustomerDB(
        name=customer.name,
        company=customer.company,
        position=customer.position,
        last_contact=customer.last_contact
    )
    # 添加到会话并提交
    db.add(db_customer)
    db.commit()
    # 刷新对象以获取生成的 ID
    db.refresh(db_customer)
    return db_customer

# PUT /customers/{id} (修改客户)
@app.put("/customers/{customer_id}", response_model=Customer)
def update_customer(customer_id: int, updated_customer: CustomerCreate, db: Session = Depends(get_db)):
    # 查询指定 ID 的客户
    db_customer = db.query(CustomerDB).filter(CustomerDB.id == customer_id).first()
    
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # 更新字段
    db_customer.name = updated_customer.name
    db_customer.company = updated_customer.company
    db_customer.position = updated_customer.position
    db_customer.last_contact = updated_customer.last_contact
    
    # 提交更改
    db.commit()
    db.refresh(db_customer)
    return db_customer

if __name__ == "__main__":
    import uvicorn
    # 启动服务
    uvicorn.run(app, host="127.0.0.1", port=8000)
