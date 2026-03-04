from app.db.session import SessionLocal
from app.services.api_key_service import create_api_key


def main() -> None:
    db = SessionLocal()
    try:
        tenant_id = input("tenant_id: ").strip()
        name = input("name [manual]: ").strip() or "manual"
        key, raw = create_api_key(db, tenant_id=tenant_id, name=name)
        print("created id:", key.id)
        print("api key:", raw)
    finally:
        db.close()


if __name__ == "__main__":
    main()
