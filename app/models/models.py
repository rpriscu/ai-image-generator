from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import enum

db = SQLAlchemy()

class User(db.Model, UserMixin):
    """User model for Google-authenticated users"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255))
    picture = db.Column(db.String(255))  # Profile picture URL
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    
    usage = db.relationship("MonthlyUsage", backref="user", lazy=True, cascade="all, delete-orphan")
    assets = db.relationship("Asset", backref="user", lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<User {self.email}>'

    @staticmethod
    def get_or_create(email, name=None, picture=None):
        """Get existing user or create a new one"""
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, name=name, picture=picture)
            db.session.add(user)
            db.session.commit()
        return user

class MonthlyUsage(db.Model):
    """Tracks monthly usage per user"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # Format: "2025-05"
    request_count = db.Column(db.Integer, default=0)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'month', name='_user_month_uc'),)
    
    def __repr__(self):
        return f'<MonthlyUsage {self.user.email} {self.month}: {self.request_count}>'

class AssetType(enum.Enum):
    """Types of assets that can be stored"""
    image = "image"
    video = "video" 
    animation = "animation"

class ShortUrl(db.Model):
    """Stores the mapping between short URL keys and original URLs"""
    id = db.Column(db.Integer, primary_key=True)
    short_key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    original_url = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ShortUrl {self.short_key}: {self.original_url[:30]}...>' 

class Asset(db.Model):
    """Asset model for storing generated content"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    file_url = db.Column(db.String(2048), nullable=False)  # Increased from 255 to 2048 characters
    thumbnail_url = db.Column(db.String(512), nullable=True)  # For video thumbnails
    type = db.Column(db.Enum(AssetType), nullable=False, default=AssetType.image)
    prompt = db.Column(db.Text)
    model = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Asset {self.id} by {self.user_id}: {self.type.value}>'
    
    def to_dict(self):
        """Convert the asset to a dictionary for API responses"""
        return {
            'id': self.id,
            'file_url': self.file_url,
            'thumbnail_url': self.thumbnail_url,
            'type': self.type.value,
            'prompt': self.prompt,
            'model': self.model,
            'created_at': self.created_at.isoformat()
        }

class Admin(db.Model):
    """Admin user model with username/password authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Admin {self.username}>'
    
    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check the password against the hash"""
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def create_admin(username, password):
        """Create a new admin user"""
        admin = Admin(username=username)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        return admin 