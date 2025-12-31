"""
Base Tracker Class for Heart Portal Health Trackers
Eliminates ~400 lines of duplicate code across Sodium, Fluid, Weight, and BP trackers

Usage:
    class SodiumTracker(BaseTracker):
        def __init__(self, database_url):
            super().__init__(
                database_url=database_url,
                table_name='sodium_entries',
                entry_fields=['food_item', 'sodium_mg', 'serving_size', 'meal_type', 'notes']
            )

        def validate_entry(self, **kwargs):
            sodium_mg = kwargs.get('sodium_mg', 0)
            return 0 <= sodium_mg <= 50000
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from database import DatabaseConfig
from logger import get_logger

logger = get_logger('base-tracker')


class BaseTracker(ABC):
    """Abstract base class for all health trackers"""

    def __init__(self, database_url: str, table_name: str, entry_fields: List[str]):
        """
        Initialize base tracker

        Args:
            database_url: PostgreSQL connection string
            table_name: Name of the entries table (e.g., 'sodium_entries')
            entry_fields: List of field names specific to this tracker
        """
        self.db = DatabaseConfig(database_url)
        self.table_name = table_name
        self.entry_fields = entry_fields
        logger.info(f"Initialized {self.__class__.__name__} with table {table_name}")

    @abstractmethod
    def validate_entry(self, **kwargs) -> Tuple[bool, Optional[str]]:
        """
        Validate entry data before insertion
        Each tracker must implement its own validation logic

        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        pass

    def add_entry(
        self,
        user_id: int,
        date: str,
        **kwargs
    ) -> Tuple[bool, Optional[str]]:
        """
        Add a new entry with automatic validation

        Args:
            user_id: User ID
            date: Entry date (YYYY-MM-DD format)
            **kwargs: Tracker-specific fields

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        # Validate entry data
        is_valid, error_message = self.validate_entry(**kwargs)
        if not is_valid:
            logger.warning(f"Validation failed for {self.table_name}: {error_message}")
            return False, error_message

        # Prepare fields and values
        fields = ['user_id', 'date'] + list(kwargs.keys())
        placeholders = ', '.join([self.db.get_placeholder()] * len(fields))
        values = [user_id, date] + list(kwargs.values())

        query = f"""
            INSERT INTO {self.table_name} ({', '.join(fields)})
            VALUES ({placeholders})
        """

        try:
            result = self.db.execute_query(query, tuple(values))
            if result > 0:
                logger.info(f"Added entry to {self.table_name} for user {user_id} on {date}")
                return True, None
            return False, "Failed to insert entry"
        except Exception as e:
            logger.error(f"Error adding entry to {self.table_name}: {e}")
            return False, str(e)

    def get_entries(
        self,
        user_id: int,
        limit: int = 30,
        offset: int = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get user entries with optional date filtering and pagination

        Args:
            user_id: User ID
            limit: Maximum number of entries to return
            offset: Number of entries to skip (for pagination)
            start_date: Filter entries from this date (YYYY-MM-DD)
            end_date: Filter entries up to this date (YYYY-MM-DD)

        Returns:
            List of entry dictionaries
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE user_id = {self.db.get_placeholder()}
        """
        params = [user_id]

        if start_date:
            query += f" AND date >= {self.db.get_placeholder()}"
            params.append(start_date)

        if end_date:
            query += f" AND date <= {self.db.get_placeholder()}"
            params.append(end_date)

        query += f"""
            ORDER BY date DESC
            LIMIT {self.db.get_placeholder()} OFFSET {self.db.get_placeholder()}
        """
        params.extend([limit, offset])

        try:
            entries = self.db.execute_query(query, tuple(params), fetch_all=True)
            logger.debug(f"Retrieved {len(entries)} entries from {self.table_name} for user {user_id}")
            return entries
        except Exception as e:
            logger.error(f"Error retrieving entries from {self.table_name}: {e}")
            return []

    def get_entry_by_date(self, user_id: int, date: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific entry by user ID and date

        Args:
            user_id: User ID
            date: Entry date (YYYY-MM-DD)

        Returns:
            Entry dictionary or None if not found
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE user_id = {self.db.get_placeholder()}
            AND date = {self.db.get_placeholder()}
        """

        try:
            entry = self.db.execute_query(query, (user_id, date), fetch_one=True)
            return entry
        except Exception as e:
            logger.error(f"Error retrieving entry from {self.table_name}: {e}")
            return None

    def update_entry(
        self,
        user_id: int,
        date: str,
        **kwargs
    ) -> Tuple[bool, Optional[str]]:
        """
        Update an existing entry

        Args:
            user_id: User ID
            date: Entry date (YYYY-MM-DD)
            **kwargs: Fields to update

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        # Validate entry data
        is_valid, error_message = self.validate_entry(**kwargs)
        if not is_valid:
            logger.warning(f"Validation failed for {self.table_name}: {error_message}")
            return False, error_message

        # Build SET clause
        set_clauses = [f"{field} = {self.db.get_placeholder()}" for field in kwargs.keys()]
        values = list(kwargs.values()) + [user_id, date]

        query = f"""
            UPDATE {self.table_name}
            SET {', '.join(set_clauses)}
            WHERE user_id = {self.db.get_placeholder()}
            AND date = {self.db.get_placeholder()}
        """

        try:
            result = self.db.execute_query(query, tuple(values))
            if result > 0:
                logger.info(f"Updated entry in {self.table_name} for user {user_id} on {date}")
                return True, None
            return False, "Entry not found"
        except Exception as e:
            logger.error(f"Error updating entry in {self.table_name}: {e}")
            return False, str(e)

    def delete_entry(self, user_id: int, date: str) -> Tuple[bool, Optional[str]]:
        """
        Delete an entry

        Args:
            user_id: User ID
            date: Entry date (YYYY-MM-DD)

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        query = f"""
            DELETE FROM {self.table_name}
            WHERE user_id = {self.db.get_placeholder()}
            AND date = {self.db.get_placeholder()}
        """

        try:
            result = self.db.execute_query(query, (user_id, date))
            if result > 0:
                logger.info(f"Deleted entry from {self.table_name} for user {user_id} on {date}")
                return True, None
            return False, "Entry not found"
        except Exception as e:
            logger.error(f"Error deleting entry from {self.table_name}: {e}")
            return False, str(e)

    def get_statistics(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate statistics for user entries over specified days

        Args:
            user_id: User ID
            days: Number of days to include in statistics

        Returns:
            Dictionary with statistics (count, average, min, max, etc.)
        """
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        entries = self.get_entries(user_id, limit=1000, start_date=start_date)

        if not entries:
            return {
                'count': 0,
                'days': days,
                'entries': []
            }

        return {
            'count': len(entries),
            'days': days,
            'start_date': start_date,
            'end_date': datetime.now().strftime('%Y-%m-%d'),
            'entries': entries
        }

    def get_entry_count(self, user_id: int) -> int:
        """
        Get total number of entries for a user

        Args:
            user_id: User ID

        Returns:
            Total entry count
        """
        query = f"""
            SELECT COUNT(*) as count FROM {self.table_name}
            WHERE user_id = {self.db.get_placeholder()}
        """

        try:
            result = self.db.execute_query(query, (user_id,), fetch_one=True)
            return result['count'] if result else 0
        except Exception as e:
            logger.error(f"Error counting entries in {self.table_name}: {e}")
            return 0
