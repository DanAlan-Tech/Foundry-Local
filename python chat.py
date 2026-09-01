import cv2
import tkinter as tk
from tkinter import filedialog
from ultralytics import YOLO
import ollama
import os
import sys

def select_local_file():
    """Opens a local file dialog window to choose a video file."""
    root = tk.Tk()
    root.withdraw()
    print(" Opening local file explorer... Please select a video file.")
    return filedialog.askopenfilename(
        title="Select Video File for Multimodal Weapon Analysis",
        filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv")]
    )

def run_local_vision_analysis(video_path):
    """Processes video, flags firearms/weapons, and saves relevant frames locally."""
    # Defensively verify file existence before interacting with OpenCV bindings
    if not video_path or not os.path.exists(video_path):
        print(" Error: The selected file path is invalid or empty.")
        return None

    print(f" Initializing localized vision pipeline for: {os.path.basename(video_path)}")
    
    weights_path = "weapons_yolov8.pt"
    fallback_weights = "yolov8x.pt"
    
    # SECURITY CONTROL: Absolute enforcement of local assets to prevent silent remote downloads
    if os.path.exists(weights_path):
        print(f" Loading custom firearm & weapon detection weights: {weights_path}")
        model = YOLO(weights_path)
        weapon_targets = None 
    elif os.path.exists(fallback_weights):
        print(f" '{weights_path}' not found. Using verified local fallback: {fallback_weights}")
        model = YOLO(fallback_weights)
        weapon_targets = {'knife', 'scissors', 'baseball bat'}
    else:
        print(f" CRITICAL ERROR: No local model weights found ('{weights_path}' or '{fallback_weights}').")
        print(" Remote fallback downloads are disabled for security compliance. Exiting pipeline.")
        return None

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(" Error: Could not open the selected video file.")
        return None

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0  # Prevent DivisionByZero anomalies from corrupted metadata
        
    frame_count = 0
    flagged_frames = []
    
    output_dir = "local_threat_snapshots"
    os.makedirs(output_dir, exist_ok=True)

    print(" Scanning frames offline for firearms and weapons...")
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            
            # Sampling rate normalization
            if frame_count % max(1, int(fps / 2)) == 0:
                results = model(frame, verbose=False)
                timestamp = round(frame_count / fps, 2)
                
                for result in results:
                    for box in result.boxes:
                        label = model.names[int(box.cls)].lower()
                        confidence = float(box.conf)
                    
                        is_weapon = False
                        if weapon_targets is None: 
                            if any(w in label for w in ['gun', 'pistol', 'rifle', 'knife', 'weapon']) and confidence > 0.45:
                                is_weapon = True
                        else: 
                            if label in weapon_targets and confidence > 0.45:
                                is_weapon = True
                                
                        if is_weapon:
                            # SECURITY NOTE: Kept deterministic to prevent potential file injection/traversal vectors
                            safe_filename = f"threat_at_{timestamp}s.jpg".replace("..", "")
                            frame_path = os.path.join(output_dir, safe_filename)
                         
                            cv2.imwrite(frame_path, frame)
                            flagged_frames.append({"path": frame_path, "label": label, "time": timestamp, "conf": confidence})
                            break
    finally:
        cap.release()

    return flagged_frames

def get_available_ollama_models():
    """Returns the locally available Ollama model names, if any."""
    try:
        response = ollama.list()
        if not isinstance(response, dict):
            return []

        model_entries = response.get('models', [])
        names = []
        for item in model_entries:
            if isinstance(item, dict):
                name = item.get('name') or item.get('model')
                if name:
                    names.append(str(name))
            else:
                names.append(str(item))
        return names
    except Exception:
        return []

def pick_vision_model():
    """Select a compatible vision model if one exists locally; otherwise return None."""
    available = get_available_ollama_models()
    normalized = {name.lower() for name in available}

    preferred = [
        'llama3.2:latest', 'llama3.2', 'llama3.2-vision:latest', 'llama3.2-vision',
        'llava:latest', 'llava', 'bakllava:latest', 'bakllava',
    ]

    for candidate in preferred:
        if candidate.lower() in normalized:
            return candidate

    for name in available:
        lower_name = name.lower()
        if 'llama3.2' in lower_name or 'vision' in lower_name or 'llava' in lower_name:
            return name

    return None

def build_fallback_report(flagged_frames):
    """Generates a useful report when the multimodal model is unavailable or incompatible."""
    highest_conf_threat = max(flagged_frames, key=lambda x: x['conf'])
    strongest_label = highest_conf_threat['label']
    highest_conf = highest_conf_threat['conf']
    total = len(flagged_frames)

    return (
        f" Local multimodal model unavailable or incompatible with the current Ollama backend.\n"
        f"The vision pipeline still detected {total} suspicious frame(s). Strongest signal: '{strongest_label}' "
        f"at {highest_conf:.2%} confidence.\n\n"
        f"Review Area: Local validation complete, manual intervention recommended."
    )

def generate_multimodal_report(flagged_frames):
    """Feeds physical images into local Llama 3.2 Vision to perform multimodal NLP verification."""
    if not flagged_frames:
        return " Offline Analysis Complete: No firearms or weapon-like profiles were detected by the computer vision layer."

    print(f" Local vision layers flagged {len(flagged_frames)} suspicious frames.")

    highest_conf_threat = max(flagged_frames, key=lambda x: x['conf'])
    image_to_analyze = highest_conf_threat['path']
    model_name = pick_vision_model()

    if not model_name:
        print(" No compatible local vision model is available. Using offline CV fallback report.")
        return build_fallback_report(flagged_frames)

    print(f" Initiating local Multimodal LLM verification via Ollama ({model_name})...")

    local_prompt = f"""
    You are an advanced local security intelligence system. 
    A local computer vision filter flagged this specific image frame because it detected a potential threat categorized as '{highest_conf_threat['label']}' at timestamp {highest_conf_threat['time']} seconds.
    
    Visually inspect this image and provide:
    1. A verification confirming if a firearm, weapon, or imminent human threat is physically present in the frame.
    2. A Natural Language description of what actions, environment, or intent you observe in the image.
    3. A final Threat Assessment rating (Critical, Elevated, or Low/False Positive).
    """

    try:
        response = ollama.chat(
            model=model_name,
            messages=[
                {
                    'role': 'user',
                    'content': local_prompt,
                    'images': [image_to_analyze]
                }
            ]
        )
        return response['message']['content']
    except Exception as e:
        error_text = str(e).lower()
        if 'unknown model architecture' in error_text or 'mllama' in error_text:
            print(" Detected an unsupported multimodal model architecture from the active Ollama backend.")
            return build_fallback_report(flagged_frames)

        return f" Local Multimodal AI error: System communication interrupted dynamically."


if __name__ == "__main__":
    print("=== MULTIMODAL LOCAL VIDEO THREAT ANALYSIS MODALITY ===")
    
    video_file = select_local_file()
    if video_file:
        detected_threat_frames = run_local_vision_analysis(video_file)
        
        if detected_threat_frames:
            final_report = generate_multimodal_report(detected_threat_frames)
            print("\n" + "="*50)
            print(" LOCAL MULTIMODAL INTEL REPORT")
            print("="*50)
            print(final_report)
        else:
            print(" Analysis Complete: No threat indicators identified in video frames.")
    else:
        print(" Action cancelled: No local video file was chosen.")
