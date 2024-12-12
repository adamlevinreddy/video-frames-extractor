
from flask import Flask, render_template, request, send_from_directory
from pathlib import Path
import os
import traceback
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
    try:
        if 'video' not in request.files:
            return 'No video file uploaded', 400
        
        file = request.files['video']
        if file.filename == '':
            return 'No selected file', 400

        # Create directories if they don't exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
        os.makedirs(os.path.join(app.config['OUTPUT_FOLDER'], 're_size_frames'), exist_ok=True)
        
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(video_path)
        
        frame_extractor = FrameExtractor(
            vid=Path(video_path),
            out_dir=Path(app.config['OUTPUT_FOLDER']),
            img_frmt=settings.REQUIRED_IMAGE_FORMAT,
            required_frame_rate=settings.REQUIRED_FRAME_RATE,
            start_from_seconds=settings.START_FROM_SECOND,
            img_width=settings.REQUIRED_IMAGE_WIDTH,
            verbose=True
        )
        
        frame_extractor.extract_frames()
        return 'Video processed successfully', 200
    except Exception as e:
        print(f"Error processing video: {str(e)}")
        print(traceback.format_exc())
        return f'Error processing video: {str(e)}', 500

@app.route('/frames')
def view_frames():
    try:
        resize_frames_dir = os.path.join(app.config['OUTPUT_FOLDER'], 're_size_frames')
        if not os.path.exists(resize_frames_dir):
            return 'No frames available', 404
            
        frames = [f for f in os.listdir(resize_frames_dir) if f.endswith(settings.REQUIRED_IMAGE_FORMAT)]
        return render_template('frames.html', frames=frames)
    except Exception as e:
        print(f"Error viewing frames: {str(e)}")
        return f'Error viewing frames: {str(e)}', 500

@app.route('/frame/<filename>')
def frame(filename):
    return send_from_directory(os.path.join(app.config['OUTPUT_FOLDER'], 're_size_frames'), filename)
