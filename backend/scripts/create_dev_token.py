from __future__ import annotations

import argparse

from app.auth import VALID_ROLES, create_access_token
from app.database import SessionLocal, init_database
from app.models import User


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a local FoodLink JWT")
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--role", type=int, choices=sorted(VALID_ROLES), required=True)
    parser.add_argument("--minutes", type=int, default=120)
    args = parser.parse_args()

    init_database()
    with SessionLocal() as db:
        user = db.get(User, args.user_id)
        if user is None:
            parser.error("user does not exist; run python -m scripts.seed_demo first")
        if user.role != args.role:
            parser.error("role does not match the database user")
        if user.status != 1:
            parser.error("user is disabled")

    print(create_access_token(args.user_id, args.role, args.minutes))


if __name__ == "__main__":
    main()
