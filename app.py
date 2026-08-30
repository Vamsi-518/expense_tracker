from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)

app.secret_key = "expense_tracker_secret_key"

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456",
        database="expense_tracker"
    )

def login_required(route_function):

    @wraps(route_function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        return route_function(*args, **kwargs)

    return wrapper

@app.route("/")
def home():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        if not name or not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        db = get_db()
        cursor = db.cursor()

        try:

            cursor.execute(
                """
                INSERT INTO users (name, email, password)
                VALUES (%s, %s, %s)
                """,
                (name, email, hashed_password)
            )

            db.commit()

            flash("Registration successful. Please login.", "success")

            return redirect(url_for("login"))

        except mysql.connector.IntegrityError:

            flash("Email already registered.", "error")

            return redirect(url_for("register"))

        finally:

            cursor.close()
            db.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email = %s",
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        db.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():

    user_id = session["user_id"]

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Get transactions
    cursor.execute(
        """
        SELECT *
        FROM transactions
        WHERE user_id = %s
        ORDER BY transaction_date DESC, id DESC
        """,
        (user_id,)
    )

    transactions = cursor.fetchall()

    # Total income
    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM transactions
        WHERE user_id = %s AND type = 'Income'
        """,
        (user_id,)
    )

    total_income = cursor.fetchone()["total"]

    # Total expense
    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM transactions
        WHERE user_id = %s AND type = 'Expense'
        """,
        (user_id,)
    )

    total_expense = cursor.fetchone()["total"]

    balance = total_income - total_expense

    cursor.close()
    db.close()

    return render_template(
        "dashboard.html",
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance
    )


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_transaction():

    if request.method == "POST":

        transaction_type = request.form["type"]
        category = request.form["category"]
        amount = request.form["amount"]
        description = request.form["description"]
        transaction_date = request.form["transaction_date"]

        if not category or not amount or not transaction_date:
            flash("Please fill all required fields.", "error")
            return redirect(url_for("add_transaction"))

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO transactions
            (user_id, type, category, amount, description, transaction_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                session["user_id"],
                transaction_type,
                category,
                amount,
                description,
                transaction_date
            )
        )

        db.commit()

        cursor.close()
        db.close()

        flash("Transaction added successfully.", "success")

        return redirect(url_for("dashboard"))

    return render_template("add_transaction.html")


@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_transaction(id):

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM transactions
        WHERE id = %s AND user_id = %s
        """,
        (id, session["user_id"])
    )

    transaction = cursor.fetchone()

    if not transaction:

        cursor.close()
        db.close()

        flash("Transaction not found.", "error")

        return redirect(url_for("dashboard"))

    if request.method == "POST":

        transaction_type = request.form["type"]
        category = request.form["category"]
        amount = request.form["amount"]
        description = request.form["description"]
        transaction_date = request.form["transaction_date"]

        cursor.execute(
            """
            UPDATE transactions
            SET type = %s,
                category = %s,
                amount = %s,
                description = %s,
                transaction_date = %s
            WHERE id = %s AND user_id = %s
            """,
            (
                transaction_type,
                category,
                amount,
                description,
                transaction_date,
                id,
                session["user_id"]
            )
        )

        db.commit()

        cursor.close()
        db.close()

        flash("Transaction updated successfully.", "success")

        return redirect(url_for("dashboard"))

    cursor.close()
    db.close()

    return render_template(
        "edit_transaction.html",
        transaction=transaction
    )


@app.route("/delete/<int:id>")
@login_required
def delete_transaction(id):

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        DELETE FROM transactions
        WHERE id = %s AND user_id = %s
        """,
        (id, session["user_id"])
    )

    db.commit()

    cursor.close()
    db.close()

    flash("Transaction deleted.", "success")

    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True)