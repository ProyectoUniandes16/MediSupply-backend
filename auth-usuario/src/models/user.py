from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt

db = SQLAlchemy()

class User(db.Model):
    """
    Modelo de usuario para autenticación
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    # rol del usuario: 'vendedor', 'gerente' o 'cliente'
    rol = db.Column(db.String(20), default='cliente', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    ALLOWED_ROLES = ('vendedor', 'gerente', 'cliente')

    def __init__(self, email, password, nombre, apellido, rol='cliente'):
        self.email = email.lower()
        self.password_hash = self._hash_password(password)
        self.nombre = nombre
        self.apellido = apellido
        rol_value = (rol or 'cliente').lower()
        if rol_value not in self.ALLOWED_ROLES:
            raise ValueError(f"Rol inválido: {rol}. Roles permitidos: {', '.join(self.ALLOWED_ROLES)}")
        self.rol = rol_value
    
    def _hash_password(self, password):
        """Hashea la contraseña usando bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password):
        """Verifica si la contraseña es correcta"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def to_dict(self):
        """Convierte el usuario a diccionario (sin contraseña)"""
        return {
            'id': self.id,
            'email': self.email,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'rol': self.rol,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def find_by_email(cls, email):
        """Busca un usuario por email"""
        return cls.query.filter_by(email=email.lower()).first()
    
    @classmethod
    def find_by_id(cls, user_id):
        """Busca un usuario por ID"""
        return cls.query.get(user_id)
    
    def save(self):
        """Guarda el usuario en la base de datos"""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """Elimina el usuario de la base de datos"""
        db.session.delete(self)
        db.session.commit()
    
    def __repr__(self):
        return f'<User {self.email}>'
