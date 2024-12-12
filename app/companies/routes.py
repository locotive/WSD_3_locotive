from flask import Blueprint, request, jsonify
from app.common.middleware import login_required
from app.database import get_db

companies_bp = Blueprint('companies', __name__)

@companies_bp.route('/', methods=['POST'])
@login_required
def create_company():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"message": "Company name is required"}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            "INSERT INTO companies (name, description) VALUES (%s, %s)",
            (data['name'], data.get('description', ''))
        )
        db.commit()
        return jsonify({"message": "Company created successfully", "company_id": cursor.lastrowid}), 201

    except Exception as e:
        db.rollback()
        return jsonify({"message": str(e)}), 500

    finally:
        cursor.close() 