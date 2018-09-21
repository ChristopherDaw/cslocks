from os import environ
from cslocks.app import app

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
