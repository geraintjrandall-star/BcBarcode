from extensions import db  # import the single shared db instance

class ScannerStatus(db.Model):
    __tablename__ = 'scanner_status'
    address = db.Column(db.String, primary_key=True)
    user = db.Column(db.String, nullable=True)
    production_order = db.Column(db.String, nullable=True)
    operation = db.Column(db.String, nullable=True)
    mode = db.Column(db.String, nullable=True)  # e.g. "Pause", "Production", "Stock"
    time_mode_started = db.Column(db.DateTime, nullable=True)
    location = db.Column(db.String, nullable=True)
    line_no = db.Column(db.Integer, nullable=True)
    item_no = db.Column(db.String, nullable=True)
    last_seen = db.Column(db.DateTime, nullable=True)

class ConsumptionJournalEntry(db.Model):
    __tablename__ = 'consumption_journal'
    id = db.Column(db.Integer, primary_key=True)
    production_order_no = db.Column(db.String, nullable=False)
    line_no = db.Column(db.Integer, nullable=False)
    item_no = db.Column(db.String, nullable=False)
    bin_code = db.Column(db.String, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    posting_date = db.Column(db.Date, nullable=False)

class OutputJournalEntry(db.Model):
    __tablename__ = 'output_journal'
    id = db.Column(db.Integer, primary_key=True)
    production_order_no = db.Column(db.String, nullable=False)
    item_no = db.Column(db.String, nullable=False)
    line_no = db.Column(db.Integer, nullable=False)
    operation_no = db.Column(db.String, nullable=True)
    user = db.Column(db.String, nullable=True)
    runtime_minutes = db.Column(db.Integer, nullable=False)
    output_quantity = db.Column(db.Integer, nullable=False)
    finished = db.Column(db.Boolean, nullable=False)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    user_number = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String, nullable=False)
