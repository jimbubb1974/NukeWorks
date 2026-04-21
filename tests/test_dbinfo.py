from app import create_app

# This script uses Flask's test client to simulate a browser session
# which has already selected the Q: database via session. It then
# calls the temporary debug endpoint /select-db/db-info and prints the
# JSON response. Save this file at the repo root and run:
#    (.venv) C:\...\NukeWorks> python test_dbinfo.py

app = create_app('development')
app.testing = True

path = r"Q:\0001\PS05DNED\Uncontrolled Documents\5 - Reference Info\Projects Database\nukeworks.sqlite"

with app.test_client() as client:
    # Set the session to indicate the DB was selected in the browser
    with client.session_transaction() as sess:
        sess['selected_db_path'] = path

    resp = client.get('/select-db/db-info')
    print('status:', resp.status_code)
    print(resp.get_data(as_text=True))
