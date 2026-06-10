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
    video_file = request.files['video']
    x = int(request.form.get('x'))
    y = int(request.form.get('y'))
    w = int(request.form.get('w'))
    h = int(request.form.get('h'))

    input_path = os.path.join(UPLOAD_FOLDER, video_file.filename)
    output_path = os.path.join(OUTPUT_FOLDER, "ai_clean_" + video_file.filename)
    video_file.save(input_path)

    try:
        # Open the video file using OpenCV
        cap = cv2.VideoCapture(input_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Setup video writer to save the output
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # 1. Create a black mask matching the frame size
            mask = np.zeros(frame.shape[:2], dtype=np.uint8)
            
            # 2. Draw a white box exactly where your logo is
            mask[y:y+h, x:x+w] = 255

            # 3. Apply Advanced AI/Math Inpainting to intelligently heal the background texture
            # cv2.INPAINT_TELEA reconstructs the target area using neighborhood pixel structures
            clean_frame = cv2.inpaint(frame, mask, inpaintRadius=7, flags=cv2.INPAINT_TELEA)

            out.write(clean_frame)

        cap.release()
        out.release()

        return send_file(output_path, as_attachment=True)
    
    except Exception as e:
        print(f"AI Processing Error: {e}")
        return {"error": str(e)}, 500
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
if __name__ == '__main__':
    app.run(port=5000, debug=True)