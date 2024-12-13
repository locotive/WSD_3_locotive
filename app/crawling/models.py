from datetime import datetime
from app.database import db

class Company(db.Model):
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    jobs = db.relationship('Job', backref='company', lazy=True)

class Job(db.Model):
    __tablename__ = 'job_postings'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    link = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(100))
    experience = db.Column(db.String(100))
    education = db.Column(db.String(100))
    employment_type = db.Column(db.String(100))
    deadline = db.Column(db.String(100))
    sector = db.Column(db.String(200))
    salary = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'company': self.company.name,
            'title': self.title,
            'link': self.link,
            'location': self.location,
            'experience': self.experience,
            'education': self.education,
            'employment_type': self.employment_type,
            'deadline': self.deadline,
            'sector': self.sector,
            'salary': self.salary,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }