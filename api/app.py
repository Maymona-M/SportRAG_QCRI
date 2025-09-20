from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import sys, os, json
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts import rag_core
from scripts.rag_core import ConversationManager, SYSTEM_PROMPT
from scripts.pose_image_retriever import PoseImageRetriever

app = Flask(__name__, static_url_path='/static', static_folder='static')
CORS(app)

conv_manager = ConversationManager(SYSTEM_PROMPT)
retriever = PoseImageRetriever(db_path='images_db.json', base_dir='static')

import cv2
import uuid
import mediapipe as mp

import math

def calculate_angle(a, b, c):
    """Calculate angle between 3 points (in degrees)"""
    a = [a.x, a.y]
    b = [b.x, b.y]
    c = [c.x, c.y]
    
    ba = [a[0] - b[0], a[1] - b[1]]
    bc = [c[0] - b[0], c[1] - b[1]]

    cosine_angle = (ba[0]*bc[0] + ba[1]*bc[1]) / (
        math.sqrt(ba[0]**2 + ba[1]**2) * math.sqrt(bc[0]**2 + bc[1]**2) + 1e-6)
    angle = math.degrees(math.acos(max(min(cosine_angle, 1.0), -1.0)))
    return angle


@app.route('/check_pose', methods=['POST'])
def check_pose():
    if 'image' not in request.files:
        return jsonify({'message': 'No image uploaded'}), 400

    file = request.files['image']
    filename = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join('static', filename)
    file.save(filepath)

    img = cv2.imread(filepath)
    if img is None:
        return jsonify({'message': 'Invalid image'}), 400

    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils

    with mp_pose.Pose(static_image_mode=True) as pose:
        results = pose.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        if not results.pose_landmarks:
            return jsonify({'message': 'No person detected in the image.'})

        landmarks = results.pose_landmarks.landmark

        # Calculate torso angle (shoulder-hip-knee)
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]

        torso_angle = calculate_angle(left_shoulder, left_hip, left_knee)

        # Feedback based on torso angle
        if torso_angle > 160:
            feedback = "✅ You appear to be standing upright."
        else:
            feedback = "⚠️ Try to straighten your back more."

        # Draw pose landmarks on the image
        mp_drawing.draw_landmarks(img, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        # Save overlay image
        overlay_path = os.path.join('static', 'pose_' + filename)
        cv2.imwrite(overlay_path, img)

    # Optionally, remove original file to keep folder clean
    # os.remove(filepath)

    return jsonify({
        'message': feedback,
        'image_path': f'/static/pose_{filename}'
    })



def format_sse(data: str, event: str = 'message') -> str:
    return f"event: {event}\ndata: {data}\n\n"


def save_chat_log(query, response):
    log_entry = {"user_query": query, "response": response}
    with open("chat_logs.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")


def user_wants_visualization(query):
    visualization_keywords = ['show me', 'visualize', 'see', 'display', 'image', 'pose', 'technique', 'picture', 'photo']
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in visualization_keywords)


@app.route('/ask', methods=['POST'])

def ask_rag():
    data = request.json
    query = (data.get('query') or '').strip()
    print(f"[DEBUG] Received query: {query}")  # ✅

    if not query:
        print("[ERROR] No query provided")  # ✅
        return jsonify({"error": "No query provided"}), 400

    wants_vis = user_wants_visualization(query)
    print(f"[DEBUG] Wants visualization? {wants_vis}")  # ✅

    image_path = retriever.retrieve_image(query) if wants_vis else None
    if image_path:
        print(f"[DEBUG] Retrieved image path: {image_path}")  # ✅

    def generate():
        if image_path:
            image_url = f"/static/{image_path}"
            msg = {
                "type": "bot_response",
                "message": "Here is the pose visualization you requested.",
                "image_path": image_url
            }
            print(f"[DEBUG] Sending visualization response: {msg}")  # ✅
            yield format_sse(json.dumps(msg))
            save_chat_log(query, msg["message"])
            conv_manager.update(query, msg["message"])
            return

        # fallback to normal RAG streaming
        full_response = ""
        try:
            print(f"[DEBUG] Calling run_rag_pipeline for query: {query}")  # ✅
            for message_json_str in rag_core.run_rag_pipeline(query, conv_manager):
                print(f"[DEBUG] Received RAG chunk: {message_json_str}")  # ✅
                try:
                    message = json.loads(message_json_str)
                    if message.get("type") in ("bot_response", "response"):
                        full_response += message.get("message", "") or message.get("content", "")
                except Exception as parse_err:
                    print(f"[ERROR] JSON parse error: {parse_err}")  # ✅
                yield format_sse(message_json_str)

            print(f"[DEBUG] Final response to save: {full_response}")  # ✅
            save_chat_log(query, full_response)
            conv_manager.update(query, full_response)
        except Exception as e:
            print(f"[ERROR] Exception in run_rag_pipeline: {str(e)}")  # ✅
            yield format_sse(json.dumps({"type": "error", "message": f"Server error: {str(e)}"}), event="error")

    return Response(generate(), mimetype='text/event-stream')



def load_chat_history_from_logs(file_path="chat_logs.jsonl"):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    user_q = entry.get("user_query", "")
                    bot_r = entry.get("response", "")
                    if user_q and bot_r:
                        conv_manager.update(user_q, bot_r)
                except Exception:
                    continue


if __name__ == '__main__':
    print("Pre-loading RAG core components...")
    try:
        rag_core._load_embedder()
        rag_core._load_vector_db()
        load_chat_history_from_logs()
        print("Starting Flask app...")
    except Exception as e:
        print(f"Fatal error during RAG core pre-loading: {e}")
        sys.exit(1)

    app.run(debug=True, host='0.0.0.0', port=9610)
