from flask import Flask, render_template, request, redirect, url_for
from services.user_service import initialize_app_database, create_user, fetch_user_by_id, remove_user_by_id
import os

app = Flask(__name__)

if os.getenv("ENV") != "test":
    initialize_app_database()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    address = request.form.get('address', '').strip()
    phonenumber = request.form.get('phonenumber', '').strip()
    password = request.form.get('password', '')

    if not all([name, email, address, phonenumber, password]):
        return redirect(url_for('index'))

    user = create_user(name, email, address, phonenumber, password)
    return render_template('submitteddata.html', user=user)


@app.route('/get-data', methods=['GET', 'POST'])
def get_data():
    if request.method == 'POST':
        input_id = request.form.get('input_id', '').strip()
        if not input_id.isdigit():
            return render_template('data.html', users=[], input_id=input_id, error='Enter a numeric ID.')

        users = fetch_user_by_id(int(input_id))
        return render_template('data.html', users=users, input_id=input_id)

    return render_template('get_data.html')


@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete_data(id):
    if request.method == 'POST':
        remove_user_by_id(id)
        return redirect(url_for('get_data'))

    return render_template('delete.html', id=id)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
