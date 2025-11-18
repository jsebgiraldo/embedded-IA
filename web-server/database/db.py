"""SQLite database setup and models."""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

# Database URL
DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATABASE_DIR, exist_ok=True)
DATABASE_URL = f"sqlite:///{os.path.join(DATABASE_DIR, 'agent_dashboard.db')}"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Agent(Base):
    """Agent model for storing agent information."""
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # developer, test, build
    status = Column(String, default="idle")  # idle, active, error
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = Column(DateTime, nullable=True)


class Job(Base):
    """Job model for storing job execution history."""
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String, nullable=False)  # fix_build, test_suite, analysis
    status = Column(String, default="pending")  # pending, running, success, failed, cancelled
    agent_id = Column(String, nullable=True)
    model_used = Column(String, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # in seconds
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Log(Base):
    """Log model for storing system logs."""
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String, nullable=False)  # INFO, WARNING, ERROR, DEBUG, SUCCESS
    agent_id = Column(String, nullable=True, index=True)
    job_id = Column(Integer, nullable=True, index=True)
    message = Column(Text, nullable=False)
    meta_data = Column(Text, nullable=True)  # JSON string for additional data


class Metric(Base):
    """Metric model for storing performance metrics."""
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metric_type = Column(String, nullable=False)  # success_rate, avg_time, model_usage
    agent_id = Column(String, nullable=True, index=True)
    value = Column(Float, nullable=False)
    meta_data = Column(Text, nullable=True)  # JSON string for additional data


# ============================================================================
# GitHub Integration Models
# ============================================================================

class Project(Base):
    """Project imported from GitHub."""
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, index=True)  # UUID
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # GitHub info
    repo_url = Column(String, nullable=False)
    repo_full_name = Column(String, nullable=False, index=True)  # owner/repo
    branch = Column(String, default="main")
    
    # Local info
    clone_path = Column(String, nullable=False)
    last_commit_sha = Column(String, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    
    # ESP32 config
    target = Column(String, default="esp32")  # esp32, esp32s2, esp32s3, esp32c3
    build_system = Column(String, default="cmake")  # cmake, make
    
    # Status
    status = Column(String, default="pending", index=True)  # pending, active, error, archived
    webhook_secret = Column(String, nullable=True)  # For validating webhooks
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String, nullable=True)  # User ID (future auth)
    
    # Relationships
    dependencies = relationship("Dependency", back_populates="project", cascade="all, delete-orphan")
    builds = relationship("Build", back_populates="project", cascade="all, delete-orphan")


class Dependency(Base):
    """ESP-IDF component dependency."""
    __tablename__ = "dependencies"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Component info
    component_name = Column(String, nullable=False, index=True)
    version = Column(String, nullable=False)
    source = Column(String, nullable=False)  # registry, git, local
    
    # Git source (if applicable)
    git_url = Column(String, nullable=True)
    git_ref = Column(String, nullable=True)  # commit, tag, branch
    
    # Installation
    installed = Column(Boolean, default=False)
    installed_at = Column(DateTime, nullable=True)
    install_error = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    project = relationship("Project", back_populates="dependencies")


class Build(Base):
    """Build history for projects."""
    __tablename__ = "builds"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Build info
    commit_sha = Column(String, nullable=False, index=True)
    commit_message = Column(Text, nullable=True)
    commit_author = Column(String, nullable=True)
    branch = Column(String, nullable=False, index=True)
    
    # Execution
    status = Column(String, default="pending", index=True)  # pending, running, success, failed
    started_at = Column(DateTime, nullable=True, index=True)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # in seconds
    
    # Results
    build_output = Column(Text, nullable=True)
    test_results = Column(Text, nullable=True)  # JSON string
    artifacts_path = Column(String, nullable=True)
    
    # Trigger
    triggered_by = Column(String, nullable=False)  # webhook, manual, scheduled
    github_event_type = Column(String, nullable=True)  # push, pull_request
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    project = relationship("Project", back_populates="builds")


class WebhookEvent(Base):
    """GitHub webhook event log."""
    __tablename__ = "webhook_events"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Event info
    event_type = Column(String, nullable=False, index=True)  # push, pull_request, ping
    event_id = Column(String, unique=True, nullable=False, index=True)  # GitHub delivery ID
    payload = Column(Text, nullable=False)  # Full JSON payload
    
    # Processing
    status = Column(String, default="pending", index=True)  # pending, processing, success, failed
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Validation
    signature_valid = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    print(f"✅ Database initialized at: {DATABASE_URL}")


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
