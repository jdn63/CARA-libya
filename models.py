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


class ExportJob(db.Model):
    """Tracks asynchronous GIS/data export jobs."""
    __tablename__ = "export_jobs"

    id = db.Column(db.Integer, primary_key=True)
    export_type = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(32), nullable=False, default='queued', index=True)
    cache_freshness_minutes = db.Column(db.Integer, default=30)
    params = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    total_count = db.Column(db.Integer, nullable=True)
    processed_count = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)
    result_url = db.Column(db.String(512), nullable=True)

    def __repr__(self):
        return f"<ExportJob {self.id} type={self.export_type} status={self.status}>"


class DataSourceCache(db.Model):
    """Cache for external data source responses."""
    __tablename__ = "data_source_cache"

    id = db.Column(db.Integer, primary_key=True)
    source_type = db.Column(db.String(64), nullable=False, index=True)
    jurisdiction_id = db.Column(db.String(128), nullable=True, index=True)
    county_name = db.Column(db.String(128), nullable=True, index=True)
    data = db.Column(db.JSON, nullable=True)
    fetched_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_valid = db.Column(db.Boolean, default=True, index=True)
    fetch_duration_seconds = db.Column(db.Float, nullable=True)
    api_source = db.Column(db.String(512), nullable=True)
    used_fallback = db.Column(db.Boolean, default=False)
    fallback_reason = db.Column(db.Text, nullable=True)

    @property
    def is_fresh(self):
        if self.expires_at is None:
            return True
        return datetime.utcnow() < self.expires_at

    @property
    def freshness_status(self):
        return 'fresh' if self.is_fresh else 'stale'

    @property
    def age_hours(self):
        if self.fetched_at is None:
            return None
        return (datetime.utcnow() - self.fetched_at).total_seconds() / 3600

    @property
    def age_minutes(self):
        if self.fetched_at is None:
            return None
        return (datetime.utcnow() - self.fetched_at).total_seconds() / 60

    def __repr__(self):
        return f"<DataSourceCache {self.source_type} jid={self.jurisdiction_id}>"


class DataQualityEvent(db.Model):
    """Log of data quality events such as fallback usage or fetch failures."""
    __tablename__ = "data_quality_events"

    id = db.Column(db.Integer, primary_key=True)
    occurred_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    event_type = db.Column(db.String(64), nullable=False)
    source_type = db.Column(db.String(64), nullable=True, index=True)
    jurisdiction_id = db.Column(db.String(128), nullable=True)
    county_name = db.Column(db.String(128), nullable=True)
    severity = db.Column(db.String(16), default='info')
    message = db.Column(db.Text, nullable=True)
    details = db.Column(db.JSON, nullable=True)

    def __repr__(self):
        return f"<DataQualityEvent {self.event_type} source={self.source_type}>"


class HERCRiskCache(db.Model):
    """Cache for computed HERC region risk aggregations."""
    __tablename__ = "herc_risk_cache"

    id = db.Column(db.Integer, primary_key=True)
    herc_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    name = db.Column(db.String(128), nullable=True)
    risk_data = db.Column(db.JSON, nullable=True)
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_valid = db.Column(db.Boolean, default=True, index=True)
    calculation_duration_seconds = db.Column(db.Float, nullable=True)
    jurisdiction_count = db.Column(db.Integer, nullable=True)
    error_message = db.Column(db.Text, nullable=True)

    @property
    def age_minutes(self):
        if self.calculated_at is None:
            return None
        return (datetime.utcnow() - self.calculated_at).total_seconds() / 60

    def __repr__(self):
        return f"<HERCRiskCache {self.herc_id}>"
