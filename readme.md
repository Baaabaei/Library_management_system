# 📚 Library Management System

A full-featured library management web application built with Flask (Python backend) and vanilla JavaScript, designed to help small libraries manage their book collections and lending processes efficiently.

![Languages](https://img.shields.io/badge/HTML-74.4%25-orange)
![Languages](https://img.shields.io/badge/Python-25.5%25-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

- **Dashboard Overview**: Get a quick snapshot of your library's status including total books, active loans, returned items, and overdue notices.
- **Book Management**: Add, edit, search, filter, and delete books. Track total copies and available quantities.
- **Loan Management**: Register new loans, record book returns, and maintain a complete history of all transactions.
- **Overdue Tracking**: Automatically identifies loans overdue by more than 2 weeks, calculated using the Jalali (Persian) calendar.
- **Dual-Library Support**: Manage collections for both the **Main Library** and the **Electrical Engineering Faculty**.
- **Advanced Search**: Perform comprehensive searches across book titles, authors, and all loan record fields.
- **CSV Import/Export**: Easily migrate your data using standard CSV files.
- **Persian (Farsi) UI**: Full right-to-left (RTL) interface tailored for Persian-speaking users.

## 🖥️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Python 3.6+ with Flask |
| **Frontend** | Vanilla JavaScript, HTML5, CSS3 |
| **Data Storage** | CSV files (no database setup required) |
| **CORS** | Flask-CORS for cross-origin requests |

## 🚀 Getting Started

### Prerequisites

- Python 3.6 or higher installed on your system.
- `pip` package manager.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Baaabaei/Library_management_system.git
    cd Library_management_system
    ```

2.  **Install required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```
    This will install `flask` and `flask-cors`.

### Running the Application

1.  **Start the Flask server:**
    - **Windows:** Double-click the `run_server.bat` file.
    - **Manual (All OS):** Run the following command in your terminal:
      ```bash
      python server.py
      ```
    You should see output indicating the server is running on `http://localhost:5000`.

2.  **Open the application:**
    Open your web browser and navigate to `http://localhost:5000`.

> [!NOTE]
> The server uses port `5000` by default. If this port is in use, you can change it in the `server.py` file.

## 📂 Project Structure

```
Library_management_system/
├── server.py              # Flask backend server
├── index.html             # Main frontend single-page interface
├── requirements.txt       # Python dependencies
├── run_server.bat         # Windows batch file to start the server
├── data/                  # Data storage directory (auto-created)
│   ├── books.csv          # Book inventory
│   └── loans.csv          # Loan transaction records
└── Tutorial.md            # Detailed user guide (in Persian)
```

## 💾 Data Storage

The system uses CSV files for data persistence, eliminating the need for a separate database setup:
- **`books.csv`**: Stores book information (ID, name, author, code, quantity, library).
- **`loans.csv`**: Stores loan records (borrower details, book info, dates, library).

> [!IMPORTANT]
> The system automatically initializes these files with sample data on the first run.

## 🔧 Key Features in Detail

### Dashboard
Get an overview of your library's status at a glance.

![Dashboard](docs/images/dashboard.png)


### Automatic Overdue Calculation
The system calculates overdue days based on the **Jalali (Shamsi/Persian) calendar**. It compares the loan's borrow date against today's system date to determine if an item is overdue.
Automatically identify overdue items.

![Overdue List](docs/images/overdue.png)
*Items overdue by more than 2 weeks*
### Multi-Library Support
Each book and loan can be associated with a specific library branch, allowing you to manage multiple collections within a single system.

### Data Import/Export
- **Export:** Send a `GET` request to `/api/export/csv?type=all`.
- **Import:** Send a `POST` request to `/api/import/csv` with the CSV files.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details (if provided).

## 👤 Author

**Baaabaei**

- GitHub: [@Baaabaei](https://github.com/Baaabaei)

---
Made with 📚 for better library management.