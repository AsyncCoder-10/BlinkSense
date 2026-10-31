import cv2, csv, io
from flask import Flask, Response, jsonify, render_template
from detector import Analyzer
from rag import coach

app = Flask(__name__)
analyzer = Analyzer()


def frames():
    cap = cv2.VideoCapture(0)
    while True:
        ok, f = cap.read()
        if not ok:
            break
        f = analyzer.process(cv2.flip(f, 1))
        _, buf = cv2.imencode(".jpg", f)
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video")
def video():
    return Response(frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/api/status")
def status():
    return jsonify(analyzer.stats())


@app.route("/api/reset", methods=["POST"])
def reset():
    analyzer.reset()
    return jsonify(ok=True)


@app.route("/api/export")
def export():
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["time", "state", "ear", "blinks"])
    w.writerows(analyzer.log)
    return Response(
        out.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=session.csv"},
    )


@app.route("/api/feedback")
def feedback():
    return jsonify(feedback=coach(analyzer.stats()))


if __name__ == "__main__":
    app.run(debug=False, threaded=True)
