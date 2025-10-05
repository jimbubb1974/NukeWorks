"""
Base database models and mixins
"""
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, event
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.declarative import declared_attr

# Create base class for all models
Base = declarative_base()


class TimestampMixin:
    """
    Mixin to add timestamp fields and optimistic locking
    Includes created_date, modified_date, created_by, modified_by

    All tables with this mixin will have:
    - created_date: TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
    - modified_date: TIMESTAMP (updated on modification)
    - created_by: INTEGER FK to users.user_id
    - modified_by: INTEGER FK to users.user_id
    """

    @declared_attr
    def created_date(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    @declared_attr
    def modified_date(cls):
        return Column(DateTime, onupdate=datetime.utcnow)

    @declared_attr
    def created_by(cls):
        return Column(Integer, ForeignKey('users.user_id'))

    @declared_attr
    def modified_by(cls):
        return Column(Integer, ForeignKey('users.user_id'))

    def check_concurrent_modification(self, original_modified_date):
        """
        Check if record was modified by another user (optimistic locking)

        Args:
            original_modified_date: Timestamp when user loaded the record

        Returns:
            Boolean: True if record was modified, False otherwise

        Raises:
            ConcurrentModificationError: if record was modified by another user
        """
        if self.modified_date and original_modified_date:
            # Convert to datetime if string
            if isinstance(original_modified_date, str):
                from dateutil.parser import parse
                original_modified_date = parse(original_modified_date)

            if self.modified_date > original_modified_date:
                from app.exceptions import ConcurrentModificationError
                raise ConcurrentModificationError(
                    f"Record was modified by another user at {self.modified_date}. "
                    f"Please refresh and try again."
                )
        return False

    def touch(self, user_id=None):
        """
        Update modified_date timestamp

        Args:
            user_id: ID of user making the modification
        """
        self.modified_date = datetime.utcnow()
        if user_id:
            self.modified_by = user_id
