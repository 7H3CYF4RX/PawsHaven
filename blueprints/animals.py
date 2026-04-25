"""
Animals Blueprint — CRUD, Search, Medical Records, Import
Vulnerabilities: SQL injection (#22), IDOR (#6), XXE (#10), NoSQL injection (#36)
"""
import json
from flask import Blueprint, request, jsonify, g
from middleware.auth_middleware import require_auth, optional_auth
from utils.id_encoder import encode_id, decode_id
from utils import database as db

animals_bp = Blueprint('animals', __name__)


@animals_bp.route('/api/animals', methods=['GET'])
@optional_auth
def list_animals():
    """
    VULN #36: NoSQL injection (simulated) — filter param parsed as JSON query operators.
    """
    sandbox_id = g.sandbox_id if g.current_user else None
    filter_param = request.args.get('filter', '')

    if not sandbox_id:
        return jsonify({'animals': [], 'message': 'Login required to view animals.'})

    if filter_param:
        try:
            # VULN: Parses filter as JSON and builds SQL from it
            filters = json.loads(filter_param)
            where_clauses = []
            for key, value in filters.items():
                if isinstance(value, dict):
                    for op, val in value.items():
                        if op == '$ne':
                            where_clauses.append(f"{key} != '{val}'")
                        elif op == '$gt':
                            where_clauses.append(f"CAST({key} AS INTEGER) > {val}")
                        elif op == '$regex':
                            where_clauses.append(f"{key} LIKE '%{val}%'")
                        elif op == '$exists':
                            where_clauses.append(f"{key} IS NOT NULL")
                else:
                    where_clauses.append(f"{key} = '{value}'")

            where = " AND ".join(where_clauses) if where_clauses else "1=1"
            sql = f"SELECT * FROM animals WHERE {where}"
            animals = db.execute_raw(sandbox_id, sql)
        except Exception:
            animals = db.query_all(sandbox_id, "SELECT * FROM animals")
    else:
        animals = db.query_all(sandbox_id, "SELECT * FROM animals")

    # Add encoded IDs
    for a in animals:
        a['encoded_id'] = encode_id('animal', a['id'])

    return jsonify({'animals': animals, 'total': len(animals)})


@animals_bp.route('/api/animals/search', methods=['GET'])
@require_auth
def search_animals():
    """
    VULN #22: SQL Injection — raw string formatting in SQL query.
    """
    query = request.args.get('q', '')

    if not query:
        return jsonify({'results': [], 'message': 'Please provide a search query.'})

    # VULN: Raw string formatting — SQL injection!
    sql = f"SELECT * FROM animals WHERE name LIKE '%{query}%' OR species LIKE '%{query}%' OR breed LIKE '%{query}%' OR description LIKE '%{query}%'"

    try:
        results = db.execute_raw(g.sandbox_id, sql)
        for r in results:
            r['encoded_id'] = encode_id('animal', r['id'])
        return jsonify({'results': results, 'total': len(results), 'query': query})
    except Exception as e:
        # VULN #34: Verbose error messages
        return jsonify({'error': f'Search failed: {str(e)}', 'query': sql}), 500


@animals_bp.route('/api/animals/<encoded_id>', methods=['GET'])
@require_auth
def get_animal(encoded_id):
    """VULN #6: IDOR — access any animal via Base64 ID."""
    res_type, res_id = decode_id(encoded_id)
    if res_type != 'animal' or res_id is None:
        return jsonify({'error': 'Invalid animal ID.'}), 400

    animal = db.query_one(g.sandbox_id, "SELECT * FROM animals WHERE id = ?", [res_id])
    if not animal:
        return jsonify({'error': 'Animal not found.'}), 404

    animal['encoded_id'] = encode_id('animal', animal['id'])
    return jsonify({'animal': animal})


@animals_bp.route('/api/animals', methods=['POST'])
@require_auth
def create_animal():
    data = request.get_json()
    animal_id = db.execute_returning_id(g.sandbox_id,
        "INSERT INTO animals (name, species, breed, age, gender, description, status, added_by) VALUES (?, ?, ?, ?, ?, ?, 'available', ?)",
        [data.get('name',''), data.get('species',''), data.get('breed',''),
         data.get('age',''), data.get('gender',''), data.get('description',''),
         g.current_user['user_id']])

    return jsonify({'message': 'Animal added successfully!', 'id': encode_id('animal', animal_id)}), 201


@animals_bp.route('/api/animals/<encoded_id>', methods=['PUT'])
@require_auth
def update_animal(encoded_id):
    res_type, res_id = decode_id(encoded_id)
    if res_type != 'animal' or res_id is None:
        return jsonify({'error': 'Invalid animal ID.'}), 400

    data = request.get_json()
    for key, value in data.items():
        if key not in ('id', 'added_by', 'added_at'):
            try:
                db.execute(g.sandbox_id, f"UPDATE animals SET {key} = ? WHERE id = ?", [value, res_id])
            except:
                pass

    return jsonify({'message': 'Animal updated successfully.'})


@animals_bp.route('/api/animals/<encoded_id>', methods=['DELETE'])
@require_auth
def delete_animal(encoded_id):
    res_type, res_id = decode_id(encoded_id)
    if res_type != 'animal' or res_id is None:
        return jsonify({'error': 'Invalid animal ID.'}), 400
    db.execute(g.sandbox_id, "DELETE FROM animals WHERE id = ?", [res_id])
    return jsonify({'message': 'Animal removed.'})


@animals_bp.route('/api/animals/<encoded_id>/medical', methods=['GET'])
@require_auth
def get_medical_records(encoded_id):
    """VULN #6: IDOR — access any animal's medical records via Base64 ID."""
    res_type, res_id = decode_id(encoded_id)
    if res_type != 'animal' or res_id is None:
        return jsonify({'error': 'Invalid animal ID.'}), 400

    records = db.query_all(g.sandbox_id, "SELECT * FROM medical_records WHERE animal_id = ?", [res_id])
    animal = db.query_one(g.sandbox_id, "SELECT name FROM animals WHERE id = ?", [res_id])

    return jsonify({
        'animal_name': animal['name'] if animal else 'Unknown',
        'records': records,
        'total': len(records)
    })


@animals_bp.route('/api/animals/import', methods=['POST'])
@require_auth
def import_animals():
    """
    VULN #10: XXE — XML external entity injection.
    Parses XML with external entities enabled.
    """
    from lxml import etree

    xml_data = request.data
    if not xml_data:
        return jsonify({'error': 'No XML data provided. Send raw XML in request body.'}), 400

    try:
        # VULN: External entities enabled!
        parser = etree.XMLParser(resolve_entities=True, dtd_validation=False, no_network=False)
        tree = etree.fromstring(xml_data, parser)

        animals = []
        for animal_el in tree.findall('.//animal'):
            name = animal_el.findtext('name', '')
            species = animal_el.findtext('species', '')
            breed = animal_el.findtext('breed', '')
            description = animal_el.findtext('description', '')

            if name and species:
                animal_id = db.execute_returning_id(g.sandbox_id,
                    "INSERT INTO animals (name, species, breed, description, status, added_by) VALUES (?, ?, ?, ?, 'available', ?)",
                    [name, species, breed, description, g.current_user['user_id']])
                animals.append({'name': name, 'species': species, 'breed': breed, 'description': description})

        return jsonify({'message': f'{len(animals)} animals imported.', 'imported': animals})

    except etree.XMLSyntaxError as e:
        return jsonify({'error': f'XML parsing error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Import failed: {str(e)}'}), 500
