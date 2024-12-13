
from flask import Flask, render_template, request, send_from_directory
from pathlib import Path
import os
import traceback
from frame_extractor_multithread import FrameExtractor
import settings

app = Flask(__name__, static_folder=str(settings.OUTDIR), static_url_path='/static')
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

        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        video_name = file.filename.rsplit('.', 1)[0]
        
        # Create directories if they don't exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        frame_dir = os.path.join(app.config['OUTPUT_FOLDER'], f"{video_name}_{timestamp}")
        os.makedirs(frame_dir, exist_ok=True)
        os.makedirs(os.path.join(frame_dir, 'orig_size_frames'), exist_ok=True)
        os.makedirs(os.path.join(frame_dir, 're_size_frames'), exist_ok=True)
        
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(video_path)
        
        from concurrent.futures import ThreadPoolExecutor
        frame_extractor = FrameExtractor(
            out_dir=Path(frame_dir),
            img_frmt=settings.REQUIRED_IMAGE_FORMAT,
            required_frame_rate=settings.REQUIRED_FRAME_RATE,
            start_from_seconds=settings.START_FROM_SECOND,
            img_width=settings.REQUIRED_IMAGE_WIDTH,
            verbose=True
        )
        
        with ThreadPoolExecutor() as executor:
            executor.submit(frame_extractor.extract_frames, Path(video_path))
        return 'Video processed successfully', 200
    except Exception as e:
        print(f"Error processing video: {str(e)}")
        print(traceback.format_exc())
        return f'Error processing video: {str(e)}', 500

@app.route('/frames')
def view_frames():
    try:
        output_dir = app.config['OUTPUT_FOLDER']
        extractions = sorted([d for d in os.listdir(output_dir) 
                            if os.path.isdir(os.path.join(output_dir, d))])
        return render_template('frames.html', extractions=extractions)
    except Exception as e:
        print(f"Error viewing frames: {str(e)}")
        return f'Error viewing frames: {str(e)}', 500

@app.route('/frames/<extraction>')
def view_extraction_frames(extraction):
    try:
        resize_frames_dir = os.path.join(app.config['OUTPUT_FOLDER'], extraction, 're_size_frames')
        if not os.path.exists(resize_frames_dir):
            return 'No frames available', 404
            
        frames = [f for f in os.listdir(resize_frames_dir) if f.endswith(settings.REQUIRED_IMAGE_FORMAT)]
        return render_template('frames.html', frames=frames, current_extraction=extraction)
    except Exception as e:
        print(f"Error viewing frames: {str(e)}")
        return f'Error viewing frames: {str(e)}', 500

@app.route('/frame/<filename>')
def frame(filename):
    try:
        resize_frames_dir = os.path.join(app.config['OUTPUT_FOLDER'], 're_size_frames')
        return send_from_directory(resize_frames_dir, filename, as_attachment=False)
    except Exception as e:
        print(f"Error serving frame: {str(e)}")
        return f'Error serving frame: {str(e)}', 500

@app.route('/action-frames/<extraction>')
def view_action_frames(extraction):
    try:
        from frame_analyzer import FrameAnalyzer
        frames_dir = Path(os.path.join(app.config['OUTPUT_FOLDER'], extraction, 're_size_frames'))
        analyzer = FrameAnalyzer(frames_dir)
        action_frames = analyzer.detect_changes()
        action_frames = [f.name for f in action_frames]
        return render_template('frames.html', frames=action_frames, current_extraction=extraction)
    except Exception as e:
        print(f"Error detecting action frames: {str(e)}")
        return f'Error detecting action frames: {str(e)}', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
