"""
SQLAlchemy models for BabelLayer.

Each class maps to a single DB table. Relationships are defined here
so the ORM can handle cascading deletes and eager/lazy loading.
"""
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float,
    Boolean, ForeignKey, JSON,
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    role = Column(String(20), default="analyst")  # admin | analyst | viewer
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime)

    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

    @property
    def is_admin(self):
        return self.role == "admin"

    def __repr__(self):
        return f"<User {self.username}>"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="projects")
    datasets = relationship("Dataset", back_populates="project", cascade="all, delete-orphan")
    transformations = relationship("TransformationJob", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project {self.name}>"


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False)  # csv, json, xml, xlsx
    file_size = Column(Integer)
    row_count = Column(Integer)
    column_count = Column(Integer)
    schema_info = Column(JSON)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_source = Column(Boolean, default=True)

    project = relationship("Project", back_populates="datasets")
    mappings_as_source = relationship(
        "FieldMapping", foreign_keys="FieldMapping.source_dataset_id",
        back_populates="source_dataset", cascade="all, delete-orphan",
    )
    mappings_as_target = relationship(
        "FieldMapping", foreign_keys="FieldMapping.target_dataset_id",
        back_populates="target_dataset", cascade="all, delete-orphan",
    )
    quality_reports = relationship("QualityReport", back_populates="dataset", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Dataset {self.name}>"


class FieldMapping(Base):
    """Maps a single field from one dataset to another."""
    __tablename__ = "field_mappings"

    id = Column(Integer, primary_key=True)
    source_dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    target_dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    source_field = Column(String(200), nullable=False)
    target_field = Column(String(200), nullable=False)
    mapping_type = Column(String(50), default="direct")   # direct | transform | calculated
    transformation_rule = Column(Text)
    confidence = Column(Float)     # 0.0–1.0
    ai_suggested = Column(Boolean, default=False)
    confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    source_dataset = relationship("Dataset", foreign_keys=[source_dataset_id],
                                  back_populates="mappings_as_source")
    target_dataset = relationship("Dataset", foreign_keys=[target_dataset_id],
                                  back_populates="mappings_as_target")

    def __repr__(self):
        return f"<Mapping {self.source_field} → {self.target_field}>"


class TransformationJob(Base):
    """Tracks each ETL run: what was mapped, row stats, errors."""
    __tablename__ = "transformations"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    source_dataset_id = Column(Integer, ForeignKey("datasets.id"))
    target_dataset_id = Column(Integer, ForeignKey("datasets.id"))
    output_path = Column(String(500))
    status = Column(String(20), default="pending")   # pending | running | done | failed
    rows_processed = Column(Integer, default=0)
    rows_ok = Column(Integer, default=0)
    rows_failed = Column(Integer, default=0)
    error_log = Column(Text)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="transformations")

    def __repr__(self):
        return f"<TransformationJob {self.name} [{self.status}]>"


class QualityReport(Base):
    __tablename__ = "data_quality_reports"

    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    report_type = Column(String(50), nullable=False)  # anomaly | completeness | consistency
    total_records = Column(Integer)
    issues_found = Column(Integer)
    score = Column(Float)        # 0–100
    anomalies = Column(JSON)
    statistics = Column(JSON)
    recommendations = Column(Text)
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    dataset = relationship("Dataset", back_populates="quality_reports")

    def __repr__(self):
        return f"<QualityReport {self.report_type} score={self.score}>"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    details = Column(JSON)
    ip_address = Column(String(45))
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.action} by user {self.user_id}>"
