# in-built modules
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor

# dependencies packages
import cv2
import imutils

# Internal module
import settings


class FrameExtractor:
    def __init__(self, out_dir, img_frmt='jpg', required_frame_rate=None, start_from_seconds=None, img_width=720, verbose=True):
        self.out_dir = out_dir
        self.img_frmt = img_frmt
        self.required_frame_rate = required_frame_rate or 1
        self.start_from_seconds = start_from_seconds or 0
        self.img_width = img_width
        self.verbose = verbose

    def create_dir_if_not_exists(self, dirname: str):
        """Create a directory with the specified name inside the 'out_dir' 
        directory if it doesn't exist.

        :param dirname: Name of the directory to be created.
        :return: created dir path.
        """
        target_dir = Path.joinpath(self.out_dir, dirname)
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
        else:
            return target_dir
        return target_dir

    def extract_frames(self, vid):
        """Extract frames from a video."""
        count = 1

        vid_cap = cv2.VideoCapture(str(Path(vid)))
        frames = int(vid_cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
        fps = int(vid_cap.get(cv2.CAP_PROP_FPS))
        try:
            seconds = int(frames/fps)
            target_frames = int(seconds * self.required_frame_rate)
        except ZeroDivisionError as ex:
            print("Unable to detect seconds")
            seconds = 1
            target_frames = 1

        if self.verbose:
            print("======================================")
            print(f"[OUT FILE DIRECTORY] - {self.out_dir}")
            print(f"[TOTAL SOURCE FRAMES] - {frames}")
            print(f"[SOURCE FPS] - {fps}")
            print(f"[VIDEO LENGTH] - {seconds} seconds")
            print(f"[TARGET EXTRACTION RATE] - {self.required_frame_rate} frames/sec")
            print(f"[EXPECTED OUTPUT FRAMES] - {target_frames}")
        # start from 1 if 'start_from_seconds' is not passed.
        sec = int(self.start_from_seconds)
        vid_cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
        vidname = vid.stem

        orig_file_dir = self.create_dir_if_not_exists('orig_size_frames')
        resize_file_dir = self.create_dir_if_not_exists('re_size_frames')
        while (vid_cap.isOpened()):
            success, image = vid_cap.read()
            if success:
                try:
                    timestamp_ms = vid_cap.get(cv2.CAP_PROP_POS_MSEC)
                    # Format timestamp with padded numbers for proper sorting
                    timestamp = time.strftime('%H_%M_%S', time.gmtime(timestamp_ms/1000))
                    frame_num = str(count).zfill(5)  # Pad with zeros for proper sorting
                    orig_file_location = f"{orig_file_dir}/{timestamp}_{frame_num}_{vidname}.{self.img_frmt}"
                    resize_file_location = f"{resize_file_dir}/{timestamp}_{frame_num}_{vidname}.{self.img_frmt}"

                    # Calculate original aspect ratio
                    height, width = image.shape[:2]
                    aspect_ratio = width / height

                    # Keep original resolution but fix aspect ratio if needed
                    if width != int(height * aspect_ratio):
                        new_height = height
                        new_width = int(height * aspect_ratio)
                        orig_img = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
                    else:
                        orig_img = image
                    cv2.imwrite(orig_file_location, orig_img)

                    # Create resized version while maintaining aspect ratio
                    new_width = settings.REQUIRED_IMAGE_WIDTH
                    new_height = int(new_width / aspect_ratio)
                    resized_img = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
                    cv2.imwrite(resize_file_location, resized_img)

                    print(f"Done: {count}")
                except Exception as ex:
                    print("[ERROR CODE 1001]")
                    print(ex)
            else:
                print(f"Done Extracting for video {vid}")
                print(
                    f"Frames: {count - 1} orig & Frames: {count - 1} resized.")
                break

            count += 1
            if count > frames:  # Stop if we've processed all frames
                print(f"Reached end of video at frame {count-1}")
                break
            sec += self.required_frame_rate
            vid_cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)

    """Extract frames from videos and save them as images.

    Args:
        vid_dir: The path to the directory containing the videos.
        out_dir: The path to the directory where the images will be saved.
        img_frmt: The image format to use for saving the images. Defaults to 'jpg'.
        required_frame_rate: The frame rate at which to extract frames from the videos.
            Defaults to 5 frames per second.
        start_from_seconds: The number of seconds into the video to start extracting frames.
            Defaults to 0 (start from the beginning of the video).
    """


if __name__ == '__main__':
    vid_dir = settings.VIDEO_DIRPATH
    out_dir = settings.OUTDIR
    required_frame_rate = settings.REQUIRED_FRAME_RATE
    start_from_seconds = settings.START_FROM_SECOND
    img_frmt = settings.REQUIRED_IMAGE_FORMAT
    img_width = settings.REQUIRED_IMAGE_WIDTH
    verbose = True

    vid_dir_path = Path(vid_dir)
    out_dir = Path(out_dir)
    if vid_dir_path.exists():
        # Get start time
        time_start = time.time()
        vids = [vid for vid in vid_dir_path.iterdir()]
        frame_extractor = FrameExtractor(
            out_dir, img_frmt, required_frame_rate, start_from_seconds, img_width, verbose)
        with ThreadPoolExecutor() as executor:
            list(executor.map(frame_extractor.extract_frames, vids))
        time_end = time.time()
        if verbose:
            print(
                f"It took {time_end-time_start:.2f} seconds for conversion.")
    else:
        print(f"The specified path ({vid_dir}) does not exist!")