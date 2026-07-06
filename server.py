from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import csv
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
BOOKS_CSV = os.path.join(DATA_DIR, 'books.csv')
LOANS_CSV = os.path.join(DATA_DIR, 'loans.csv')

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# ==================== CSV HELPERS ====================

def read_csv(file_path, headers=None):
    """Read CSV file and return list of dictionaries"""
    if not os.path.exists(file_path):
        return []
    
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric fields
                for key, value in row.items():
                    if key in ['id', 'number'] and value:
                        try:
                            row[key] = int(value)
                        except ValueError:
                            row[key] = 0
                    elif key in ['available'] and value:
                        try:
                            row[key] = int(value)
                        except ValueError:
                            row[key] = 0
                data.append(row)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []
    return data

def write_csv(file_path, data, headers):
    """Write list of dictionaries to CSV file"""
    try:
        with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
            if data and len(data) > 0:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                for row in data:
                    # Ensure all headers exist in row
                    clean_row = {h: row.get(h, '') for h in headers}
                    writer.writerow(clean_row)
            else:
                # Write empty file with headers
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
        return True
    except Exception as e:
        print(f"Error writing {file_path}: {e}")
        return False

# ==================== INITIALIZE CSV FILES ====================

def migrate_csv_headers(file_path, required_headers, defaults=None):
    """If a CSV file already exists but is missing one of the required columns
    (e.g. an older books.csv/loans.csv you copy in before starting the server,
    made before the 'کتابخانه'/'library' column existed), add the missing
    column(s) with a default value and rewrite the file. Any extra columns the
    file already has that aren't part of our schema are kept, appended at the end.
    Does nothing if the file is already up to date."""
    defaults = defaults or {}
    if not os.path.exists(file_path):
        return
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            existing_headers = reader.fieldnames or []
            rows = list(reader)
    except Exception as e:
        print(f"⚠️ Could not inspect {file_path} for migration: {e}")
        return

    missing = [h for h in required_headers if h not in existing_headers]
    if not missing:
        return  # already up to date, nothing to do

    final_headers = required_headers + [h for h in existing_headers if h not in required_headers]
    for row in rows:
        for h in missing:
            row[h] = defaults.get(h, '')
    write_csv(file_path, rows, final_headers)
    print(f"🔧 Updated {os.path.basename(file_path)}: added missing column(s) {', '.join(missing)}")

def init_csv_files():
    """Create default CSV files if they don't exist, or migrate them if they
    exist but were made before the multi-library feature (missing column)."""
    # Books CSV headers
    # 'library' tags which collection a book belongs to, e.g. 'اصلی' or 'دانشکده برق'
    books_headers = ['id', 'name', 'author', 'code', 'number', 'library']
    
    if not os.path.exists(BOOKS_CSV):
        # Create with sample data
        sample_books = [
            {'id': 1, 'name': 'پرسشهاي عجيب و پاسخ هاي عجيب تر', 'author': 'نوشته ا. جي . آرمسترانگ', 'code': 'AC', 'number': 6, 'library': 'اصلی'},
            {'id': 2, 'name': 'ترجمه و گلچینی از کشکول شیخ بهایی (م)', 'author': 'نجفی یزدی', 'code': 'AC۱۰۵', 'number': 1, 'library': 'اصلی'},
            {'id': 3, 'name': 'کشکول طبسی(مرجع)', 'author': 'سید علنیقی طبسی حائری', 'code': 'AC۱۲۷', 'number': 1, 'library': 'اصلی'}
        ]
        write_csv(BOOKS_CSV, sample_books, books_headers)
        print(f"✅ Created {BOOKS_CSV} with sample data")
    else:
        migrate_csv_headers(BOOKS_CSV, books_headers, {'library': 'اصلی'})
    
    # Loans CSV headers
    loans_headers = ['id', 'نشان', 'نام', 'درجه', 'قسمت', 'شماره پرسنلی/دانشجویی', 
                     'شماره تماس', 'عنوان کتاب', 'کتابخانه', 'کد کنگره', 'تاریخ امانت', 'تاریخ بازگردانی']
    
    if not os.path.exists(LOANS_CSV):
        # Create with sample data
        sample_loans = [
            {'id': 1, 'نشان': 'کریمی', 'نام': 'محمدحسین', 'درجه': 'سال یکم', 
             'قسمت': 'گروهان توکلی', 'شماره پرسنلی/دانشجویی': '840331465', 
             'شماره تماس': '9912946824', 'عنوان کتاب': 'هنر بازی استراتژیک', 'کتابخانه': 'اصلی',
             'کد کنگره': '', 'تاریخ امانت': '1404/07/02', 'تاریخ بازگردانی': ''},
            {'id': 2, 'نشان': 'نوری شعرباف', 'نام': 'امیرعباس', 'درجه': 'سال دوم', 
             'قسمت': 'گروهان شهید توکلی', 'شماره پرسنلی/دانشجویی': '840331271', 
             'شماره تماس': '9931187440', 'عنوان کتاب': 'طراحی دیجیتال (مدار منطقی) مانو', 'کتابخانه': 'اصلی',
             'کد کنگره': 'tk7888', 'تاریخ امانت': '1404/08/12', 'تاریخ بازگردانی': '1404/08/25'}
        ]
        write_csv(LOANS_CSV, sample_loans, loans_headers)
        print(f"✅ Created {LOANS_CSV} with sample data")
    else:
        migrate_csv_headers(LOANS_CSV, loans_headers, {'کتابخانه': 'اصلی'})

# Initialize CSV files
init_csv_files()

# ==================== API ROUTES ====================

@app.route('/')
def index():
    """Serve the HTML page"""
    html_file = os.path.join(os.path.dirname(__file__), 'index.html')
    if os.path.exists(html_file):
        return send_file(html_file)
    else:
        return jsonify({
            'status': 'error',
            'message': 'HTML file not found. Please place "index.html" in the same directory as server.py'
        }), 404

@app.route('/api/books', methods=['GET'])
def get_books():
    """Get all books from CSV"""
    books = read_csv(BOOKS_CSV)
    return jsonify(books)

@app.route('/api/books', methods=['POST'])
def save_books():
    """Save books to CSV"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        # Validate data
        if not isinstance(data, list):
            return jsonify({'success': False, 'message': 'Data must be a list'}), 400
        
        headers = ['id', 'name', 'author', 'code', 'number', 'library']
        success = write_csv(BOOKS_CSV, data, headers)
        
        if success:
            return jsonify({
                'success': True, 
                'message': f'Successfully saved {len(data)} books',
                'count': len(data)
            })
        else:
            return jsonify({'success': False, 'message': 'Error writing to CSV'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/loans', methods=['GET'])
def get_loans():
    """Get all loans from CSV"""
    loans = read_csv(LOANS_CSV)
    return jsonify(loans)

@app.route('/api/loans', methods=['POST'])
def save_loans():
    """Save loans to CSV"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        if not isinstance(data, list):
            return jsonify({'success': False, 'message': 'Data must be a list'}), 400
        
        headers = ['id', 'نشان', 'نام', 'درجه', 'قسمت', 'شماره پرسنلی/دانشجویی', 
                   'شماره تماس', 'عنوان کتاب', 'کتابخانه', 'کد کنگره', 'تاریخ امانت', 'تاریخ بازگردانی']
        success = write_csv(LOANS_CSV, data, headers)
        
        if success:
            return jsonify({
                'success': True, 
                'message': f'Successfully saved {len(data)} loans',
                'count': len(data)
            })
        else:
            return jsonify({'success': False, 'message': 'Error writing to CSV'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/import/csv', methods=['POST'])
def import_csv():
    """Import data from uploaded CSV files"""
    try:
        if 'books' not in request.files and 'loans' not in request.files:
            return jsonify({'success': False, 'message': 'No CSV files provided'}), 400
        
        results = {}
        
        # Import books CSV
        if 'books' in request.files:
            books_file = request.files['books']
            if books_file.filename.endswith('.csv'):
                # Read uploaded CSV
                content = books_file.read().decode('utf-8-sig')
                lines = content.strip().split('\n')
                if len(lines) > 1:
                    headers = lines[0].split(',')
                    # Remove BOM if present
                    headers[0] = headers[0].replace('\ufeff', '')
                    headers = [h.strip().strip('"') for h in headers]
                    
                    data = []
                    for line in lines[1:]:
                        if not line.strip():
                            continue
                        values = [v.strip().strip('"') for v in line.split(',')]
                        row = {}
                        for i, h in enumerate(headers):
                            if i < len(values):
                                if h in ['id', 'number'] and values[i]:
                                    try:
                                        row[h] = int(values[i])
                                    except ValueError:
                                        row[h] = 0
                                else:
                                    row[h] = values[i]
                        data.append(row)
                    
                    # Save to CSV
                    book_headers = ['id', 'name', 'author', 'code', 'number', 'library']
                    write_csv(BOOKS_CSV, data, book_headers)
                    results['books'] = f'Imported {len(data)} books'
        
        # Import loans CSV
        if 'loans' in request.files:
            loans_file = request.files['loans']
            if loans_file.filename.endswith('.csv'):
                content = loans_file.read().decode('utf-8-sig')
                lines = content.strip().split('\n')
                if len(lines) > 1:
                    headers = lines[0].split(',')
                    headers[0] = headers[0].replace('\ufeff', '')
                    headers = [h.strip().strip('"') for h in headers]
                    
                    data = []
                    for line in lines[1:]:
                        if not line.strip():
                            continue
                        values = [v.strip().strip('"') for v in line.split(',')]
                        row = {}
                        for i, h in enumerate(headers):
                            if i < len(values):
                                if h == 'id' and values[i]:
                                    try:
                                        row[h] = int(values[i])
                                    except ValueError:
                                        row[h] = 0
                                else:
                                    row[h] = values[i]
                        data.append(row)
                    
                    # Save to CSV
                    loan_headers = ['id', 'نشان', 'نام', 'درجه', 'قسمت', 'شماره پرسنلی/دانشجویی', 
                                   'شماره تماس', 'عنوان کتاب', 'کتابخانه', 'کد کنگره', 'تاریخ امانت', 'تاریخ بازگردانی']
                    write_csv(LOANS_CSV, data, loan_headers)
                    results['loans'] = f'Imported {len(data)} loans'
        
        return jsonify({'success': True, 'message': 'CSV import completed', 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    """Export data as CSV files"""
    try:
        # Get export type
        export_type = request.args.get('type', 'all')
        
        if export_type in ['books', 'all']:
            books = read_csv(BOOKS_CSV)
            book_headers = ['id', 'name', 'author', 'code', 'number', 'library']
            book_csv = os.path.join(DATA_DIR, 'export_books.csv')
            write_csv(book_csv, books, book_headers)
        
        if export_type in ['loans', 'all']:
            loans = read_csv(LOANS_CSV)
            loan_headers = ['id', 'نشان', 'نام', 'درجه', 'قسمت', 'شماره پرسنلی/دانشجویی', 
                           'شماره تماس', 'عنوان کتاب', 'کتابخانه', 'کد کنگره', 'تاریخ امانت', 'تاریخ بازگردانی']
            loan_csv = os.path.join(DATA_DIR, 'export_loans.csv')
            write_csv(loan_csv, loans, loan_headers)
        
        return jsonify({
            'success': True,
            'message': 'Export completed',
            'files': {
                'books': '/data/export_books.csv' if export_type in ['books', 'all'] else None,
                'loans': '/data/export_loans.csv' if export_type in ['loans', 'all'] else None
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/data/<filename>')
def download_csv(filename):
    """Download exported CSV files"""
    file_path = os.path.join(DATA_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({'success': False, 'message': 'File not found'}), 404

@app.route('/api/status', methods=['GET'])
def status():
    """Check server status"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'data_directory': DATA_DIR,
        'books_file': os.path.exists(BOOKS_CSV),
        'loans_file': os.path.exists(LOANS_CSV)
    })

# ==================== RUN SERVER ====================

if __name__ == '__main__':
    print("=" * 50)
    print("📚 Library Management System - Python Server")
    print("=" * 50)
    print(f"📁 Data directory: {DATA_DIR}")
    print(f"📖 Books CSV: {BOOKS_CSV}")
    print(f"📋 Loans CSV: {LOANS_CSV}")
    print("=" * 50)
    print("🚀 Starting server at http://localhost:5000")
    print("📝 Press Ctrl+C to stop the server")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)