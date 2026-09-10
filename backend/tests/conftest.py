from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Callable, Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.auth import create_access_token
from app.database import Base, build_engine, get_db
from app.main import create_app
from app.models import Merchant, Product, User
from app.timeutils import now_shanghai_naive


def _seed_database(db: Session) -> None:
    users = [
        User(id=1, role=1, login_name="student-1", password="x", school="测试大学", student_id="S001", name="学生甲", phone="13800000001", status=1),
        User(id=2, role=2, login_name="merchant-1", password="x", name="商家甲账号", phone="13800000002", status=1),
        User(id=3, role=2, login_name="merchant-2", password="x", name="商家乙账号", phone="13800000003", status=1),
        User(id=4, role=3, login_name="admin", password="x", name="管理员", phone="13800000004", status=1),
        User(id=5, role=1, login_name="student-2", password="x", school="测试大学", student_id="S002", name="学生乙", phone="13800000005", status=1),
        User(id=6, role=1, login_name="disabled", password="x", school="测试大学", student_id="S003", name="停用学生", phone="13800000006", status=0),
    ]
    db.add_all(users)
    db.flush()

    merchants = [
        Merchant(id=1, user_id=2, shop_name="甲店", location="南门", lat=Decimal("30.100000"), lng=Decimal("120.100000"), audit_status=1),
        Merchant(id=2, user_id=3, shop_name="乙店", location="北门", lat=Decimal("30.200000"), lng=Decimal("120.200000"), audit_status=1),
    ]
    db.add_all(merchants)
    db.flush()

    now = now_shanghai_naive()
    products = [
        Product(id=1, merchant_id=1, title="测试套餐", image="image-1", original_price=Decimal("28.00"), discount_price=Decimal("12.00"), quantity=3, expire_time=now + timedelta(days=1), location="南门一号", lat=Decimal("30.100000"), lng=Decimal("120.100000"), status=1),
        Product(id=2, merchant_id=2, title="其他店商品", image="", original_price=Decimal("20.00"), discount_price=Decimal("9.90"), quantity=5, expire_time=now + timedelta(days=1), location="北门二号", lat=Decimal("30.200000"), lng=Decimal("120.200000"), status=1),
        Product(id=3, merchant_id=1, title="已过期商品", image="", original_price=Decimal("10.00"), discount_price=Decimal("5.00"), quantity=2, expire_time=now - timedelta(minutes=1), location="南门一号", lat=Decimal("30.100000"), lng=Decimal("120.100000"), status=1),
        Product(id=4, merchant_id=1, title="已下架商品", image="", original_price=Decimal("10.00"), discount_price=Decimal("5.00"), quantity=2, expire_time=now + timedelta(days=1), location="南门一号", lat=Decimal("30.100000"), lng=Decimal("120.100000"), status=0),
    ]
    db.add_all(products)
    db.commit()


@pytest.fixture
def session_factory():
    test_engine = build_engine("sqlite://")
    Base.metadata.create_all(bind=test_engine)
    factory = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)
    with factory() as db:
        _seed_database(db)
    try:
        yield factory
    finally:
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


@pytest.fixture
def client(session_factory) -> TestClient:
    application = create_app(initialize_database=False)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    application.dependency_overrides[get_db] = override_get_db
    with TestClient(application) as test_client:
        yield test_client


@pytest.fixture
def auth_headers() -> Callable[[int, int], Dict[str, str]]:
    def make_headers(user_id: int, role: int) -> Dict[str, str]:
        token = create_access_token(user_id=user_id, role=role)
        return {"Authorization": "Bearer {}".format(token)}

    return make_headers
