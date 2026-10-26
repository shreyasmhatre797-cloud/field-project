from flask import Flask, render_template, request, session, redirect
import pyodbc
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, timedelta

app = Flask(__name__)
app.secret_key = "ironfitness_secret_key"


def get_connection():

    server = r'.\SQLEXPRESS01'
    database = 'GymManagement'

    connection = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        f'SERVER={server};'
        f'DATABASE={database};'
        'Trusted_Connection=yes;'
    )

    return connection


@app.route("/")
def home():

    return render_template("index.html")

@app.route("/admin")
def admin():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """SELECT MemberID, FullName, Email, Phone,
                  MembershipType, MembershipExpiry
           FROM Members"""
    )

    members = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("admin.html", members=members)


@app.route("/payments", methods=["GET", "POST"])
def payments():
    connection = get_connection()
    cursor = connection.cursor()

    if request.method == "POST":
        member_id = request.form["member_id"]
        amount = request.form["amount"]
        payment_method = request.form["payment_method"]
        payment_status = request.form["payment_status"]

        cursor.execute("""
            INSERT INTO Payments
                (MemberID, Amount, PaymentMethod, PaymentStatus)
            VALUES (?, ?, ?, ?)
        """, member_id, amount, payment_method, payment_status)

        connection.commit()

        cursor.close()
        connection.close()

        return redirect("/payments")

    cursor.execute("""
        SELECT PaymentID, MemberID, Amount,
               PaymentDate, PaymentMethod, PaymentStatus
        FROM Payments
        ORDER BY PaymentID DESC
    """)

    payment_records = cursor.fetchall()

    cursor.execute("""
        SELECT
            COALESCE(SUM(CASE
                WHEN PaymentStatus = 'Paid' THEN Amount
                ELSE 0
            END), 0) AS TotalCollected,
            SUM(CASE
                WHEN PaymentStatus = 'Paid' THEN 1
                ELSE 0
            END) AS PaidCount,
            SUM(CASE
                WHEN PaymentStatus = 'Pending' THEN 1
                ELSE 0
            END) AS PendingCount
        FROM Payments
    """)

    summary = cursor.fetchone()

    cursor.close()
    connection.close()

    return render_template(
        "payments.html",
        payments=payment_records,
        summary=summary
    )


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        membership = request.form["membership"]

        password_hash = generate_password_hash(password)

        if membership == "Monthly":
            expiry = date.today() + timedelta(days=30)

        elif membership == "Quarterly":
            expiry = date.today() + timedelta(days=90)

        else:
            expiry = date.today() + timedelta(days=365)

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO Members
            (FullName, Email, Phone, Password,
             MembershipType, MembershipExpiry)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            name,
            email,
            phone,
            password_hash,
            membership,
            expiry
        )

        connection.commit()

        cursor.close()
        connection.close()

        return """
        <h1>Registration Successful!</h1>
        <p>Welcome to Body Garage.</p>
        <a href="/">Go back to Home</a>
        """

    return render_template(
    "register.html",
    selected_plan=request.args.get("plan", "Monthly")
)


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """SELECT FullName, Password, MembershipType, MembershipExpiry
               FROM Members
               WHERE Email = ?""",
            email
        )

        member = cursor.fetchone()

        cursor.close()
        connection.close()

        if member and check_password_hash(member.Password, password):

            session["email"] = email

            status = "ACTIVE" if member.MembershipExpiry >= date.today() else "EXPIRED"

            return render_template(
                "dashboard.html",
                name=member.FullName,
                membership=member.MembershipType,
                expiry=member.MembershipExpiry,
                status=status
            )

        else:

            return """
            <h1>Login Failed</h1>
            <p>Invalid email or password.</p>
            <a href="/login">Try Again</a>
            """

    return render_template("login.html")

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


@app.route("/dashboard")
def dashboard():

    if "email" not in session:
        return redirect("/login")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """SELECT FullName, MembershipType, MembershipExpiry
           FROM Members
           WHERE Email = ?""",
        session["email"]
    )

    member = cursor.fetchone()

    cursor.close()
    connection.close()

    if not member:
        session.clear()
        return redirect("/login")

    status = "ACTIVE" if member.MembershipExpiry >= date.today() else "EXPIRED"

    return render_template(
        "dashboard.html",
        name=member.FullName,
        membership=member.MembershipType,
        expiry=member.MembershipExpiry,
        status=status
    )




@app.route("/delete_member/<int:member_id>", methods=["POST"])
def delete_member(member_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM Members WHERE MemberID = ?",
        member_id
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect("/admin")

if __name__ == "__main__":
    app.run(debug=True)