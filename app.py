import os
import cv2
import numpy as np
from flask import Flask, request, send_file, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Serves your index.html file at http://127.0.0.1:5000/
@app.route('/')
def home():
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return render_template_string(f.read())
    except FileNotFoundError:
        return "index.html not found in directory!", 404

@app.route('/script.js')
def serve_script():
    try:
        with open('script.js', 'r', encoding='utf-8') as f:
            # Returns the javascript file with the correct web header
            return f.read(), 200, {'Content-Type': 'application/javascript'}
    except FileNotFoundError:
        return "script.js not found!", 404

@app.route('/api/remove-logo', methods=['POST'])
def remove_logo():
    if 'video' not in request.files:
        return {"error": "No video file provided"}, 400

    video_file = request.files['video']
    
    try:
        x = int(float(request.form.get('x', 0)))
        y = int(float(request.form.get('y', 0)))
        w = int(float(request.form.get('w', 0)))
        h = int(float(request.form.get('h', 0)))
    except ValueError:
        return {"error": "Invalid coordinates provided"}, 400

    # Ensure directories exist right before processing
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    input_path = os.path.join(UPLOAD_FOLDER, video_file.filename)
    output_path = os.path.join(OUTPUT_FOLDER, "ai_clean_" + os.path.splitext(video_file.filename)[0] + ".mp4")
    video_file.save(input_path)

    try:
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise Exception("Could not open input video file.")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0: fps = 30.0  # Fallback if FPS detection fails
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # PRODUCTION FIX: Use XVID codec which is universally supported on Linux servers
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        if not out.isOpened():
            raise Exception("VideoWriter failed to initialize. Check server codec support.")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Boundary safety checks for the coordinates
            img_h, img_w = frame.shape[:2]
            actual_x = max(0, min(x, img_w - 1))
            actual_y = max(0, min(y, img_h - 1))
            actual_w = max(1, min(w, img_w - actual_x))
            actual_h = max(1, min(h, img_h - actual_y))

            # Generate binary mask array
            mask = np.zeros(frame.shape[:2], dtype=np.uint8)
            mask[actual_y:actual_y+actual_h, actual_x:actual_x+actual_w] = 255

            # Apply advanced AI texture healing
            clean_frame = cv2.inpaint(frame, mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)
            out.write(clean_frame)

        cap.release()
        out.release()

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception("Output video was not generated or is empty.")

        return send_file(output_path, as_attachment=True)
    
    except Exception as e:
        print(f"CRITICAL PROCESSING ERROR: {str(e)}")
        return {"error": f"Internal video processing failure: {str(e)}"}, 500
    finally:
        # Cleanup temporary raw uploads to keep the server clean
        if os.path.exists(input_path):
            os.remove(input_path)

if __name__ == '__main__':
    app.run(port=5000, debug=True)