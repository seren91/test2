# Library Management System

The Library Management System is a Flask-based web application with user authentication, role-based access, and features to manage books, customers, and loans in a library.

## Features

- User authentication and authorization (user and admin roles).
- Add new customers and books.
- Loan and return books.
- Display lists of books, customers, and loans.
- Find books and customers by name.
- List late loans.
- Remove books and customers.

## Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/library-management-system.git
Create a virtual environment (recommended):


python -m venv venv
Activate the virtual environment:
.\venv\Scripts\activate
Install dependencies:
pip install -r requirements.txt
Initialize the database:
python app.py
Usage
Register an account or log in if you already have one.
Use the provided functionalities in the web interface or interact with the API routes.
API Routes
POST /login: Log in with username and password.
POST /register: Register a new user.
GET /logout: Log out the current user.
POST /addcustomer: Add a new customer.
POST /addloan: Add a new loan.
POST /addbook: Add a new book.
GET /listloans: List all loans.
GET /listcustomers: List all customers.
GET /listbooks: List all books.
GET /findbook/{book_name}: Find a book by name.
GET /findcustomer/{customer_name}: Find a customer by name.
POST /returnbook/{book_name}: Return a book by name.
GET /lateloans: List late loans.
POST /remove_book: Remove a book.
POST /remove_customer: Remove a customer.
Contributing
If you'd like to contribute to this project, please follow the Contributing Guidelines.

License
This project is licensed under the MIT License.