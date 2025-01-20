from datetime import datetime
import json
from flask_login import UserMixin
from app import db, login_manager

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Vztahy
    farms = db.relationship('Farm', backref='owner', lazy=True)
    
    def __repr__(self):
        return f'<User {self.email}>'

class Farm(db.Model):
    """Model pro farmu"""
    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Převede farmu na slovník"""
        return {
            'id': self.id,
            'farm_id': self.farm_id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None
        }

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.Text)
    original_description = db.Column(db.Text)
    short_description = db.Column(db.Text)
    long_description = db.Column(db.Text)
    image_path = db.Column(db.String(200))
    price = db.Column(db.Float)
    unit = db.Column(db.String(20))
    stock = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    is_confirmed = db.Column(db.Boolean, default=False)
    product_metadata = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Vztahy
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'), nullable=False)
    
    @property
    def metadata_dict(self):
        """Převede JSON string na slovník"""
        if self.product_metadata:
            return json.loads(self.product_metadata)
        return {}
    
    @metadata_dict.setter
    def metadata_dict(self, value):
        """Uloží slovník jako JSON string"""
        if value is None:
            self.product_metadata = None
        else:
            self.product_metadata = json.dumps(value)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sku': self.sku,
            'name': self.name,
            'ingredients': self.ingredients,
            'original_description': self.original_description,
            'short_description': self.short_description,
            'long_description': self.long_description,
            'image_path': self.image_path,
            'price': self.price,
            'unit': self.unit,
            'stock': self.stock,
            'is_active': self.is_active,
            'is_confirmed': self.is_confirmed,
            'metadata': self.metadata_dict,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
            'farm_id': self.farm_id
        }
    
    def __repr__(self):
        return f'<Product {self.sku}: {self.name}>' 