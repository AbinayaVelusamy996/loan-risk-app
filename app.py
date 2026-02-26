from flask import Flask, render_template, request, redirect, url_for, flash, Response, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import pickle
import numpy as np
import os

from models import db, User, Prediction   # IMPORTANT

# ---------------- APP INIT ----------------
app = Flask(__name__)
app.secret_key = "supersecretkey"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)   # ✅ now config already set

# ---------------- LOGIN MANAGER ----------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- ADMIN DECORATOR ----------------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role.lower() != "admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# ---------------- LOAD ML MODEL ----------------
with open("loan_model.pkl", "rb") as f:
    model = pickle.load(f)

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid credentials")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = User(
            username=request.form["username"],
            email=request.form["email"],
            password=generate_password_hash(request.form["password"]),
            role="user"
        )
        db.session.add(user)
        db.session.commit()
        flash("Registration successful")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ---------------- DASHBOARD ----------------
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":

        features = np.array([[
            int(request.form["no_of_dependents"]),
            1 if request.form["education"].lower() == "graduate" else 0,
            1 if request.form["self_employed"].lower() == "yes" else 0,
            float(request.form["income_annum"]),
            float(request.form["loan_amount"]),
            float(request.form["loan_term"]),
            float(request.form["cibil_score"]),
            float(request.form["residential_assets_value"]),
            float(request.form["commercial_assets_value"]),
            float(request.form["luxury_assets_value"]),
            float(request.form["bank_asset_value"])
        ]])

        prob = model.predict_proba(features)[0][1]

        cibil = float(request.form["cibil_score"])
        income = float(request.form["income_annum"])
        loan_amt = float(request.form["loan_amount"])

        if cibil >= 750 and income >= 800000 and loan_amt <= income * 0.5:
            loan_status, risk_level = "Approved", "Low"
        elif cibil >= 650:
            loan_status, risk_level = "Approved", "Medium"
        else:
            loan_status, risk_level = "Rejected", "High"

        prediction = Prediction(
            user_id=current_user.id,
            applicant_name=request.form["applicant_name"],
            no_of_dependents=int(request.form["no_of_dependents"]),
            education=request.form["education"],
            self_employed=request.form["self_employed"],
            income_annum=income,
            loan_amount=loan_amt,
            loan_term=float(request.form["loan_term"]),
            cibil_score=cibil,
            residential_assets_value=float(request.form["residential_assets_value"]),
            commercial_assets_value=float(request.form["commercial_assets_value"]),
            luxury_assets_value=float(request.form["luxury_assets_value"]),
            bank_asset_value=float(request.form["bank_asset_value"]),
            loan_status=loan_status,
            risk_level=risk_level,
            probability=round(prob, 2)
        )

        db.session.add(prediction)
        db.session.commit()

        return redirect(url_for("prediction_result", id=prediction.id))

    return render_template("dashboard.html")

@app.route("/prediction_result/<int:id>")
@login_required
def prediction_result(id):
    prediction = Prediction.query.get_or_404(id)
    return render_template("result.html", prediction=prediction)

@app.route("/history")
@login_required
def history():
    preds = Prediction.query.filter_by(user_id=current_user.id).all()
    return render_template("history.html", predictions=preds)

# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin/dashboard")
@login_required
@admin_required
def admin_dashboard():
    query = db.session.query(Prediction, User.username).join(User)
    search = request.args.get("search")

    if search:
        query = query.filter(
            User.username.contains(search) |
            Prediction.loan_status.contains(search) |
            Prediction.risk_level.contains(search)
        )

    return render_template("admin_dashboard.html", predictions=query.all())

# ---------------- EXPORT CSV ----------------
# @app.route("/admin/export")
# @login_required
# @admin_required
# def export_csv():
#     # Fetch predictions with outer join to include all, even if user missing
#     predictions = db.session.query(
#         Prediction.loan_amount,
#         Prediction.loan_status,
#         Prediction.risk_level,
#         Prediction.probability,
#         Prediction.timestamp,
#         User.username
#     ).outerjoin(User).all()
#
#     def generate():
#         # CSV Header
#         yield "Username,LoanAmount,Status,Risk,Probability,Date\n"
#
#         for loan_amount, loan_status, risk_level, probability, timestamp, username in predictions:
#             # Safe defaults
#             username = username if username is not None else "N/A"
#             loan_amount = loan_amount if loan_amount is not None else 0
#             loan_status = loan_status if loan_status else "N/A"
#             risk_level = risk_level if risk_level else "N/A"
#             # Convert probability to integer percentage string
#             probability_str = f"{int(round(probability * 100))}%" if probability is not None else "0%"
#             # Format timestamp safely
#             date_str = timestamp.strftime("%Y-%m-%d %H:%M:%S") if timestamp else "N/A"
#
#             # Yield CSV row
#             yield f"{username},{loan_amount},{loan_status},{risk_level},{probability_str},{date_str}\n"
#
#     return Response(
#         generate(),
#         mimetype="text/csv",
#         headers={"Content-Disposition": "attachment;filename=predictions.csv"}
#     )


@app.route("/admin/export")
@login_required
@admin_required
def export_csv():

    search = request.args.get("search")

    query = db.session.query(
        Prediction.loan_amount,
        Prediction.loan_status,
        Prediction.risk_level,
        Prediction.probability,
        Prediction.timestamp,
        User.username
    ).outerjoin(User)

    # ✅ Apply same search filter
    if search:
        query = query.filter(
            User.username.contains(search) |
            Prediction.loan_status.contains(search) |
            Prediction.risk_level.contains(search)
        )

    predictions = query.all()

    def generate():
        yield "Username,LoanAmount,Status,Risk,Probability,Date\n"

        for loan_amount, loan_status, risk_level, probability, timestamp, username in predictions:
            username = username or "N/A"
            loan_amount = loan_amount or 0
            loan_status = loan_status or "N/A"
            risk_level = risk_level or "N/A"
            probability_str = f"{int(round(probability * 100))}%" if probability else "0%"
            date_str = timestamp.strftime("%Y-%m-%d %H:%M:%S") if timestamp else "N/A"

            yield f"{username},{loan_amount},{loan_status},{risk_level},{probability_str},{date_str}\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=filtered_predictions.csv"}
    )

# ---------------- MAIN ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
