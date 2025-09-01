import psycopg
from config import DATABASE_CONFIG

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg.connect(**DATABASE_CONFIG)
        return conn
    except psycopg.Error as e:
        print(f"Database connection error: {e}")
        return None

def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            # Message logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS message_logs (
                    id SERIAL PRIMARY KEY,
                    sender VARCHAR(20) NOT NULL,
                    message TEXT,
                    response TEXT,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT,
                    processing_time_ms INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Pending actions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pending_actions (
                    id SERIAL PRIMARY KEY,
                    action_type VARCHAR(50) NOT NULL,
                    sender VARCHAR(20) NOT NULL,
                    details JSONB,
                    status VARCHAR(20) DEFAULT 'pending',
                    admin_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP NULL
                )
            """)
            
            conn.commit()
            return True
            
    except Exception as e:
        print("Database initialization error:", e)
        conn.rollback()
        return False
    finally:
        conn.close()

def log_message(sender, message, response, success=True, error_message=None, processing_time=None):
    """Log message to database"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO message_logs (sender, message, response, success, error_message, processing_time_ms)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (sender, message, response, success, error_message, processing_time))
            conn.commit()
            return True
    except Exception as e:
        print("Error logging message:", e)
        conn.rollback()
        return False
    finally:
        conn.close()

def add_pending_action(action_type, sender, details):
    """Add pending action to database"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO pending_actions (action_type, sender, details)
                VALUES (%s, %s, %s)
            """, (action_type, sender, details))
            conn.commit()
            return True
    except Exception as e:
        print("Error adding pending action:", e)
        conn.rollback()
        return False
    finally:
        conn.close()

def get_recent_messages(limit=50):
    """Get recent messages from database"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, sender, message, response, success, error_message, timestamp 
                FROM message_logs 
                ORDER BY timestamp DESC 
                LIMIT %s
            """, (limit,))
            return cursor.fetchall()
    except Exception as e:
        print("Error fetching messages:", e)
        return []
    finally:
        conn.close()

def get_pending_actions():
    """Get pending actions from database"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, action_type, sender, details, created_at
                FROM pending_actions 
                WHERE status = 'pending'
                ORDER BY created_at DESC
            """)
            return cursor.fetchall()
    except Exception as e:
        print("Error fetching pending actions:", e)
        return []
    finally:
        conn.close()

def get_dashboard_metrics():
    """Get metrics for dashboard"""
    conn = get_db_connection()
    if not conn:
        return {}
    
    try:
        with conn.cursor() as cursor:
            # Total messages
            cursor.execute("SELECT COUNT(*) FROM message_logs")
            total_messages = cursor.fetchone()[0] or 0
            
            # Success rate
            cursor.execute("SELECT COUNT(*) FROM message_logs WHERE success = true")
            success_count = cursor.fetchone()[0] or 0
            success_rate = round((success_count / total_messages * 100), 1) if total_messages > 0 else 0
            
            # Active users (last 24h)
            cursor.execute("""
                SELECT COUNT(DISTINCT sender) 
                FROM message_logs 
                WHERE timestamp >= NOW() - INTERVAL '24 hours'
            """)
            active_users = cursor.fetchone()[0] or 0
            
            # Pending actions
            cursor.execute("SELECT COUNT(*) FROM pending_actions WHERE status = 'pending'")
            pending_actions = cursor.fetchone()[0] or 0
            
            return {
                'total_messages': total_messages,
                'success_rate': success_rate,
                'active_users': active_users,
                'pending_actions': pending_actions
            }
    except Exception as e:
        print("Error fetching metrics:", e)
        return {
            'total_messages': 0,
            'success_rate': 0,
            'active_users': 0,
            'pending_actions': 0
        }
    finally:
        conn.close()
