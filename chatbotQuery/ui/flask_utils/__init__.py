
"""


"""

try:
    from flask import Flask, render_template, request, jsonify
except:
    pass
import time


def run_flask_app_conversation(asking_f):
    app = Flask(__name__, template_folder='../../assets/templates')

    @app.route("/")
    def index():
        return render_template("chat.html")

    @app.route("/ask", methods=['POST'])
    def ask():
        def jsonify_message(messageDict):
            return {'status': 'OK', 'answer': str(messageDict['message'])}
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
                    if answer['collection']:
                        answers_json = []
                        for answer_e in answer['message']:
                            answers_json.append(jsonify_message(answer_e))
                        return jsonify(*answers_json)
                    else:
                        return jsonify(jsonify_message(answer))
    app.run(debug=True, host='0.0.0.0', port=5000)
