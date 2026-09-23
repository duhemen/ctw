"""Model SQLAlchemy CTW - Fase 2B."""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, Date, Boolean, ForeignKey
)
from sqlalchemy.orm import relationship
from core.database import Base
from core.utils import utcnow


class Region(Base):
    __tablename__ = "regions"

    code = Column(String(20), primary_key=True)
    name = Column(String(150), nullable=False, index=True)
    level = Column(String(20), nullable=False, index=True)
    parent_code = Column(String(20), ForeignKey("regions.code"), nullable=True, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)


class Provider(Base):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    npwp = Column(String(30), default="")
    siujk_number = Column(String(50), default="")
    classification = Column(String(50), default="")
    qualification = Column(String(20), default="")
    address = Column(String(300), default="")
    region_code = Column(String(20), ForeignKey("regions.code"), nullable=True)
    contact_person = Column(String(150), default="")
    phone = Column(String(30), default="")
    email = Column(String(100), default="")
    created_at = Column(DateTime, default=utcnow)

    region = relationship("Region")
    blacklist_entries = relationship(
        "Blacklist", back_populates="provider", cascade="all, delete-orphan"
    )


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, default="")
    region_code = Column(String(20), ForeignKey("regions.code"), nullable=True, index=True)
    address = Column(String(300), default="")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String(50), default="Berjalan", index=True)

    contract_number = Column(String(100), default="")
    contract_value = Column(Float, default=0.0)
    contract_start = Column(Date, nullable=True)
    contract_end = Column(Date, nullable=True)
    duration_days = Column(Integer, default=0)
    is_multi_year = Column(Boolean, default=False)
    funding_source = Column(String(50), default="")
    fiscal_year = Column(Integer, nullable=True)

    risk_level = Column(String(20), default="Sedang", index=True)
    progress_physical = Column(Float, default=0.0)
    progress_financial = Column(Float, default=0.0)
    time_work_percent = Column(Float, default=0.0)
    progress_updated_at = Column(DateTime, nullable=True)

    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=True)
    supervisor_id = Column(Integer, ForeignKey("providers.id"), nullable=True)

    created_at = Column(DateTime, default=utcnow)

    region = relationship("Region")
    provider = relationship("Provider", foreign_keys=[provider_id])
    supervisor = relationship("Provider", foreign_keys=[supervisor_id])
    feedbacks = relationship("Feedback", back_populates="project", cascade="all, delete-orphan")
    schedules = relationship("ProjectSchedule", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("ProjectMilestone", back_populates="project", cascade="all, delete-orphan")
    photos = relationship("ProjectPhoto", back_populates="project", cascade="all, delete-orphan")


class ProjectSchedule(Base):
    __tablename__ = "project_schedules"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    period = Column(String(20), nullable=False)
    planned_percent = Column(Float, default=0.0)
    actual_percent = Column(Float, default=0.0)

    project = relationship("Project", back_populates="schedules")


class ProjectMilestone(Base):
    __tablename__ = "project_milestones"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    target_date = Column(Date, nullable=True)
    actual_date = Column(Date, nullable=True)
    status = Column(String(30), default="Pending")
    progress = Column(Float, default=0.0)
    notes = Column(Text, default="")

    project = relationship("Project", back_populates="milestones")


class ProjectPhoto(Base):
    __tablename__ = "project_photos"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    caption = Column(String(300), default="")
    category = Column(String(50), default="progress")
    taken_at = Column(DateTime, default=utcnow)

    project = relationship("Project", back_populates="photos")


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    feedback_type = Column(String(20), nullable=False)
    reporter_name = Column(String(150), default="Anonim")
    reporter_contact = Column(String(150), default="")
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    attachment_path = Column(String(500), default="")
    status = Column(String(30), default="Baru")
    created_at = Column(DateTime, default=utcnow)

    project = relationship("Project", back_populates="feedbacks")


class Blacklist(Base):
    __tablename__ = "blacklist"

    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    reason = Column(Text, nullable=False)
    category = Column(String(50), default="Lainnya")
    regulation_ref = Column(String(200), default="")
    decision_by = Column(String(200), default="")
    decision_number = Column(String(100), default="")
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(String(30), default="Aktif")
    document_url = Column(String(500), default="")
    created_at = Column(DateTime, default=utcnow)

    provider = relationship("Provider", back_populates="blacklist_entries")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(128), default="")
    role = Column(String(32), default="admin")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)


# ============================================================
# OBSERVASI LAPANGAN (dari spatianomics.db)
# ============================================================

class ObservationVariable(Base):
    """Katalog variabel observasi (20 jenis)."""
    __tablename__ = "observation_variables"

    id = Column(Integer, primary_key=True)
    kode = Column(String(32), unique=True, nullable=False, index=True)
    nama = Column(String(128), nullable=False)
    deskripsi = Column(Text, default="")
    level_target = Column(String(128), default="")
    tipe = Column(String(16), default="boolean")  # boolean | scale
    severity_weight = Column(Float, default=0.5)
    is_active = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=True)


class Observation(Base):
    """Data observasi lapangan per wilayah."""
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True)
    wilayah_kode = Column(String(20), nullable=False, index=True)
    variable_kode = Column(String(32), nullable=False, index=True)
    nilai = Column(Float, default=0.0)
    catatan = Column(Text, default="")
    foto_path = Column(String(500), default="")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    observer = Column(String(64), default="")
    verified = Column(Boolean, default=False)
    verified_by = Column(String(64), default="")
    rejected = Column(Boolean, default=False)
    rejection_reason = Column(Text, default="")
    timestamp = Column(DateTime, default=utcnow)
    # Metadata
    severity_score = Column(Float, default=0.0)  # weight * nilai
    severity_level = Column(String(16), default="rendah")  # rendah | sedang | tinggi
    created_at = Column(DateTime, default=utcnow)
