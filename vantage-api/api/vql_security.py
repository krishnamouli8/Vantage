"""Enhanced VQL parser with security improvements.

Adds input validation, SQL injection prevention, and query complexity limits.
"""

import re
from typing import List, Set
from vantage_common.exceptions import ValidationError


# Whitelist of allowed table names
ALLOWED_TABLES = {'metrics', 'traces', 'spans', 'alerts'}

# Whitelist of allowed column names for metrics table
ALLOWED_COLUMNS = {
    'id', 'timestamp', 'service_name', 'metric_name', 'metric_type',
    'value', 'endpoint', 'method', 'status_code', 'duration_ms',
    'tags', 'trace_id', 'span_id', 'aggregated', 'resolution_minutes',
    'min_value', 'max_value', 'p50', 'p95', 'p99', 'sample_count',
    'error_count', 'created_at'
}

# Whitelist of allowed SQL aggregate functions
ALLOWED_FUNCTIONS = {'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'PERCENTILE'}

# Whitelist of allowed operators
ALLOWED_OPERATORS = {'=', '>', '<', '>=', '<=', '!=', 'LIKE'}

# Maximum query complexity limits
MAX_SELECT_FIELDS = 20
MAX_WHERE_CONDITIONS = 10
MAX_GROUP_BY_FIELDS = 5
MAX_ORDER_BY_FIELDS = 3
MAX_LIMIT_VALUE = 10000
MAX_JOIN_COUNT = 2


class VQLValidator:
    """Validate and sanitize VQL queries to prevent SQL injection."""
    
    @staticmethod
    def validate_identifier(identifier: str, allowed_set: Set[str]) -> str:
        """Validate an identifier against a whitelist.
        
        Args:
            identifier: The identifier to validate
            allowed_set: Set of allowed identifiers
            
        Returns:
            Validated identifier
            
        Raises:
            ValidationError: If identifier is not in whitelist
        """
        # Remove whitespace
        identifier = identifier.strip()
        
        # Check if it's a valid identifier (alphanumeric + underscore)
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
            raise ValidationError(
                f"Invalid identifier: {identifier}",
                details={"reason": "Contains invalid characters"}
            )
        
        # Check against whitelist
        if identifier.lower() not in {s.lower() for s in allowed_set}:
            raise ValidationError(
                f"Identifier not allowed: {identifier}",
                details={"allowed": list(allowed_set)}
            )
        
        return identifier
    
    @staticmethod
    def validate_operator(operator: str) -> str:
        """Validate SQL operator.
        
        Args:
            operator: The operator to validate
            
        Returns:
            Validated operator
            
        Raises:
            ValidationError: If operator is not allowed
        """
        operator = operator.strip().upper()
        
        if operator not in ALLOWED_OPERATORS:
            raise ValidationError(
                f"Operator not allowed: {operator}",
                details={"allowed": list(ALLOWED_OPERATORS)}
            )
        
        return operator
    
    @staticmethod
    def validate_value(value: str) -> str:
        """Sanitize query value to prevent injection.
        
        Args:
            value: The value to sanitize
            
        Returns:
            Sanitized value
        """
        # Remove quotes
        value = value.strip().strip("'\"")
        
        # Prevent common SQL injection patterns
        dangerous_patterns = [
            r';',  # Statement terminator
            r'--',  # Comment
            r'/\*',  # Block comment
            r'\*/',  # Block comment end
            r'xp_',  # Extended stored procedure
            r'sp_',  # Stored procedure
            r'UNION',  # Union injection
            r'DROP',  # Dangerous command
            r'DELETE',  # Dangerous command
            r'INSERT',  # Dangerous command
            r'UPDATE',  # Dangerous command
            r'EXEC',  # Execute command
            r'EXECUTE',  # Execute command
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError(
                    f"Value contains dangerous pattern: {pattern}",
                    details={"value": value}
                )
        
        return value
    
    @staticmethod
    def validate_limit(limit: int) -> int:
        """Validate LIMIT value.
        
        Args:
            limit: The limit value
            
        Returns:
            Validated limit
            
        Raises:
            ValidationError: If limit exceeds maximum
        """
        if limit <= 0:
            raise ValidationError(
                "LIMIT must be positive",
                details={"limit": limit}
            )
        
        if limit > MAX_LIMIT_VALUE:
            raise ValidationError(
                f"LIMIT exceeds maximum: {MAX_LIMIT_VALUE}",
                details={"limit": limit, "max": MAX_LIMIT_VALUE}
            )
        
        return limit
    
    @staticmethod
    def validate_query_complexity(
        select_count: int,
        where_count: int,
        group_by_count: int,
        order_by_count: int
    ) -> None:
        """Validate overall query complexity.
        
        Raises:
            ValidationError: If query is too complex
        """
        if select_count > MAX_SELECT_FIELDS:
            raise ValidationError(
                f"Too many SELECT fields: {select_count} > {MAX_SELECT_FIELDS}"
            )
        
        if where_count > MAX_WHERE_CONDITIONS:
            raise ValidationError(
                f"Too many WHERE conditions: {where_count} > {MAX_WHERE_CONDITIONS}"
            )
        
        if group_by_count > MAX_GROUP_BY_FIELDS:
            raise ValidationError(
                f"Too many GROUP BY fields: {group_by_count} > {MAX_GROUP_BY_FIELDS}"
            )
        
        if order_by_count > MAX_ORDER_BY_FIELDS:
            raise ValidationError(
                f"Too many ORDER BY fields: {order_by_count} > {MAX_ORDER_BY_FIELDS}"
            )
    
    @staticmethod
    def validate_function(func_name: str) -> str:
        """Validate aggregate function name.
        
        Args:
            func_name: Function name to validate
            
        Returns:
            Validated function name
            
        Raises:
            ValidationError: If function is not allowed
        """
        func_name = func_name.strip().upper()
        
        if func_name not in ALLOWED_FUNCTIONS:
            raise ValidationError(
                f"Function not allowed: {func_name}",
                details={"allowed": list(ALLOWED_FUNCTIONS)}
            )
        
        return func_name
    
    @staticmethod
    def sanitize_like_pattern(pattern: str) -> str:
        """Sanitize LIKE pattern to prevent DoS via catastrophic backtracking.
        
        Args:
            pattern: LIKE pattern
            
        Returns:
            Sanitized pattern
        """
        # Limit pattern length
        if len(pattern) > 100:
            raise ValidationError(
                "LIKE pattern too long",
                details={"max_length": 100}
            )
        
        # Prevent multiple wildcards in a row
        if re.search(r'%{3,}', pattern) or re.search(r'_{3,}', pattern):
            raise ValidationError(
                "LIKE pattern contains too many consecutive wildcards"
            )
        
        return pattern


def validate_vql_query(query: str) -> None:
    """Perform comprehensive validation on VQL query.
    
    Args:
        query: VQL query string
        
    Raises:
        ValidationError: If query is invalid or dangerous
    """
    # Max query length
    if len(query) > 5000:
        raise ValidationError(
            "Query too long",
            details={"max_length": 5000}
        )
    
    # Prevent query stacking
    if ';' in query and query.strip().index(';') < len(query.strip()) - 1:
        raise ValidationError("Multiple statements not allowed")
    
    # Prevent comments
    if '--' in query or '/*' in query:
        raise ValidationError("Comments not allowed in queries")
    
    # Require SELECT
    if not re.search(r'\bSELECT\b', query, re.IGNORECASE):
        raise ValidationError("Query must contain SELECT clause")
    
    # Prevent dangerous keywords (expanded list)
    dangerous_keywords = [
        'DROP', 'DELETE', 'INSERT', 'UPDATE', 'TRUNCATE',
        'ALTER', 'CREATE', 'REPLACE', 'EXEC', 'EXECUTE',
        'PRAGMA', 'ATTACH', 'DETACH'  # SQLite specific dangerous commands
    ]
    for keyword in dangerous_keywords:
        # Use word boundary to avoid false positives
        if re.search(rf'\b{keyword}\b', query, re.IGNORECASE):
            raise ValidationError(
                f"Dangerous keyword not allowed: {keyword}"
            )
    
    # Block access to system tables
    system_tables = ['sqlite_master', 'sqlite_schema', 'sqlite_temp_master']
    for table in system_tables:
        if re.search(rf'\b{table}\b', query, re.IGNORECASE):
            raise ValidationError(
                f"Access to system table not allowed: {table}"
            )
