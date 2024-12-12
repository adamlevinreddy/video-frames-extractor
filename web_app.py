
from flask import Flask, render_template, request, send_from_directory
from pathlib import Path
import os
from frame_extractor_multithread import FrameExtractor
import settings

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'videos'
app.config['OUTPUT_FOLDER'] = str(settings.OUTDIR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'video' not in request.files:
        return 'No video file uploaded', 400
    
    file = request.files['video']
    if file.filename == '':
        return 'No selected file', 400

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(video_path)
    
    frame_extractor = FrameExtractor(
        Path(video_path),
        Path(app.config['OUTPUT_FOLDER']),
        settings.REQUIRED_IMAGE_FORMAT,
        settings.REQUIRED_FRAME_RATE,
        settings.START_FROM_SECOND,
        settings.REQUIRED_IMAGE_WIDTH,
        True
    )
    
    frame_extractor.extract_frames()
    return 'Video processed successfully', 200

@app.route('/frames')
def view_frames():
    resize_frames_dir = os.path.join(app.config['OUTPUT_FOLDER'], 're_size_frames')
    if not os.path.exists(resize_frames_dir):
        return 'No frames available', 404
        
    frames = [f for f in os.listdir(resize_frames_dir) if f.endswith(settings.REQUIRED_IMAGE_FORMAT)]
    return render_template('frames.html', frames=frames)

@app.route('/frame/<filename>')
def frame(filename):
    return send_from_directory(os.path.join(app.config['OUTPUT_FOLDER'], 're_size_frames'), filename)
