
"""


"""

try:
    from flask import Flask, render_template, request, jsonify
except:
    pass
import time


def run_flask_app_conversation(asking_f):
    app = Flask(__name__, template_folder='../../templates')

    @app.route("/")
    def index():
        return render_template("chat2.html")

    @app.route("/ask", methods=['POST'])
    def ask():
        exited = False
        if exited:
            time.sleep(60)
            exit()
        message = str(request.form['messageText'])
        while True:
            if (message == "quit") or (message is None):
                exit()
            else:
                answer = asking_f({'message': message})
                if (answer is None) or exited:
                    exited = True
                else:
                    bot_response = str(answer['message'])
                    return jsonify({'status': 'OK', 'answer': bot_response})
    app.run(debug=True, host='0.0.0.0', port=5000)
