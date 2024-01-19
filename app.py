# Virtual env -  "Set-ExecutionPolicy Unrestricted -Scope Process"

from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_socketio import SocketIO, send, emit
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
socketio = SocketIO(app)
app.secret_key = "123456"  # Change this to a secure, random key

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    vote = db.Column(db.Integer, nullable=False, default=0)


class Help(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)


@app.route("/")
def home():
    if "username" in session:
        username = session["username"]
        return render_template("logged.html", username=username)
    return 'You are not logged in | <a href="/login">Login</a>'


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]

        # Check if the user exists in the database
        user = User.query.filter_by(username=username).first()

        if not user:
            # If the user does not exist, create a new user and add it to the database
            new_user = User(username=username, vote=0)
            db.session.add(new_user)
            db.session.commit()

        session["username"] = username
        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/help_data")
def help_data():
    help_entries = Help.query.all()
    data = [{"id": entry.id, "username": entry.username} for entry in help_entries]
    return render_template("help_data.html")


@app.route("/fetch_help_data")
def fetch_help_data():
    help_entries = Help.query.all()
    data = [{"id": entry.id, "username": entry.username} for entry in help_entries]
    return jsonify(data)


@app.route("/help", methods=["POST"])
def help():
    if "username" in session:
        current_username = session["username"]
        help_entry = Help(username=current_username)
        db.session.add(help_entry)
        db.session.commit()
        return jsonify({"message": "Help requested successfully"})
    return jsonify({"message": "User not logged in"})


@app.route("/delete_help_request/<int:help_id>", methods=["DELETE"])
def delete_help_request(help_id):
    try:
        # Delete the help request from the database
        help_entry = Help.query.get(help_id)
        if help_entry:
            db.session.delete(help_entry)
            db.session.commit()

            # Return success response
            return jsonify({"message": "Help request deleted successfully"}), 200
        else:
            # Return error response if help entry is not found
            return jsonify({"error": "Help request not found"}), 404
    except Exception as e:
        # Return error response if there's any issue with deletion
        return jsonify({"error": str(e)}), 500


@app.route("/clear_all_help_requests", methods=["DELETE"])
def clear_all_help_requests():
    try:
        # Clear all help requests from the database
        Help.query.delete()
        db.session.commit()

        # Return success response
        return jsonify({"message": "All help requests cleared successfully"}), 200
    except Exception as e:
        # Return error response if there's any issue with clearing
        return jsonify({"error": str(e)}), 500


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("home"))


@app.route("/graph")
def graph():
    return render_template("graph.html")


@app.route("/get_votes_count")
def get_votes_count():
    count_0 = User.query.filter_by(vote=0).count()
    count_1 = User.query.filter_by(vote=1).count()
    return jsonify({"0": count_0, "1": count_1})


@socketio.on("message")
def handle_message(message):
    print("Received message:", message)


@socketio.on("connect")
def handle_connect():
    print("Client connected")


@socketio.on("vote")
def handle_vote(data):
    # Extract the username from the data
    username = data["username"]

    # Update the vote in the database
    user = User.query.filter_by(username=username).first()
    if not user:
        # If the user does not exist, create a new user and add it to the database
        new_user = User(username=username, vote=0)
        db.session.add(new_user)
        db.session.commit()
    else:
        # Flash a message indicating that the username is already taken
        flash("Username already taken. Please choose another.")

    # Optionally, you can emit a message back to the client
    emit("vote_result", {"message": "Vote submitted successfully"}, broadcast=True)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    socketio.run(app, debug=True)
    # OR
    # app.run(debug=True)
