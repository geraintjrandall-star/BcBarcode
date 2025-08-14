from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from extensions import db, socketio
from models import ScannerStatus, ConsumptionJournalEntry, OutputJournalEntry, User
from datetime import datetime
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

auth = HTTPBasicAuth()

# For demo, use a single user-password dictionary with hashed password:
users = {
    "admin": generate_password_hash("system165")
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username
    return None

bp = Blueprint('main', __name__)

# --- Scanner Status and related routes ---

@bp.route('/')
def index():
    scanners = ScannerStatus.query.order_by(ScannerStatus.address).all()
    users = {user.user_number: user.name for user in User.query.all()}

    # Attach user name to each scanner object (dynamically)
    for scanner in scanners:
        scanner.user_name = users.get(scanner.user, "Unknown User" if scanner.user else "-")

    return render_template('index.html', scanners=scanners)

@bp.route('/scan', methods=['POST'])
def scan():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON received"}), 400

    address = data.get('address')
    mode = data.get('mode')
    value = data.get('value')

    if not address or mode is None or value is None:
        return jsonify({"error": "Missing fields"}), 400

    scanner = ScannerStatus.query.get(address)
    now = datetime.utcnow()

    if not scanner:
        scanner = ScannerStatus(address=address)
        db.session.add(scanner)

    def has_required_fields(sc):
        return all([
            sc.production_order,
            sc.line_no is not None,
            sc.item_no,
            sc.operation
        ])

    if mode == 0:
        if scanner.mode == "Pause":
            scanner.mode = "Production"
            scanner.time_mode_started = now

        if scanner.production_order and scanner.line_no and scanner.location:
            consumption_entry = ConsumptionJournalEntry(
                production_order_no=scanner.production_order,
                line_no=scanner.line_no,
                item_no=value,
                bin_code=scanner.location,
                quantity=1,
                posting_date=now.date()
            )
            db.session.add(consumption_entry)

    elif mode == 1:
        scanner.user = value

    elif mode == 2:
        print(value)
        po, item_no, line_no = value.split('%')
        if scanner.production_order != po or scanner.item_no != item_no or scanner.line_no != int(line_no):
            if has_required_fields(scanner):
                runtime_minutes = int((now - scanner.time_mode_started).total_seconds() / 60) if scanner.time_mode_started else 0
                output_entry = OutputJournalEntry(
                    production_order_no=scanner.production_order,
                    item_no=scanner.item_no,
                    line_no=scanner.line_no,
                    operation_no=scanner.operation,
                    user=scanner.user,
                    runtime_minutes=runtime_minutes,
                    output_quantity=0,
                    finished=False
                )
                db.session.add(output_entry)

            scanner.production_order = po
            scanner.item_no = item_no
            scanner.line_no = int(line_no)
            scanner.mode = "Production"
            scanner.location = "SHOP FLOOR"
            scanner.time_mode_started = now
        if scanner.mode == "Pause":
            scanner.mode = "Production"
            scanner.time_mode_started = now
        if scanner.mode == "Stock":
            scanner.mode = "Production"
            scanner.time_mode_started = now
        scanner.location = "SHOP FLOOR"

    elif mode == 3:
        if scanner.operation != value:
            if has_required_fields(scanner):
                runtime_minutes = int((now - scanner.time_mode_started).total_seconds() / 60) if scanner.time_mode_started else 0
                output_entry = OutputJournalEntry(
                    production_order_no=scanner.production_order,
                    item_no=scanner.item_no,
                    line_no=scanner.line_no,
                    operation_no=scanner.operation,
                    user=scanner.user,
                    runtime_minutes=runtime_minutes,
                    output_quantity=0,
                    finished=False
                )
                db.session.add(output_entry)
            scanner.operation = value
        if scanner.mode == "Pause":
            scanner.mode = "Production"
            scanner.time_mode_started = now
        scanner.location = "SHOP FLOOR"

    elif mode == 4:
        if scanner.mode == "Pause":
            scanner.mode = "Production"
            scanner.time_mode_started = now
        scanner.mode = "Stock"
        scanner.location = value

    elif mode == 5:
        if scanner.mode == "Pause":
            scanner.mode = "Production"
            scanner.time_mode_started = now
        scanner.mode = "Production"
        if scanner.production_order and scanner.line_no and scanner.item_no:
            consumption_entry = ConsumptionJournalEntry(
                production_order_no=scanner.production_order,
                line_no=scanner.line_no,
                item_no=value,
                bin_code="COPPER",
                quantity=1,
                posting_date=now.date()
            )
            db.session.add(consumption_entry)

    elif mode == 6:
        if has_required_fields(scanner):
            runtime_minutes = int((now - scanner.time_mode_started).total_seconds() / 60) if scanner.time_mode_started else 0
            output_entry = OutputJournalEntry(
                production_order_no=scanner.production_order,
                item_no=scanner.item_no,
                line_no=scanner.line_no,
                operation_no=scanner.operation,
                user=scanner.user,
                runtime_minutes=runtime_minutes,
                output_quantity=0,
                finished=False
            )
            db.session.add(output_entry)
        scanner.mode = "Pause"
        scanner.time_mode_started = now

    elif mode == 7:
        if has_required_fields(scanner):
            runtime_minutes = int((now - scanner.time_mode_started).total_seconds() / 60) if scanner.time_mode_started else 0
            output_entry = OutputJournalEntry(
                production_order_no=scanner.production_order,
                item_no=scanner.item_no,
                line_no=scanner.line_no,
                operation_no=scanner.operation,
                user=scanner.user,
                runtime_minutes=runtime_minutes,
                output_quantity=1,
                finished=True
            )
            db.session.add(output_entry)
        scanner.mode = "Pause"
        scanner.production_order  = ""
        scanner.item_no = ""
        scanner.operation = ""
        scanner.line_no = ""
        scanner.time_mode_started = now

    scanner.last_seen = now

    db.session.commit()
    socketio.emit('new_scan', {'address': address})

    return jsonify({"status": "OK", "address": address})


@bp.route('/consumption')
def view_consumption():
    entries = ConsumptionJournalEntry.query.order_by(ConsumptionJournalEntry.id.desc()).all()
    return render_template('consumption.html', entries=entries)


@bp.route('/output')
def view_output():
    entries = OutputJournalEntry.query.order_by(OutputJournalEntry.id.desc()).all()
    return render_template('output.html', entries=entries)


# --- User Management Routes ---

@bp.route('/users')
def users_list():
    users = User.query.order_by(User.user_number).all()
    return render_template('users.html', users=users)

@bp.route('/users/add', methods=['GET', 'POST'])
def users_add():
    if request.method == 'POST':
        user_number = request.form.get('user_number')
        name = request.form.get('name')
        if not user_number or not name:
            flash('User Number and Name are required.', 'error')
            return redirect(url_for('main.users_add'))
        existing = User.query.get(user_number)
        if existing:
            flash('User Number already exists.', 'error')
            return redirect(url_for('main.users_add'))

        new_user = User(user_number=user_number, name=name)
        db.session.add(new_user)
        db.session.commit()
        flash('User added successfully.', 'success')
        return redirect(url_for('main.users_list'))
    return render_template('user_form.html', action='Add', user=None)

@bp.route('/users/edit/<user_number>', methods=['GET', 'POST'])
def users_edit(user_number):
    user = User.query.get_or_404(user_number)
    if request.method == 'POST':
        name = request.form.get('name')
        if not name:
            flash('Name is required.', 'error')
            return redirect(url_for('main.users_edit', user_number=user_number))
        user.name = name
        db.session.commit()
        flash('User updated successfully.', 'success')
        return redirect(url_for('main.users_list'))
    return render_template('user_form.html', action='Edit', user=user)

@bp.route('/users/delete/<user_number>', methods=['POST'])
def users_delete(user_number):
    user = User.query.get_or_404(user_number)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted.', 'success')
    return redirect(url_for('main.users_list'))

@bp.route('/scanners')
@auth.login_required
def view_scanners():
    scanners = ScannerStatus.query.order_by(ScannerStatus.address).all()
    return render_template('scanners.html', scanners=scanners)

@bp.route('/scanners/delete/<string:address>', methods=['POST'])
@auth.login_required
def delete_scanner(address):
    scanner = ScannerStatus.query.get(address)
    if scanner:
        db.session.delete(scanner)
        db.session.commit()
        return jsonify({"status": "success", "message": f"Scanner {address} deleted."})
    else:
        return jsonify({"status": "error", "message": "Scanner not found."}), 404
