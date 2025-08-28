from .models import get_db_connection
import datetime

def fetch_balance_by_phone(phone_number):
    conn = get_db_connection()
    if not conn:
        return "⚠️ Could not connect to the database."

    try:
        with conn.cursor() as cursor:
            query = """
                SELECT balance_kes
                FROM parent
                WHERE phone_number = %s
            """
            cursor.execute(query, (phone_number,))
            result = cursor.fetchone()

            if result:
                balance = result[0]
                return f"💰 Your current balance is KES {balance:.2f}"
            else:
                return "❌ No account found for this number. Please contact support."

    except Exception as e:
        print(f"Error fetching balance: {e}")
        return "⚠️ An error occurred while retrieving your balance."

    finally:
        conn.close()

def fetch_balance_by_phone_and_id(phone_number, national_id):
    conn = get_db_connection()
    if not conn:
        return "⚠️ Could not connect to the database."

    try:
        with conn.cursor() as cursor:
            query = """
                SELECT balance_kes
                FROM parent
                WHERE phone_number = %s AND national_id = %s
            """
            cursor.execute(query, (phone_number, national_id))
            result = cursor.fetchone()

            if result:
                balance = result[0]
                return f"💰 The parent's balance is KES {balance:.2f}"
            else:
                return "❌ No matching parent found. Please check the phone number and ID."

    except Exception as e:
        print(f"Error fetching balance: {e}")
        return "⚠️ An error occurred while retrieving the balance."

    finally:
        conn.close()

def verify_parent(phone_number, national_id):
    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 1
                FROM parent
                WHERE phone_number = %s AND national_id = %s
                LIMIT 1;
            """, (phone_number, national_id))
            return cursor.fetchone() is not None

    except Exception as e:
        print(f"Error verifying parent: {e}")
        return False

    finally:
        conn.close()

def fetch_children_by_parent_phone(phone_number):
    conn = get_db_connection()
    if not conn:
        return "⚠️ Could not connect to the database."

    try:
        with conn.cursor() as cursor:
            query = """
                SELECT c.full_name, c.birth_date, c.gender, s.name as school_name, c.grade
                FROM child c
                JOIN parent p ON c.parent_id = p.id
                JOIN school s ON c.school_id = s.id
                WHERE p.phone_number = %s
                ORDER BY c.full_name
            """
            cursor.execute(query, (phone_number,))
            children = cursor.fetchall()

            if children:
                response = "👧 Your registered children:\n\n"
                for i, child in enumerate(children, 1):
                    full_name, birth_date, gender, school_name, grade = child
                    
                    response += f"{i}. {full_name} ({gender}), {grade}, {school_name}\n"
                
                return response
            else:
                return "❌ No children found for your account. Please contact support."

    except Exception as e:
        print(f"Error fetching children: {e}")
        return "⚠️ An error occurred while retrieving children information."

    finally:
        conn.close()
def get_child_with_active_tag(parent_phone, child_id=None):
    """Get children with active tags for a parent"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cursor:
            if child_id:
                # Get specific child with active tag
                query = """
                    SELECT c.id, c.full_name, c.grade, t.id as tag_id
                    FROM child c
                    JOIN tag t ON c.id = t.child_id
                    JOIN parent p ON c.parent_id = p.id
                    WHERE p.phone_number = %s AND c.id = %s AND t.status = 'active'
                """
                cursor.execute(query, (parent_phone, child_id))
            else:
                # Get all children with active tags
                query = """
                    SELECT c.id, c.full_name, c.grade, t.id as tag_id
                    FROM child c
                    JOIN tag t ON c.id = t.child_id
                    JOIN parent p ON c.parent_id = p.id
                    WHERE p.phone_number = %s AND t.status = 'active'
                    ORDER BY c.full_name
                """
                cursor.execute(query, (parent_phone,))
            
            return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching children with active tags: {e}")
        return []
    finally:
        conn.close()

def deactivate_tag(tag_id):
    """Deactivate a tag by setting status to inactive"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE tag SET status = 'inactive' WHERE id = %s
            """, (tag_id,))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error deactivating tag: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
def get_child_with_active_tag(parent_phone, child_id=None):
    """Get children with active tags for a parent"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cursor:
            if child_id:
                # Get specific child with active tag
                query = """
                    SELECT c.id, c.full_name, c.grade, t.id as tag_id
                    FROM child c
                    JOIN tag t ON c.id = t.child_id
                    JOIN parent p ON c.parent_id = p.id
                    WHERE p.phone_number = %s AND c.id = %s AND t.status = 'active'
                """
                cursor.execute(query, (parent_phone, child_id))
            else:
                # Get all children with active tags
                query = """
                    SELECT c.id, c.full_name, c.grade, t.id as tag_id
                    FROM child c
                    JOIN tag t ON c.id = t.child_id
                    JOIN parent p ON c.parent_id = p.id
                    WHERE p.phone_number = %s AND t.status = 'active'
                    ORDER BY c.full_name
                """
                cursor.execute(query, (parent_phone,))
            
            return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching children with active tags: {e}")
        return []
    finally:
        conn.close()

def deactivate_tag(tag_id):
    """Deactivate a tag by setting status to inactive"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE tag SET status = 'inactive' WHERE id = %s
            """, (tag_id,))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error deactivating tag: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
def fetch_children_by_parent_phone(phone_number, include_tags=False):
    """Get children for a parent, optionally with tag information"""
    conn = get_db_connection()
    if not conn:
        return "⚠️ Could not connect to the database." if not include_tags else []

    try:
        with conn.cursor() as cursor:
            if include_tags:
                # Get children with their active tag information
                query = """
                    SELECT c.id, c.full_name, c.gender, s.name as school_name, c.grade, 
                           t.id as tag_id, t.status as tag_status
                    FROM child c
                    JOIN parent p ON c.parent_id = p.id
                    JOIN school s ON c.school_id = s.id
                    LEFT JOIN tag t ON c.id = t.child_id AND t.status = 'active'
                    WHERE p.phone_number = %s
                    ORDER BY c.full_name
                """
                cursor.execute(query, (phone_number,))
                return cursor.fetchall()
            else:
                # Original functionality - just return children info
                query = """
                    SELECT c.full_name, c.birth_date, c.gender, s.name as school_name, c.grade
                    FROM child c
                    JOIN parent p ON c.parent_id = p.id
                    JOIN school s ON c.school_id = s.id
                    WHERE p.phone_number = %s
                    ORDER BY c.full_name
                """
                cursor.execute(query, (phone_number,))
                children = cursor.fetchall()

                if children:
                    response = "👧 Your registered children:\n\n"
                    for i, child in enumerate(children, 1):
                        full_name, birth_date, gender, school_name, grade = child
                        response += f"{i}. {full_name} ({gender}), {grade}, {school_name}\n"
                    return response
                else:
                    return "❌ No children found for your account. Please contact support."

    except Exception as e:
        print(f"Error fetching children: {e}")
        return "⚠️ An error occurred while retrieving children information." if not include_tags else []
    finally:
        conn.close()
def deactivate_child_tag(child_id):
    """Deactivate the active tag for a child"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE tag SET status = 'inactive' 
                WHERE child_id = %s AND status = 'active'
            """, (child_id,))
            conn.commit()
            return cursor.rowcount > 0  # Returns True if a tag was deactivated
    except Exception as e:
        print(f"Error deactivating tag: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()