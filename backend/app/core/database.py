import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.core.config import settings

logger = logging.getLogger("insightiq.database")

Base = declarative_base()

engine = None
SessionLocal = None
_db_status = {
    "connected": False,
    "dialect": None,
    "url": settings.DATABASE_URL,
    "message": "Database not initialized"
}


def init_db():
    global engine, SessionLocal, _db_status
    primary_url = settings.DATABASE_URL
    masked_url = primary_url
    if "@" in primary_url:
        # mask password for logging
        try:
            proto, rest = primary_url.split("://", 1)
            creds, host_part = rest.split("@", 1)
            user = creds.split(":", 1)[0]
            masked_url = f"{proto}://{user}:*****@{host_part}"
        except Exception:
            masked_url = "database://***"

    logger.info("Attempting to connect to database at %s", masked_url)

    # 1. Try configured DATABASE_URL (MySQL by default)
    try:
        temp_engine = create_engine(
            primary_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={"connect_timeout": 2} if "mysql" in primary_url else {}
        )
        with temp_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        engine = temp_engine
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        _db_status["connected"] = True
        _db_status["dialect"] = engine.dialect.name
        _db_status["url"] = masked_url
        _db_status["message"] = f"Connected successfully to {engine.dialect.name.upper()} database."
        logger.info("Successfully connected to primary database (%s).", engine.dialect.name)
        return True
    except Exception as exc:
        err_msg = str(exc)
        logger.warning(
            "Primary database connection failed: %s\n"
            "Ensure MySQL is running (e.g., via 'docker-compose up -d' or local service) "
            "and DATABASE_URL is correct in .env.",
            err_msg
        )
        _db_status["connected"] = False
        _db_status["message"] = (
            f"Unable to connect to MySQL database at {masked_url}. "
            "Check that MySQL is running ('docker-compose up -d' or local server) "
            "and that user credentials are valid in .env."
        )

        # Fallback to SQLite if enabled
        if settings.FALLBACK_SQLITE_IF_MYSQL_UNAVAILABLE:
            sqlite_path = settings.PROJECT_ROOT / "data" / "insightiq_local.sqlite3"
            fallback_url = f"sqlite:///{sqlite_path}"
            logger.info("Falling back to local SQLite database: %s", fallback_url)
            try:
                engine = create_engine(
                    fallback_url,
                    connect_args={"check_same_thread": False}
                )
                SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                Base.metadata.create_all(bind=engine)
                _db_status["connected"] = True
                _db_status["dialect"] = "sqlite"
                _db_status["url"] = f"sqlite:///{sqlite_path.name}"
                _db_status["message"] = (
                    "Running with local SQLite storage (MySQL was unreachable). "
                    "Start MySQL and restart to use MySQL."
                )
                logger.info("SQLite fallback initialized successfully.")
                return True
            except Exception as e_fallback:
                logger.error("Failed to initialize SQLite fallback: %s", e_fallback)
                _db_status["message"] = f"DB connection failed: {err_msg}"
                return False
        return False


def get_db_status():
    global _db_status, engine
    if engine is not None:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            _db_status["connected"] = True
        except Exception as exc:
            _db_status["connected"] = False
            _db_status["message"] = f"Connection lost: {str(exc)}"
    return _db_status


def get_db():
    global SessionLocal
    if SessionLocal is None:
        init_db()
    if SessionLocal is None:
        raise RuntimeError(
            "Database is not initialized. Please ensure MySQL or SQLite is accessible."
        )
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
