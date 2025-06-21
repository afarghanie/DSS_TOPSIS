from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from werkzeug.utils import secure_filename
import json
from flasgger import Swagger

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///topsis.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['JWT_ALGORITHM'] = 'HS256'
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
bcrypt = Bcrypt(app)
CORS(app)
Swagger(app)

# JWT Error Handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'error': 'Token has expired',
        'message': 'The token has expired. Please log in again.'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'error': 'Invalid token',
        'message': 'Signature verification failed. Please log in again.'
    }), 422

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        'error': 'Authorization required',
        'message': 'Request does not contain an access token.'
    }), 401

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    theme_preference = db.Column(db.String(10), default='light')
    projects = db.relationship('Project', backref='user', lazy=True)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow)
    criteria = db.relationship('Criterion', backref='project', lazy=True, cascade='all, delete-orphan')
    alternatives = db.relationship('Alternative', backref='project', lazy=True, cascade='all, delete-orphan')

class Criterion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    criterion_type = db.Column(db.String(10), nullable=False)  # 'benefit' or 'cost'
    weight = db.Column(db.Float, nullable=False)
    values = db.relationship('AlternativeCriterionValue', backref='criterion', lazy=True, cascade='all, delete-orphan')

class Alternative(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    values = db.relationship('AlternativeCriterionValue', backref='alternative', lazy=True, cascade='all, delete-orphan')

class AlternativeCriterionValue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    alternative_id = db.Column(db.Integer, db.ForeignKey('alternative.id'), nullable=False)
    criterion_id = db.Column(db.Integer, db.ForeignKey('criterion.id'), nullable=False)
    value = db.Column(db.Float, nullable=False)

# TOPSIS Calculation Functions
def normalize_matrix(matrix):
    """Normalize the decision matrix"""
    denominator = np.sqrt(np.sum(matrix**2, axis=0))
    return matrix / denominator

def calculate_weighted_matrix(normalized_matrix, weights):
    """Calculate weighted normalized matrix"""
    return normalized_matrix * weights

def find_ideal_solutions(weighted_matrix, criteria_types):
    """Find positive and negative ideal solutions"""
    A_plus = np.zeros(weighted_matrix.shape[1])
    A_minus = np.zeros(weighted_matrix.shape[1])
    
    for j in range(weighted_matrix.shape[1]):
        if criteria_types[j] == 'benefit':
            A_plus[j] = weighted_matrix[:, j].max()
            A_minus[j] = weighted_matrix[:, j].min()
        else:  # cost
            A_plus[j] = weighted_matrix[:, j].min()
            A_minus[j] = weighted_matrix[:, j].max()
    
    return A_plus, A_minus

def calculate_distances(weighted_matrix, A_plus, A_minus):
    """Calculate distances to ideal solutions"""
    D_plus = np.sqrt(np.sum((weighted_matrix - A_plus)**2, axis=1))
    D_minus = np.sqrt(np.sum((weighted_matrix - A_minus)**2, axis=1))
    return D_plus, D_minus

def calculate_preference_values(D_plus, D_minus):
    """Calculate preference values"""
    V = D_minus / (D_plus + D_minus)
    return np.nan_to_num(V, nan=0.0)

def perform_topsis_calculation(alternatives_data, criteria_weights, criteria_types):
    """Perform complete TOPSIS calculation"""
    # Convert to numpy arrays
    matrix = np.array(alternatives_data)
    weights = np.array(criteria_weights)
    
    # Step 1: Normalize matrix
    normalized_matrix = normalize_matrix(matrix)
    
    # Step 2: Calculate weighted matrix
    weighted_matrix = calculate_weighted_matrix(normalized_matrix, weights)
    
    # Step 3: Find ideal solutions
    A_plus, A_minus = find_ideal_solutions(weighted_matrix, criteria_types)
    
    # Step 4: Calculate distances
    D_plus, D_minus = calculate_distances(weighted_matrix, A_plus, A_minus)
    
    # Step 5: Calculate preference values
    V = calculate_preference_values(D_plus, D_minus)
    
    return {
        'normalized_matrix': normalized_matrix.tolist(),
        'weighted_matrix': weighted_matrix.tolist(),
        'A_plus': A_plus.tolist(),
        'A_minus': A_minus.tolist(),
        'D_plus': D_plus.tolist(),
        'D_minus': D_minus.tolist(),
        'preference_values': V.tolist()
    }

# Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(email=email, password=hashed_password)
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'theme_preference': user.theme_preference
            }
        }), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

# Project Management Routes
@app.route('/api/projects', methods=['GET'])
@jwt_required()
def get_projects():
    user_id = get_jwt_identity()
    projects = Project.query.filter_by(user_id=user_id).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'creation_date': p.creation_date.isoformat(),
        'last_modified': p.last_modified.isoformat()
    } for p in projects]), 200

@app.route('/api/projects', methods=['POST'])
@jwt_required()
def create_project():
    user_id = get_jwt_identity()
    data = request.get_json()
    name = data.get('name')
    
    if not name:
        return jsonify({'error': 'Project name is required'}), 400
    
    project = Project(user_id=user_id, name=name)
    db.session.add(project)
    db.session.commit()
    
    return jsonify({
        'id': project.id,
        'name': project.name,
        'creation_date': project.creation_date.isoformat(),
        'last_modified': project.last_modified.isoformat()
    }), 201

@app.route('/api/projects/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    user_id = get_jwt_identity()
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    criteria = [{
        'id': c.id,
        'name': c.name,
        'criterion_type': c.criterion_type,
        'weight': c.weight
    } for c in project.criteria]
    
    alternatives = [{
        'id': a.id,
        'name': a.name,
        'values': [{
            'criterion_id': v.criterion_id,
            'value': v.value
        } for v in a.values]
    } for a in project.alternatives]
    
    return jsonify({
        'id': project.id,
        'name': project.name,
        'criteria': criteria,
        'alternatives': alternatives
    }), 200

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    user_id = get_jwt_identity()
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    # Delete the project (cascade will handle related records)
    db.session.delete(project)
    db.session.commit()
    
    return jsonify({'message': 'Project deleted successfully'}), 200

@app.route('/api/projects/<int:project_id>/criteria', methods=['POST'])
@jwt_required()
def add_criterion(project_id):
    user_id = get_jwt_identity()
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    data = request.get_json()
    name = data.get('name')
    criterion_type = data.get('criterion_type')
    weight = data.get('weight')
    
    if not all([name, criterion_type, weight is not None]):
        return jsonify({'error': 'Name, criterion_type, and weight are required'}), 400
    
    criterion = Criterion(
        project_id=project_id,
        name=name,
        criterion_type=criterion_type,
        weight=weight
    )
    db.session.add(criterion)
    project.last_modified = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'id': criterion.id,
        'name': criterion.name,
        'criterion_type': criterion.criterion_type,
        'weight': criterion.weight
    }), 201

@app.route('/api/projects/<int:project_id>/criteria/<int:criterion_id>', methods=['DELETE'])
@jwt_required()
def delete_criterion(project_id, criterion_id):
    user_id = get_jwt_identity()
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    criterion = Criterion.query.filter_by(id=criterion_id, project_id=project_id).first()
    
    if not criterion:
        return jsonify({'error': 'Criterion not found'}), 404
    
    # Delete the criterion (cascade will handle related values)
    db.session.delete(criterion)
    project.last_modified = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': 'Criterion deleted successfully'}), 200

@app.route('/api/projects/<int:project_id>/alternatives', methods=['POST'])
@jwt_required()
def add_alternative(project_id):
    user_id = get_jwt_identity()
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    data = request.get_json()
    name = data.get('name')
    values = data.get('values', [])
    
    if not name:
        return jsonify({'error': 'Alternative name is required'}), 400
    
    alternative = Alternative(project_id=project_id, name=name)
    db.session.add(alternative)
    db.session.flush()  # Get the ID
    
    # Add values
    for value_data in values:
        value = AlternativeCriterionValue(
            alternative_id=alternative.id,
            criterion_id=value_data['criterion_id'],
            value=value_data['value']
        )
        db.session.add(value)
    
    project.last_modified = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'id': alternative.id,
        'name': alternative.name,
        'values': values
    }), 201

@app.route('/api/projects/<int:project_id>/alternatives/<int:alternative_id>', methods=['DELETE'])
@jwt_required()
def delete_alternative(project_id, alternative_id):
    user_id = get_jwt_identity()
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    alternative = Alternative.query.filter_by(id=alternative_id, project_id=project_id).first()
    
    if not alternative:
        return jsonify({'error': 'Alternative not found'}), 404
    
    # Delete the alternative (cascade will handle related values)
    db.session.delete(alternative)
    project.last_modified = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': 'Alternative deleted successfully'}), 200

@app.route('/api/projects/<int:project_id>/calculate', methods=['POST'])
@jwt_required()
def calculate_topsis(project_id):
    user_id = get_jwt_identity()
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    if not project.criteria or not project.alternatives:
        return jsonify({'error': 'Project must have criteria and alternatives'}), 400
    
    # Prepare data for calculation
    criteria_weights = [c.weight for c in project.criteria]
    criteria_types = [c.criterion_type for c in project.criteria]
    
    # Create alternatives data matrix
    alternatives_data = []
    alternative_names = []
    
    for alt in project.alternatives:
        alternative_names.append(alt.name)
        row = []
        for crit in project.criteria:
            value = next((v.value for v in alt.values if v.criterion_id == crit.id), 0)
            row.append(value)
        alternatives_data.append(row)
    
    # Perform TOPSIS calculation
    results = perform_topsis_calculation(alternatives_data, criteria_weights, criteria_types)
    
    # Add alternative names to results
    results['alternative_names'] = alternative_names
    results['criteria_names'] = [c.name for c in project.criteria]
    
    # Create ranking
    preference_values = results['preference_values']
    ranking = sorted(enumerate(preference_values), key=lambda x: x[1], reverse=True)
    results['ranking'] = [{'rank': i+1, 'alternative_index': rank[0], 'alternative_name': alternative_names[rank[0]], 'value': rank[1]} for i, rank in enumerate(ranking)]
    
    return jsonify(results), 200

@app.route('/api/upload-csv', methods=['POST'])
@jwt_required()
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Read CSV file
        df = pd.read_csv(file)
        
        # Return preview data
        return jsonify({
            'columns': df.columns.tolist(),
            'preview': df.head(10).to_dict('records'),
            'total_rows': len(df)
        }), 200
    except Exception as e:
        return jsonify({'error': f'Error reading CSV file: {str(e)}'}), 400

@app.route('/api/import-csv', methods=['POST'])
@jwt_required()
def import_csv():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    project_name = data.get('project_name')
    csv_data = data.get('csv_data')
    column_mapping = data.get('column_mapping')
    criteria_config = data.get('criteria_config')
    
    if not all([project_name, csv_data, column_mapping, criteria_config]):
        return jsonify({'error': 'Missing required data'}), 400
    
    try:
        # Create new project
        project = Project(user_id=user_id, name=project_name)
        db.session.add(project)
        db.session.flush()
        
        # Create criteria
        criteria_map = {}
        for crit_config in criteria_config:
            criterion = Criterion(
                project_id=project.id,
                name=crit_config['name'],
                criterion_type=crit_config['type'],
                weight=crit_config['weight']
            )
            db.session.add(criterion)
            db.session.flush()
            criteria_map[crit_config['name']] = criterion.id
        
        # Create alternatives and values
        for row in csv_data:
            alt_name = row[column_mapping['alternative_name']]
            alternative = Alternative(project_id=project.id, name=alt_name)
            db.session.add(alternative)
            db.session.flush()
            
            # Add values for each criterion
            for crit_config in criteria_config:
                crit_name = crit_config['name']
                if crit_name in column_mapping:
                    value = float(row[column_mapping[crit_name]])
                    alt_value = AlternativeCriterionValue(
                        alternative_id=alternative.id,
                        criterion_id=criteria_map[crit_name],
                        value=value
                    )
                    db.session.add(alt_value)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Data imported successfully',
            'project_id': project.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error importing data: {str(e)}'}), 400

@app.route('/api/user/theme', methods=['PUT'])
@jwt_required()
def update_theme():
    user_id = get_jwt_identity()
    data = request.get_json()
    theme = data.get('theme')
    
    if theme not in ['light', 'dark']:
        return jsonify({'error': 'Invalid theme'}), 400
    
    user = User.query.get(user_id)
    user.theme_preference = theme
    db.session.commit()
    
    return jsonify({'message': 'Theme updated successfully'}), 200

@app.route('/api/user', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({
        'id': user.id,
        'email': user.email,
        'theme_preference': user.theme_preference
    }), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000) 