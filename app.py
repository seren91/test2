import json
from flask import Flask, render_template, request, redirect, flash, session, url_for
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)

from icecream import ic


app = Flask(__name__)
app.secret_key = "your_secret_key"
bcrypt = Bcrypt(app)

# Create Flask app
app = Flask(__name__)
CORS(app)
app.secret_key = "your_secret_key"
bcrypt = Bcrypt(app)


# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///books.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "123"  # Replace with your actual secret key
db = SQLAlchemy(app)


# Configure Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = "login"

BOOK_TYPE_MAX_LOAN_DURATION = {"1": 10, "2": 5, "3": 2}


class Book(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(45), nullable=False)
    author = db.Column(db.String(45), nullable=False)
    year_published = db.Column(db.String(45), nullable=False)
    book_type = db.Column(db.String(100), nullable=False)
    loans = db.relationship("Loan", backref="books", cascade="all, delete-orphan")


class Customer(db.Model):
    __tablename__ = "customers"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(45), nullable=False, unique=True)
    password = db.Column(db.String(45), nullable=False)
    role = db.Column(
        db.String(45), nullable=False, default="user"
    )  # Assuming 'user' is the default role
    name = db.Column(db.String(45), nullable=False)
    city = db.Column(db.String(45), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    loans = db.relationship("Loan", backref="customers", cascade="all, delete-orphan")


class Loan(db.Model):
    __tablename__ = "loans"
    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    loan_date = db.Column(db.String(45), nullable=False)
    return_date = db.Column(db.String(45), nullable=False)

    # Foreign keys referencing Customer and Book
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)


class Users(db.Model, UserMixin):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(45), nullable=False, unique=True)
    password = db.Column(db.String(45), nullable=False)
    role = db.Column(
        db.String(45), nullable=False, default="user"
    )  # Assuming 'user' is the default role
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    customer = db.relationship("Customer", backref="users")
    # Load user from database


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash(
                "Login unsuccessful. Please check your username and password.", "danger"
            )

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully! You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


# Home page
@app.route("/")
def index():
    # Display all recipes
    # if current_user.is_authenticated:
    return render_template("index.html", user=current_user)


# flash("Please log in to access the home page.", "info")
# return redirect("/login")


# Define protected routes
@app.route("/protected_route", methods=["GET"])
@login_required  # This route requires a valid JWT token
def protected_route():
    current_user_id = get_jwt_identity()


@app.route("/addcustomer", methods=["POST"])
def add_customer():
    data = request.get_json()
    name = data.get("name")
    username = data.get("username")
    password = data.get("password")
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    role = data.get("role")
    city = data.get("city")
    age = data.get("age")

    new_customer = Customer(
        name=name,
        city=city,
        age=age,
        username=username,
        password=hashed_password,
        role=role,
    )

    db.session.add(new_customer)
    db.session.commit()

    if role.lower() == "admin":
        return jsonify({"message": "Admin added successfully"})
    else:
        return jsonify({"message": "Customer added successfully"})


@app.route("/addloan", methods=["POST"])
@login_required
def add_loan():
    try:
        data = request.get_json()

        # Get customer ID and book name from the request data
        customer_id = get_jwt_identity()
        book_name = data.get("book_name")

        # Query customer by ID and book by name
        customer = Customer.query.filter_by(id=customer_id).first()
        book = Book.query.filter_by(name=book_name).first()

        # Check if the customer and book exist
        if not customer or not book:
            return jsonify({"error": "Customer or book not found"}), 404

        # Check if the customer has already borrowed the book
        existing_loan = Loan.query.filter_by(
            customer_id=customer.id, book_id=book.id
        ).first()
        if existing_loan:
            return jsonify({"error": "Customer has already borrowed this book"}), 400

        # Create a new loan associated with the customer and book
        new_loan = Loan(
            loan_date=dt.now().strftime("%Y-%m-%d"),
            return_date="",
            customer_id=customer.id,  # Use the customer_id foreign key
            book_id=book.id,  # Use the book_id foreign key
        )

        db.session.add(new_loan)
        db.session.commit()

        return jsonify({"message": "Loan added successfully"})

    except Exception as e:
        print(str(e))
        return jsonify({"error": "Internal Server Error"}), 500


@app.route("/addbook", methods=["POST"])
# @login_required
def add_book():
    data = request.get_json()
    print(data)

    name = data.get("name")
    author = data.get("author")
    year_published = data.get("year_published")
    book_type = data.get("book_type")

    # Determine the maximum loan duration based on the book type
    max_loan_duration = {"1": 10, "2": 5, "3": 2}.get(book_type, 0)

    new_book = Book(
        name=name, author=author, year_published=year_published, book_type=book_type
    )

    db.session.add(new_book)
    db.session.commit()

    return jsonify(
        {"message": "Book added successfully", "max_loan_duration": max_loan_duration}
    )


@app.route("/listloans", methods=["GET"])
def list_loans():
    # Query all loans from the database with related customer and book information
    loans = (
        Loan.query.join(Customer, Loan.customer_id == Customer.id)
        .join(Book, Loan.book_id == Book.id)
        .all()
    )

    # Create a list of dictionaries containing loan information, customer name, and book name
    loan_list = [
        {
            "loan_date": loan.loan_date,
            "return_date": loan.return_date,
            "customer_name": loan.customers.name,  # Use the 'name' attribute of the Customer model
            "book_name": loan.books.name,  # Use the 'name' attribute of the Book model
        }
        for loan in loans
    ]

    # Return the list of loans as JSON
    return jsonify({"loans": loan_list})


@app.route("/listcustomers", methods=["GET"])
def list_customers():
    # Query all customers from the database
    customers = Customer.query.all()
    customer_list = []
    # Create a list of dictionaries containing customer information
    for customer in customers:
        if customer.role == "user":
            customer_list.append(
                {
                    "name": customer.name,
                    "role": customer.role,
                    "city": customer.city,
                    "age": customer.age,
                }
            )
    ic("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz")
    ic(customer_list)

    # Return the list of customers as JSON
    return jsonify({"customers": customer_list})


@app.route("/listbooks", methods=["GET"])
def list_books():
    # Query all books from the database
    books = Book.query.all()

    # Create a list of dictionaries containing book information
    book_list = [
        {
            "id": book.id,
            "name": book.name,
            "author": book.author,
            "year_published": book.year_published,
            "book_type": book.book_type,
        }
        for book in books
    ]

    # Return the list of books as JSON
    return jsonify({"books": book_list})


@app.route("/findbook/<string:book_name>", methods=["GET"])
def find_book(book_name):
    # Query the book by name
    book = Book.query.filter_by(name=book_name).first()

    # Check if the book exists
    if not book:
        return jsonify({"error": "Book not found"})

    # Return book information as JSON
    return jsonify(
        {
            "book": {
                "id": book.id,
                "name": book.name,
                "author": book.author,
                "year_published": book.year_published,
                "book_type": book.book_type,
            }
        }
    )


@app.route("/findcustomer/<string:customer_name>", methods=["GET"])
def find_customer(customer_name):
    # Query the customer by name
    customer = Customer.query.filter_by(name=customer_name).first()

    # Check if the customer exists
    if not customer:
        return jsonify({"error": "Customer not found"})

    # Return customer information as JSON
    return jsonify(
        {
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "city": customer.city,
                "age": customer.age,
            }
        }
    )


@app.route("/returnbook/<string:book_name>", methods=["POST"])
def return_book_by_name(book_name):
    try:
        current_user = get_jwt_identity()
        print(current_user)
        # Find the user by username
        user = Customer.query.filter_by(id=current_user).first()
        # return jsonify({'error': 'User not found'}), 200
        # Check if the user exists
        print(user)
        if not user:
            print("nnnnnnnnnuser")
            return jsonify({"error": "User not found"})
        print("gggggggggggggggggggggggggggggggggggggggggggggggggg")
        # Find the book by name
        print("aaaa")
        book = Book.query.filter_by(name=book_name).first()
        print("bbbb")
        print(book)
        # Check if the book exists
        if not book:
            print("aaaaa")
            return jsonify({"error": "Book not found"})

        # Find the latest loan for the book and the current user
        latest_loan = (
            Loan.query.filter_by(book_id=book.id, customer_id=user.id)
            .order_by(Loan.id.desc())
            .all()
        )
        # Check if there's an active loan for the book
        if len(latest_loan) == 0:
            return jsonify({"error": "No active loan for the book"})

        # Update return_date for the loan
        ic()
        for loan in latest_loan:
            if loan.return_date == "":
                loan.return_date = date.now().strftime("%Y-%m-%d")

        ic(latest_loan)
        print(db.session.dirty)
        print(db.session.new)
        db.session.commit()
        # Fetch the updated list of user books
        ##user_books = Book.query.join(Loan, Book.id == Loan.book_id).filter_by(user_id=user.id, return_date=None).all()

        # Return the list of user books along with details of the returned book
        return jsonify(
            {
                "message": "Book returned successfully",
                "returned_book": {
                    "name": book.name,
                    "author": book.author,
                    "year_published": book.year_published,
                    "book_type": book.book_type,
                },
            }
        )
    # ,
    # 'user_books': [{'name': b.name, 'author': b.author, 'year_published': b.year_published, 'book_type': b.book_type} for b in user_books]
    except Exception as e:
        print(str(e))
        return jsonify({"error": "Internal Server Error"}), 500


@app.route("/lateloans", methods=["GET"])
def list_late_loans():
    # Query late loans from the database (loans with a return_date earlier than today)
    today = datetime.now().strftime("%Y-%m-%d")
    late_loans = Loan.query.filter(Loan.return_date < today).all()

    # Create a list of dictionaries containing late loan information
    late_loan_list = [
        {"id": loan.id, "loan_date": loan.loan_date, "return_date": loan.return_date}
        for loan in late_loans
    ]

    # Return the list of late loans as JSON
    return jsonify({"late_loans": late_loan_list})


@app.route("/remove_book", methods=["POST"])
def api_remove_book():
    data = request.json
    book_id = data.get("book_id")

    remove_book(book_id)
    return jsonify({"message": "Book removed successfully"})


@app.route("/remove_customer", methods=["POST"])
def api_remove_customer():
    data = request.json
    customer_id = data.get("customer_id")

    remove_customer(customer_id)
    return jsonify({"message": "Customer removed successfully"})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
