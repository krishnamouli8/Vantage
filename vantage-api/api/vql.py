"""
VQL (Vantage Query Language) - SQL-like query language for metrics

Simple implementation that converts VQL to SQL for querying metrics.
"""

import re
import logging
import sqlite3
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VQLQuery:
    """Parsed VQL query structure"""
    
    select_fields: List[str]
    where_conditions: List[Dict[str, Any]]
    group_by: Optional[List[str]]
    order_by: Optional[List[Dict[str, str]]]
    limit: Optional[int]
    time_range: Optional[Dict[str, Any]]


class VQLParser:
    """Parse VQL queries into structured format"""
    
    def parse(self, query: str) -> VQLQuery:
        """Parse VQL query string"""
        query = query.strip()
        
        # Extract SELECT clause
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', query, re.IGNORECASE)
        if not select_match:
            raise ValueError("Invalid query: SELECT clause required")
        
        select_fields = [f.strip() for f in select_match.group(1).split(',')]
        
        # Extract WHERE clause
        where_conditions = []
        where_match = re.search(r'WHERE\s+(.*?)(?:\s+GROUP BY|\s+ORDER BY|\s+LIMIT|$)', query, re.IGNORECASE)
        if where_match:
            where_conditions = self._parse_where(where_match.group(1))
        
        # Extract GROUP BY
        group_by = None
        group_match = re.search(r'GROUP BY\s+(.*?)(?:\s+ORDER BY|\s+LIMIT|$)', query, re.IGNORECASE)
        if group_match:
            group_by = [f.strip() for f in group_match.group(1).split(',')]
        
        # Extract ORDER BY
        order_by = None
        order_match = re.search(r'ORDER BY\s+(.*?)(?:\s+LIMIT|$)', query, re.IGNORECASE)
        if order_match:
            order_by = self._parse_order_by(order_match.group(1))
        
        # Extract LIMIT
        limit = None
        limit_match = re.search(r'LIMIT\s+(\d+)', query, re.IGNORECASE)
        if limit_match:
            limit = int(limit_match.group(1))
        
        # Extract time range from WHERE
        time_range = self._extract_time_range(where_conditions)
        
        return VQLQuery(
            select_fields=select_fields,
            where_conditions=where_conditions,
            group_by=group_by,
            order_by=order_by,
            limit=limit,
            time_range=time_range
        )
    
    def _parse_where(self, where_clause: str) -> List[Dict[str, Any]]:
        """Parse WHERE conditions"""
        conditions = []
        
        # Split by AND
        parts = re.split(r'\s+AND\s+', where_clause, flags=re.IGNORECASE)
        
        for part in parts:
            part = part.strip()
            
            # Match: field operator value
            match = re.match(r'(\w+)\s*(=|>|<|>=|<=|!=)\s*(.+)', part)
            if match:
                field, operator, value = match.groups()
                value = value.strip().strip("'\"")
                
                conditions.append({
                    'field': field,
                    'operator': operator,
                    'value': value
                })
        
        return conditions
    
    def _parse_order_by(self, order_clause: str) -> List[Dict[str, str]]:
        """Parse ORDER BY clause"""
        orders = []
        parts = [p.strip() for p in order_clause.split(',')]
        
        for part in parts:
            match = re.match(r'(\w+)(?:\s+(ASC|DESC))?', part, re.IGNORECASE)
            if match:
                field = match.group(1)
                direction = match.group(2).upper() if match.group(2) else 'ASC'
                orders.append({'field': field, 'direction': direction})
        
        return orders
    
    def _extract_time_range(self, conditions: List[Dict]) -> Optional[Dict]:
        """Extract time range from conditions"""
        time_range = {}
        
        for cond in conditions:
            if cond['field'] == 'timestamp':
                if cond['operator'] in ('>', '>='):
                    time_range['start'] = int(cond['value'])
                elif cond['operator'] in ('<', '<='):
                    time_range['end'] = int(cond['value'])
        
        return time_range if time_range else None


class VQLExecutor:
    """Execute VQL queries against the database"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.parser = VQLParser()
    
    def execute(self, vql_query: str) -> List[Dict[str, Any]]:
        """Execute VQL query and return results"""
        try:
            # Parse VQL
            parsed = self.parser.parse(vql_query)
            
            # Convert to SQL
            sql, params = self._to_sql(parsed)
            
            # Execute
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            logger.info(f"Executing SQL: {sql}")
            logger.debug(f"Parameters: {params}")
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            # Convert to dicts
            results = [dict(row) for row in rows]
            
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Error executing VQL query: {e}")
            raise
    
    def _to_sql(self, query: VQLQuery) -> tuple:
        """Convert VQLQuery to SQL"""
        # Build SELECT
        select_clause = self._build_select(query.select_fields)
        
        # Build WHERE
        where_clause, params = self._build_where(query.where_conditions)
        
        # Build GROUP BY
        group_clause = ""
        if query.group_by:
            group_clause = f"GROUP BY {', '.join(query.group_by)}"
        
        # Build ORDER BY
        order_clause = ""
        if query.order_by:
            orders = [f"{o['field']} {o['direction']}" for o in query.order_by]
            order_clause = f"ORDER BY {', '.join(orders)}"
        
        # Build LIMIT
        limit_clause = ""
        if query.limit:
            limit_clause = f"LIMIT {query.limit}"
        
        # Combine
        sql_parts = [
            f"SELECT {select_clause}",
            "FROM metrics",
            where_clause,
            group_clause,
            order_clause,
            limit_clause
        ]
        
        sql = " ".join(p for p in sql_parts if p)
        
        return sql, params
    
    def _build_select(self, fields: List[str]) -> str:
        """Build SELECT clause with function support"""
        select_parts = []
        
        for field in fields:
            # Handle aggregation functions
            if 'avg(' in field.lower():
                select_parts.append(field.replace('avg(', 'AVG(').replace(')', ')'))
            elif 'count(' in field.lower():
                select_parts.append(field.replace('count(', 'COUNT(').replace(')', ')'))
            elif 'sum(' in field.lower():
                select_parts.append(field.replace('sum(', 'SUM(').replace(')', ')'))
            elif 'min(' in field.lower():
                select_parts.append(field.replace('min(', 'MIN(').replace(')', ')'))
            elif 'max(' in field.lower():
                select_parts.append(field.replace('max(', 'MAX(').replace(')', ')'))
            elif 'percentile(' in field.lower():
                # Custom percentile - use p95/p99 columns if aggregated
                match = re.match(r'percentile\((\w+),\s*(\d+)\)', field, re.IGNORECASE)
                if match:
                    col, pct = match.groups()
                    select_parts.append(f"p{pct}")
                else:
                    select_parts.append(field)
            else:
                select_parts.append(field)
        
        return ", ".join(select_parts)
    
    def _build_where(self, conditions: List[Dict]) -> tuple:
        """Build WHERE clause"""
        if not conditions:
            return "", []
        
        where_parts = []
        params = []
        
        for cond in conditions:
            where_parts.append(f"{cond['field']} {cond['operator']} ?")
            params.append(cond['value'])
        
        where_clause = "WHERE " + " AND ".join(where_parts)
        
        return where_clause, params
