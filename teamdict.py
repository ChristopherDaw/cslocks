import os
from teamdict import app
#from flask import session

if __name__ == '__main__':
    app.secret_key = os.urandom(16)

    #sess = session(app)
    app.run(debug=True, use_reloader=True)
