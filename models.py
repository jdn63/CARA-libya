"""
CARA Template — database models.

Extend these models to add fields specific to your deployment.
Run `alembic revision --autogenerate -m "description"` and then
`alembic upgrade head` after any model change.
"""

from datetime import datetime
from app import db


class JurisdictionCache(db.Model):
    """Cached risk assessment results for a jurisdiction."""
    __tablename__ = "jurisdiction_cache"

    id = db.Column(db.Integer, primary_key=True)
    jurisdiction_id = db.Column(db.String(128), nullable=False, index=True)
    profile = db.Column(db.String(64), nullable=False, default="international")
    computed_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_score = db.Column(db.Float, nullable=True)
    risk_level = db.Column(db.String(32), nullable=True)
    domain_scores = db.Column(db.JSON, nullable=True)
    domain_components = db.Column(db.JSON, nullable=True)
    data_sources_used = db.Column(db.JSON, nullable=True)
    data_coverage = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f"<JurisdictionCache {self.jurisdiction_id} score={self.total_score}>"


class ConnectorDataCache(db.Model):
    """
    Raw connector output cache. Each connector result is stored separately
    to allow partial refreshes.
    """
    __tablename__ = "connector_data_cache"

    id = db.Column(db.Integer, primary_key=True)
    jurisdiction_id = db.Column(db.String(128), nullable=False, index=True)
    connector_name = db.Column(db.String(64), nullable=False, index=True)
    fetched_at = db.Column(db.DateTime, default=datetime.utcnow)
    data = db.Column(db.JSON, nullable=True)
    available = db.Column(db.Boolean, default=False)
    error_message = db.Column(db.Text, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('jurisdiction_id', 'connector_name',
                            name='uq_connector_jurisdiction'),
    )


class UserFeedback(db.Model):
    """User feedback on assessments."""
    __tablename__ = "user_feedback"

    id = db.Column(db.Integer, primary_key=True)
    jurisdiction_id = db.Column(db.String(128), nullable=True, index=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    feedback_type = db.Column(db.String(32), nullable=True)
    message = db.Column(db.Text, nullable=True)
    contact_email = db.Column(db.String(128), nullable=True)
    resolved = db.Column(db.Boolean, default=False)


class SystemEvent(db.Model):
    """Audit log for system events (scheduler runs, errors, etc.)."""
    __tablename__ = "system_events"

    id = db.Column(db.Integer, primary_key=True)
    occurred_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    event_type = db.Column(db.String(64), nullable=False, index=True)
    severity = db.Column(db.String(16), default="info")
    message = db.Column(db.Text, nullable=True)
    details = db.Column(db.JSON, nullable=True)
