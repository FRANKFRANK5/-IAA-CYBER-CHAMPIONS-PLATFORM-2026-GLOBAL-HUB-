import os
import logging
import sys
from flask import request, jsonify
from CTFd import create_app
from CTFd.models import Users, db
from CTFd.utils.crypto import hash_password
from sqlalchemy.exc import SQLAlchemyError

# =========================================================================
# 🔒 TABAKA LA USALAMA: BRUTE FORCE & ANTI-INTRUDER PROTECTION (OWASP TOP 10)
# =========================================================================
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    HAS_LIMITER = True
except ImportError:
    HAS_LIMITER = False
    print("[!] Flask-Limiter not installed. Install with: pip install Flask-Limiter==3.5.0")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Create CTFd app
app = create_app()

# =========================================================================
# 🔒 RATE LIMITING CONFIGURATION - Anti Brute Force
# =========================================================================
if HAS_LIMITER:
    # Function to get real client IP behind Render proxy
    def get_real_ip():
        """Get real client IP address even behind reverse proxy (Render.com)"""
        # Check for Cloudflare/Render proxy headers
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        if request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        return request.remote_addr
    
    # Initialize limiter
    limiter = Limiter(
        key_func=get_real_ip,  # Use real IP, not proxy IP
        app=app,
        default_limits=["500 per day", "100 per hour"],
        storage_uri="memory://",  # Use memory storage (works on Render)
        strategy="fixed-window"  # Fixed window strategy
    )
    
    # 🛑 RATE LIMITS FOR LOGIN ENDPOINT
    # Allow only 5 login attempts per minute per IP
    @app.before_request
    def apply_rate_limits():
        if request.endpoint == 'auth.login' and request.method == 'POST':
            # Create a dynamic limit
            limit = limiter.shared_limit("5 per minute", scope="login")
            # Apply the limit
            limit(lambda: None)()
    
    # Custom error handler for rate limit exceeded
    @app.errorhandler(429)
    def rate_limit_handler(e):
        logger.warning(f"[!] Rate limit exceeded for IP: {get_real_ip()}")
        return jsonify({
            'error': 'Too many requests. Please try again later.',
            'message': 'Rate limit exceeded. Maximum 5 attempts per minute.'
        }), 429
    
    logger.info("[✓] Anti-Brute Force Layer (Flask-Limiter) activated successfully.")
    logger.info("[✓] Login rate limit: 5 attempts per minute per IP address")
else:
    logger.warning("[!] Flask-Limiter is NOT active. Add 'Flask-Limiter==3.5.0' to requirements.txt")

# =========================================================================
# 👑 ADMIN SETUP FUNCTION
# =========================================================================
def secure_admin_setup():
    """
    Usanidi salama wa akaunti ya ADMIN kwa CTFd platform.
    Inafanya kazi kwa usalama kwenye Render.com na hosting nyingine.
    """
    with app.app_context():
        try:
            # Get environment variables
            email = os.environ.get("ADMIN_EMAIL")
            username = os.environ.get("ADMIN_USERNAME")
            password = os.environ.get("ADMIN_PASS")
            
            # Validate required variables
            missing_vars = []
            if not email:
                missing_vars.append("ADMIN_EMAIL")
            if not username:
                missing_vars.append("ADMIN_USERNAME")
            if not password:
                missing_vars.append("ADMIN_PASS")
            
            if missing_vars:
                logger.error(f"[-] Missing required environment variables: {', '.join(missing_vars)}")
                logger.error("[-] Admin setup aborted for security reasons.")
                logger.info("[!] Please set these variables in your Render.com dashboard:")
                for var in missing_vars:
                    logger.info(f"    - {var}")
                return False
            
            # Validate password strength
            if len(password) < 8:
                logger.warning("[!] Password is weak (less than 8 characters). Consider using a stronger password.")
            
            # Check if admin already exists
            existing_admin = Users.query.filter(
                (Users.email == email) | (Users.type == "admin")
            ).first()
            
            if existing_admin:
                # Update existing admin
                existing_admin.type = "admin"
                existing_admin.name = username
                existing_admin.email = email
                existing_admin.password = hash_password(password)
                db.session.commit()
                logger.info(f"[✓] Admin account UPDATED securely: {username} ({email})")
                logger.info("[!] IMPORTANT: Use the new password you just set in environment variables.")
                return True
            else:
                # Create new admin
                new_admin = Users(
                    name=username,
                    email=email,
                    password=hash_password(password),
                    type="admin",
                    verified=True,
                    hidden=False
                )
                db.session.add(new_admin)
                db.session.commit()
                logger.info(f"[✓] New admin account CREATED securely: {username} ({email})")
                logger.info("[!] Save this password securely! It cannot be recovered if lost.")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"[-] Database error during admin setup: {str(e)}")
            db.session.rollback()
            return False
        except Exception as e:
            logger.error(f"[-] Unexpected error during admin setup: {str(e)}")
            return False

# =========================================================================
# 🔍 ADMIN UTILITY FUNCTIONS
# =========================================================================
def check_admin_exists():
    """Check if any admin account exists in the system"""
    with app.app_context():
        admin_count = Users.query.filter_by(type="admin").count()
        return admin_count > 0

def list_admins():
    """List all admin users (for debugging)"""
    with app.app_context():
        admins = Users.query.filter_by(type="admin").all()
        if admins:
            logger.info("[*] Current admin accounts:")
            for admin in admins:
                logger.info(f"    - {admin.name} ({admin.email})")
        return admins

def promote_to_admin(user_id=None, email=None, username=None):
    """
    Promote existing user to admin.
    Use this for adding additional admins.
    """
    with app.app_context():
        query = Users.query
        if user_id:
            user = query.filter_by(id=user_id).first()
        elif email:
            user = query.filter_by(email=email).first()
        elif username:
            user = query.filter_by(name=username).first()
        else:
            logger.error("[-] Please provide user_id, email, or username")
            return False
        
        if user:
            user.type = "admin"
            db.session.commit()
            logger.info(f"[✓] User {user.name} promoted to admin")
            return True
        else:
            logger.error(f"[-] User not found")
            return False

# =========================================================================
# 🚀 MAIN EXECUTION
# =========================================================================
if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("CTFd Admin Setup Script - Secure Configuration")
    logger.info("=" * 50)
    
    # Run admin setup
    success = secure_admin_setup()
    
    if success:
        logger.info("=" * 50)
        logger.info("[✓] Admin setup completed successfully!")
        logger.info("[✓] Your CTF platform is ready!")
        logger.info("=" * 50)
        
        # Optional: List all admins
        list_admins()
    else:
        logger.info("=" * 50)
        logger.error("[✗] Admin setup FAILED!")
        logger.info("=" * 50)
        logger.info("Troubleshooting tips:")
        logger.info("1. Check that database migrations are complete")
        logger.info("2. Verify environment variables are set in Render.com")
        logger.info("3. Check Render.com logs for more details")
        sys.exit(1)
