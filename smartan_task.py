import cv2
import mediapipe as mp
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import threading
import time
import json
from datetime import datetime

class PoseAnalysisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Pose Analysis Tool - Smartan FitTech")
        self.root.geometry("1500x1000")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize MediaPipe
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.7, min_tracking_confidence=0.7)
        
        # Video capture and playback
        self.cap = None
        self.video_cap = None
        self.is_recording = False
        self.is_playing_video = False
        self.video_thread = None
        self.video_playback_thread = None
        
        # Video clip analysis
        self.video_file_path = None
        self.current_frame_idx = 0
        self.total_frames = 0
        self.fps = 30
        self.video_analysis_results = []
        
        # Variables
        self.current_image = None
        self.analyzed_image = None
        self.original_frame = None
        
        # Exercise tracking
        self.exercise_mode = tk.StringVar(value="bicep_curl")
        self.exercise_state = "down"  
        self.pushup_state = "up"
        self.rep_count = 0
        
        # Exercise history
        self.bicep_angles = []
        self.pushup_angles = []
        self.analysis_data = []
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main title
        title_frame = tk.Frame(self.root, bg='#f0f0f0')
        title_frame.pack(pady=10)
        
        title_label = tk.Label(title_frame, text="Posture Analysis For Smartan FitTech", 
                             font=('Arial', 24, 'bold'), 
                             bg='#f0f0f0', fg='#2c3e50')
        title_label.pack()
        
        # Control panel
        control_frame = tk.Frame(self.root, bg='#f0f0f0')
        control_frame.pack(pady=10)
        
        # Exercise selection
        exercise_frame = tk.Frame(control_frame, bg='#f0f0f0')
        exercise_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(exercise_frame, text="Exercise Mode:", font=('Arial', 12, 'bold'), 
                bg='#f0f0f0').pack()
        
        exercise_combo = ttk.Combobox(exercise_frame, textvariable=self.exercise_mode,
                                    values=["bicep_curl", "pushup", "squat", "general_pose"],
                                    state="readonly", width=15)
        exercise_combo.pack(pady=5)
        exercise_combo.bind("<<ComboboxSelected>>", self.on_exercise_change)
        
        # File selection
        file_frame = tk.Frame(control_frame, bg='#f0f0f0')
        file_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(file_frame, text="Media File:", font=('Arial', 12, 'bold'), 
                bg='#f0f0f0').pack()
        
        self.file_path_var = tk.StringVar()
        self.file_entry = tk.Entry(file_frame, textvariable=self.file_path_var, 
                                  width=35, font=('Arial', 10))
        self.file_entry.pack(pady=2)
        
        file_button_frame = tk.Frame(file_frame, bg='#f0f0f0')
        file_button_frame.pack(pady=2)
        
        browse_img_btn = tk.Button(file_button_frame, text="Browse Image", 
                                  command=self.browse_image,
                                  bg='#3498db', fg='white', 
                                  font=('Arial', 8, 'bold'),
                                  padx=8)
        browse_img_btn.pack(side=tk.LEFT, padx=2)
        
        browse_video_btn = tk.Button(file_button_frame, text="Browse Video", 
                                    command=self.browse_video,
                                    bg='#9b59b6', fg='white', 
                                    font=('Arial', 8, 'bold'),
                                    padx=8)
        browse_video_btn.pack(side=tk.LEFT, padx=2)
        
        # Buttons
        button_frame = tk.Frame(control_frame, bg='#f0f0f0')
        button_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(button_frame, text="Controls:", font=('Arial', 12, 'bold'), 
                bg='#f0f0f0').pack()
        
        button_row1 = tk.Frame(button_frame, bg='#f0f0f0')
        button_row1.pack(pady=2)
        
        analyze_btn = tk.Button(button_row1, text="Analyze Image", 
                               command=self.analyze_pose,
                               bg='#27ae60', fg='white', 
                               font=('Arial', 9, 'bold'),
                               padx=10)
        analyze_btn.pack(side=tk.LEFT, padx=2)
        
        analyze_video_btn = tk.Button(button_row1, text="Analyze Video", 
                                     command=self.analyze_video_clip,
                                     bg='#8e44ad', fg='white', 
                                     font=('Arial', 9, 'bold'),
                                     padx=10)
        analyze_video_btn.pack(side=tk.LEFT, padx=2)
        
        button_row2 = tk.Frame(button_frame, bg='#f0f0f0')
        button_row2.pack(pady=2)
        
        self.start_video_btn = tk.Button(button_row2, text="Start Webcam", 
                                        command=self.start_video,
                                        bg='#e74c3c', fg='white', 
                                        font=('Arial', 9, 'bold'),
                                        padx=10)
        self.start_video_btn.pack(side=tk.LEFT, padx=2)
        
        self.stop_video_btn = tk.Button(button_row2, text="Stop", 
                                       command=self.stop_video,
                                       bg='#95a5a6', fg='white', 
                                       font=('Arial', 9, 'bold'),
                                       padx=10, state=tk.DISABLED)
        self.stop_video_btn.pack(side=tk.LEFT, padx=2)
        
        button_row3 = tk.Frame(button_frame, bg='#f0f0f0')
        button_row3.pack(pady=2)
        
        self.play_video_btn = tk.Button(button_row3, text="Play Video", 
                                       command=self.play_video_clip,
                                       bg='#e67e22', fg='white', 
                                       font=('Arial', 9, 'bold'),
                                       padx=10, state=tk.DISABLED)
        self.play_video_btn.pack(side=tk.LEFT, padx=2)

        content_frame = tk.Frame(self.root, bg='#f0f0f0')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Image display area in the UI
        image_frame = tk.LabelFrame(content_frame, text="Video/Image Analysis", 
                                   font=('Arial', 12, 'bold'),
                                   bg='#f0f0f0', fg='#2c3e50')
        image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.canvas = tk.Canvas(image_frame, bg='white', width=800, height=600)
        self.canvas.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        video_control_frame = tk.Frame(image_frame, bg='#f0f0f0')
        video_control_frame.pack(fill=tk.X, padx=10, pady=5)

        self.video_progress = ttk.Scale(video_control_frame, from_=0, to=100, 
                                       orient=tk.HORIZONTAL, length=400,
                                       command=self.on_video_seek)
        self.video_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.frame_info_var = tk.StringVar(value="Frame: 0/0")
        tk.Label(video_control_frame, textvariable=self.frame_info_var, 
                font=('Arial', 9), bg='#f0f0f0').pack(side=tk.RIGHT, padx=5)
        
        # Analysis result area
        results_frame = tk.LabelFrame(content_frame, text="Analysis Results", 
                                     font=('Arial', 12, 'bold'),
                                     bg='#f0f0f0', fg='#2c3e50',
                                     width=450)
        results_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        results_frame.pack_propagate(False)
        
        
        self.exercise_state_var = tk.StringVar(value="State: Ready")
        
        
        # Exercise-specific Analysis
        self.exercise_frame = tk.LabelFrame(results_frame, text="Exercise Analysis", 
                                          font=('Arial', 11, 'bold'),
                                          bg='#f0f0f0', fg='#8e44ad')
        self.exercise_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.primary_angle_var = tk.StringVar(value="Primary Angle: --°")
        self.secondary_angle_var = tk.StringVar(value="Secondary Angle: --°")
        self.form_status_var = tk.StringVar(value="Form: Not analyzed")
        
        tk.Label(self.exercise_frame, textvariable=self.primary_angle_var, 
                font=('Arial', 10), bg='#f0f0f0').pack(pady=1)
        tk.Label(self.exercise_frame, textvariable=self.secondary_angle_var, 
                font=('Arial', 10), bg='#f0f0f0').pack(pady=1)
        self.form_status_label = tk.Label(self.exercise_frame, textvariable=self.form_status_var, 
                                         font=('Arial', 10, 'bold'), bg='#f0f0f0')
        self.form_status_label.pack(pady=2)
        
        # Posture Analysis
        posture_frame = tk.LabelFrame(results_frame, text="🏃 Posture Analysis", 
                                     font=('Arial', 11, 'bold'),
                                     bg='#f0f0f0', fg='#2ecc71')
        posture_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.posture_status_var = tk.StringVar(value="Status: Not analyzed")
        self.posture_status_label = tk.Label(posture_frame, textvariable=self.posture_status_var, 
                                            font=('Arial', 10, 'bold'), bg='#f0f0f0')
        self.posture_status_label.pack(pady=5)
        
        # Video Analysis Summary
        summary_frame = tk.LabelFrame(results_frame, text="📊 Video Summary", 
                                     font=('Arial', 11, 'bold'),
                                     bg='#f0f0f0', fg='#34495e')
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.summary_text = tk.Text(summary_frame, wrap=tk.WORD, 
                                   font=('Arial', 9), height=6,
                                   bg='#ffffff', fg='#2c3e50')
        summary_scrollbar = tk.Scrollbar(summary_frame, orient=tk.VERTICAL, 
                                        command=self.summary_text.yview)
        self.summary_text.configure(yscrollcommand=summary_scrollbar.set)
        
        self.summary_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        summary_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Real-time feedback
        feedback_frame = tk.LabelFrame(results_frame, text="📋 Real-time Feedback", 
                                      font=('Arial', 11, 'bold'),
                                      bg='#f0f0f0', fg='#34495e')
        feedback_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.feedback_text = tk.Text(feedback_frame, wrap=tk.WORD, 
                                    font=('Arial', 9), height=12,
                                    bg='#ffffff', fg='#2c3e50')
        scrollbar = tk.Scrollbar(feedback_frame, orient=tk.VERTICAL, command=self.feedback_text.yview)
        self.feedback_text.configure(yscrollcommand=scrollbar.set)
        
        self.feedback_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready - Select exercise mode and start analysis")
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                             relief=tk.SUNKEN, anchor=tk.W,
                             bg='#ecf0f1', font=('Arial', 9))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def on_exercise_change(self, event=None):
        self.reset_count()
        mode = self.exercise_mode.get()
        if mode == "bicep_curl":
            self.exercise_frame.config(text="Bicep Curl Analysis")
        elif mode == "pushup":
            self.exercise_frame.config(text="Push-up Analysis")
        elif mode == "squat":
            self.exercise_frame.config(text="Squat Analysis")
        else:
            self.exercise_frame.config(text="General Pose Analysis")
        
        self.status_var.set(f"Exercise mode changed to: {mode.replace('_', ' ').title()}")
    
    
    def browse_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.file_path_var.set(file_path)
            self.load_image(file_path)
    
    def browse_video(self):
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv"),
                ("MP4 files", "*.mp4"),
                ("AVI files", "*.avi"),
                ("MOV files", "*.mov"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.file_path_var.set(file_path)
            self.load_video_info(file_path)
    
    def load_video_info(self, file_path):
        try:
            self.video_file_path = file_path
            cap = cv2.VideoCapture(file_path)
            self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = int(cap.get(cv2.CAP_PROP_FPS))
            cap.release()
            
            self.current_frame_idx = 0
            self.video_progress.config(to=self.total_frames-1)
            self.frame_info_var.set(f"Frame: 0/{self.total_frames}")
            self.play_video_btn.config(state=tk.NORMAL)
            
            # Load first frame
            cap = cv2.VideoCapture(file_path)
            ret, frame = cap.read()
            if ret:
                self.display_image(frame)
            cap.release()
            
            self.status_var.set(f"Video loaded: {os.path.basename(file_path)} ({self.total_frames} frames, {self.fps} FPS)")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load video: {str(e)}")
            self.status_var.set("Error loading video")
    
    def on_video_seek(self, value):
        if self.video_file_path and not self.is_playing_video:
            try:
                frame_idx = int(float(value))
                cap = cv2.VideoCapture(self.video_file_path)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if ret:
                    self.current_frame_idx = frame_idx
                    self.frame_info_var.set(f"Frame: {frame_idx}/{self.total_frames}")
                    analyzed_frame = self.analyze_frame(frame.copy())
                    self.display_image(analyzed_frame)
                cap.release()
            except Exception as e:
                print(f"Seek error: {e}")
    
    def play_video_clip(self):
        if not self.video_file_path:
            messagebox.showwarning("Warning", "Please load a video file first")
            return
        
        if not self.is_playing_video:
            self.is_playing_video = True
            self.play_video_btn.config(text="Pause", bg='#f39c12')
            self.video_playback_thread = threading.Thread(target=self.video_playback_loop, daemon=True)
            self.video_playback_thread.start()
        else:
            self.is_playing_video = False
            self.play_video_btn.config(text="Play Video", bg='#e67e22')
    
    def video_playback_loop(self):
        cap = cv2.VideoCapture(self.video_file_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame_idx)
        
        while self.is_playing_video and self.current_frame_idx < self.total_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            analyzed_frame = self.analyze_frame(frame.copy())
            
            # Update UI in main thread
            self.root.after(0, self.update_video_playback, analyzed_frame)
            
            # Control playback speed
            time.sleep(1.0 / max(self.fps, 1))
            self.current_frame_idx += 1
        
        cap.release()
        self.is_playing_video = False
        self.root.after(0, lambda: self.play_video_btn.config(text="Play Video", bg='#e67e22'))
    
    def update_video_playback(self, frame):
        self.display_image(frame)
        self.video_progress.set(self.current_frame_idx)
        self.frame_info_var.set(f"Frame: {self.current_frame_idx}/{self.total_frames}")
    
    def analyze_video_clip(self):
        if not self.video_file_path:
            messagebox.showwarning("Warning", "Please load a video file first")
            return
        
        # Create progress dialog
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Analyzing Video")
        progress_window.geometry("400x150")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        tk.Label(progress_window, text="Analyzing video clip...", 
                font=('Arial', 12)).pack(pady=20)
        
        progress_bar = ttk.Progressbar(progress_window, length=300, mode='determinate')
        progress_bar.pack(pady=10)
        
        progress_label = tk.Label(progress_window, text="Frame: 0/0")
        progress_label.pack(pady=5)
        
        # Start analysis in separate thread
        def analyze_thread():
            try:
                self.video_analysis_results = []
                cap = cv2.VideoCapture(self.video_file_path)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                
                frame_idx = 0
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Analyze frame
                    results = self.analyze_frame_for_data(frame)
                    if results:
                        results['frame'] = frame_idx
                        results['timestamp'] = frame_idx / self.fps
                        self.video_analysis_results.append(results)
                    
                    # Update progress
                    progress = (frame_idx / total_frames) * 100
                    progress_window.after(0, lambda p=progress, f=frame_idx, t=total_frames: 
                                        self.update_progress(progress_bar, progress_label, p, f, t))
                    
                    frame_idx += 1
                
                cap.release()
                
                # Generate summary
                self.generate_video_summary()
                
                # Close progress dialog
                progress_window.after(0, progress_window.destroy)
                self.status_var.set(f"Video analysis complete - {len(self.video_analysis_results)} frames analyzed")
                
            except Exception as e:
                progress_window.after(0, progress_window.destroy)
                messagebox.showerror("Error", f"Video analysis failed: {str(e)}")
        
        analysis_thread = threading.Thread(target=analyze_thread, daemon=True)
        analysis_thread.start()
    
    def update_progress(self, progress_bar, progress_label, progress, frame, total):
        progress_bar['value'] = progress
        progress_label.config(text=f"Frame: {frame}/{total}")
    
    def analyze_frame_for_data(self, frame):
        """Analyze frame and return data without UI updates"""
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(image)
        
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            
            data = {
                'pose_detected': True,
                'landmarks': [(lm.x, lm.y, lm.z) for lm in landmarks]
            }
            
            # Exercise-specific analysis
            if self.exercise_mode.get() == "bicep_curl":
                elbow_angle, form_status = self.analyze_bicep_curl_data(landmarks, frame)
                data.update({
                    'exercise': 'bicep_curl',
                    'elbow_angle': elbow_angle,
                    'form_status': form_status
                })
            elif self.exercise_mode.get() == "pushup":
                elbow_angle, body_angle, form_status = self.analyze_pushup_data(landmarks, frame)
                data.update({
                    'exercise': 'pushup',
                    'elbow_angle': elbow_angle,
                    'body_angle': body_angle,
                    'form_status': form_status
                })
            elif self.exercise_mode.get() == "squat":
                knee_angle, hip_angle, form_status = self.analyze_squat_data(landmarks, frame)
                data.update({
                    'exercise': 'squat',
                    'knee_angle': knee_angle,
                    'hip_angle': hip_angle,
                    'form_status': form_status
                })
            
            # Posture analysis
            posture_data = self.analyze_posture_data(landmarks, frame)
            data.update(posture_data)
            
            return data
        
        return {'pose_detected': False}
    
    def analyze_bicep_curl_data(self, landmarks, frame):
        """Analyze bicep curl without UI updates"""
        l_shoulder = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_SHOULDER.value, frame)
        l_elbow = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_ELBOW.value, frame)
        l_wrist = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_WRIST.value, frame)
        
        elbow_angle = self.calculate_angle(l_shoulder, l_elbow, l_wrist)
        form_status = "Good Form" if 30 <= elbow_angle <= 170 else "Check Form"
        
        return elbow_angle, form_status
    
    def analyze_pushup_data(self, landmarks, frame):
        """Analyze pushup without UI updates"""
        l_shoulder = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_SHOULDER.value, frame)
        l_elbow = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_ELBOW.value, frame)
        l_wrist = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_WRIST.value, frame)
        l_hip = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_HIP.value, frame)
        l_knee = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_KNEE.value, frame)
        
        elbow_angle = self.calculate_angle(l_shoulder, l_elbow, l_wrist)
        body_angle = self.calculate_angle(l_shoulder, l_hip, l_knee)
        
        elbow_form = "Good" if 70 <= elbow_angle <= 180 else "Check Elbow"
        body_form = "Good" if 160 <= body_angle <= 180 else "Straighten Body"
        form_status = "Good Form" if elbow_form == "Good" and body_form == "Good" else "Check Form"
        
        return elbow_angle, body_angle, form_status
    
    def analyze_squat_data(self, landmarks, frame):
        """Analyze squat without UI updates"""
        l_hip = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_HIP.value, frame)
        l_knee = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_KNEE.value, frame)
        l_ankle = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_ANKLE.value, frame)
        l_shoulder = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_SHOULDER.value, frame)
        
        knee_angle = self.calculate_angle(l_hip, l_knee, l_ankle)
        hip_angle = self.calculate_angle(l_shoulder, l_hip, l_knee)
        
        knee_form = "Good" if 70 <= knee_angle <= 180 else "Check Depth"
        hip_form = "Good" if 160 <= hip_angle <= 180 else "Check Posture"
        form_status = "Good Form" if knee_form == "Good" and hip_form == "Good" else "Check Form"
        
        return knee_angle, hip_angle, form_status
    
    def analyze_posture_data(self, landmarks, frame):
        """Analyze posture without UI updates"""
        l_shoulder = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_SHOULDER.value, frame)
        r_shoulder = self.get_coords(landmarks, self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value, frame)
        l_hip = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_HIP.value, frame)
        r_hip = self.get_coords(landmarks, self.mp_pose.PoseLandmark.RIGHT_HIP.value, frame)
        
        shoulder_symmetry = abs(l_shoulder[1] - r_shoulder[1])
        hip_symmetry = abs(l_hip[1] - r_hip[1])
        
        posture_status = "Good Posture" if shoulder_symmetry <= 30 and hip_symmetry <= 30 else "Check Posture"
        
        return {
            'shoulder_symmetry': shoulder_symmetry,
            'hip_symmetry': hip_symmetry,
            'posture_status': posture_status
        }
    
    def generate_video_summary(self):
        """Generate analysis summary from video results"""
        if not self.video_analysis_results:
            return
        
        exercise = self.exercise_mode.get()
        total_frames = len(self.video_analysis_results)
        duration = total_frames / self.fps if self.fps > 0 else 0
        
        # Calculate statistics
        good_form_count = sum(1 for r in self.video_analysis_results 
                             if r.get('form_status') == 'Good Form')
        good_form_percentage = (good_form_count / total_frames) * 100 if total_frames > 0 else 0
        
        good_posture_count = sum(1 for r in self.video_analysis_results 
                                if r.get('posture_status') == 'Good Posture')
        good_posture_percentage = (good_posture_count / total_frames) * 100 if total_frames > 0 else 0
        
        summary = f"=== VIDEO ANALYSIS SUMMARY ===\n"
        summary += f"Exercise: {exercise.replace('_', ' ').title()}\n"
        summary += f"Duration: {duration:.1f} seconds\n"
        summary += f"Frames Analyzed: {total_frames}\n\n"
        
        summary += f"FORM ANALYSIS:\n"
        summary += f"• Good Form: {good_form_percentage:.1f}% ({good_form_count}/{total_frames} frames)\n"
        summary += f"• Posture Quality: {good_posture_percentage:.1f}% good posture\n\n"
        
        if exercise == "bicep_curl":
            angles = [r.get('elbow_angle', 0) for r in self.video_analysis_results if 'elbow_angle' in r]
            if angles:
                summary += f"BICEP CURL METRICS:\n"
                summary += f"• Average Elbow Angle: {np.mean(angles):.1f}\n"
                summary += f"• Range: {min(angles):.1f} - {max(angles):.1f}\n"
                summary += f"• Recommended Range: 30° - 170°\n\n"
        
        elif exercise == "pushup":
            elbow_angles = [r.get('elbow_angle', 0) for r in self.video_analysis_results if 'elbow_angle' in r]
            body_angles = [r.get('body_angle', 0) for r in self.video_analysis_results if 'body_angle' in r]
            if elbow_angles and body_angles:
                summary += f"PUSH-UP METRICS:\n"
                summary += f"• Average Elbow Angle: {np.mean(elbow_angles):.1f}\n"
                summary += f"• Average Body Alignment: {np.mean(body_angles):.1f}\n"
                summary += f"• Elbow Range: {min(elbow_angles):.1f} - {max(elbow_angles):.1f}\n\n"
        
        elif exercise == "squat":
            knee_angles = [r.get('knee_angle', 0) for r in self.video_analysis_results if 'knee_angle' in r]
            hip_angles = [r.get('hip_angle', 0) for r in self.video_analysis_results if 'hip_angle' in r]
            if knee_angles and hip_angles:
                summary += f"SQUAT METRICS:\n"
                summary += f"• Average Knee Angle: {np.mean(knee_angles):.1f}°\n"
                summary += f"• Average Hip Angle: {np.mean(hip_angles):.1f}°\n"
                summary += f"• Knee Range: {min(knee_angles):.1f}° - {max(knee_angles):.1f}°\n\n"
        
        # Recommendations
        summary += f"RECOMMENDATIONS:\n"
        if good_form_percentage < 80:
            summary += f"• Focus on maintaining proper form throughout the movement\n"
        if good_posture_percentage < 80:
            summary += f"• Work on body alignment and posture\n"
        if good_form_percentage >= 90:
            summary += f"• Excellent form consistency!\n"
        
        summary += f"\nAnalysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Update summary text widget
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, summary)
    
    # def export_analysis_data(self):
    #     """Export analysis data to JSON file"""
    #     if not self.video_analysis_results and not self.analysis_data:
    #         messagebox.showwarning("Warning", "No analysis data to export")
    #         return
        
    #     file_path = filedialog.asksaveasfilename(
    #         title="Export Analysis Data",
    #         defaultextension=".json",
    #         filetypes=[
    #             ("JSON files", "*.json"),
    #             ("All files", "*.*")
    #         ]
    #     )
        
    #     if file_path:
    #         try:
    #             export_data = {
    #                 'exercise_mode': self.exercise_mode.get(),
    #                 'export_timestamp': datetime.now().isoformat(),
    #                 'video_file': self.video_file_path,
    #                 'total_reps': self.rep_count,
    #                 'video_analysis_results': self.video_analysis_results,
    #                 'realtime_data': self.analysis_data
    #             }
                
    #             with open(file_path, 'w') as f:
    #                 json.dump(export_data, f, indent=2)
                
    #             messagebox.showinfo("Success", f"Analysis data exported to:\n{file_path}")
    #             self.status_var.set(f"Data exported to {os.path.basename(file_path)}")
                
    #         except Exception as e:
    #             messagebox.showerror("Error", f"Failed to export data: {str(e)}")
    
    def start_video(self):
        if not self.is_recording:
            try:
                self.cap = cv2.VideoCapture(0)
                if not self.cap.isOpened():
                    messagebox.showerror("Error", "Could not access camera")
                    return
                
                self.is_recording = True
                self.start_video_btn.config(state=tk.DISABLED)
                self.stop_video_btn.config(state=tk.NORMAL)
                
                self.video_thread = threading.Thread(target=self.video_loop, daemon=True)
                self.video_thread.start()
                
                self.status_var.set("Real-time webcam analysis started")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start video: {str(e)}")
    
    def stop_video(self):
        self.is_recording = False
        self.is_playing_video = False
        if self.cap:
            self.cap.release()
        
        self.start_video_btn.config(state=tk.NORMAL)
        self.stop_video_btn.config(state=tk.DISABLED)
        self.play_video_btn.config(text="Play Video", bg='#e67e22')
        self.status_var.set("Video analysis stopped")
    
    def video_loop(self):
        while self.is_recording:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Analyze the frame
            analyzed_frame = self.analyze_frame(frame)
            
            # Display the frame
            self.root.after(0, self.display_image, analyzed_frame)
            
            time.sleep(0.03)  # ~30 FPS
    
    def load_image(self, file_path):
        try:
            # Load image with OpenCV
            self.original_frame = cv2.imread(file_path)
            if self.original_frame is None:
                raise ValueError("Could not load image")
            
            # Display original image on canvas
            self.display_image(self.original_frame)
            self.status_var.set(f"Image loaded: {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")
            self.status_var.set("Error loading image")
    
    def display_image(self, cv_image):
        try:
            # Convert from BGR to RGB
            rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width, canvas_height = 800, 600
            
            # Calculate scaling to fit canvas while maintaining aspect ratio
            img_height, img_width = rgb_image.shape[:2]
            scale = min(canvas_width/img_width, canvas_height/img_height)
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # Resize image
            resized_image = cv2.resize(rgb_image, (new_width, new_height))
            
            # Convert to PIL Image and then to PhotoImage
            pil_image = Image.fromarray(resized_image)
            self.current_image = ImageTk.PhotoImage(pil_image)
            
            # Clear canvas and display image
            self.canvas.delete("all")
            x = (canvas_width - new_width) // 2
            y = (canvas_height - new_height) // 2
            self.canvas.create_image(x, y, anchor=tk.NW, image=self.current_image)
            
        except Exception as e:
            print(f"Display error: {e}")
    
    def calculate_angle(self, a, b, c):
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - \
                  np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        if angle > 180.0:
            angle = 360 - angle
        return angle
    
    def analyze_bicep_curl(self, landmarks, frame):
        # Get left arm keypoints
        l_shoulder = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_SHOULDER.value, frame)
        l_elbow = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_ELBOW.value, frame)
        l_wrist = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_WRIST.value, frame)
        
        # Calculate elbow angle
        elbow_angle = self.calculate_angle(l_shoulder, l_elbow, l_wrist)
        self.bicep_angles.append(elbow_angle)
        
        # # Rep counting logic
        # if elbow_angle > 160 and self.exercise_state == "up":
        #     self.exercise_state = "down"
        # elif elbow_angle < 50 and self.exercise_state == "down":
        #     self.exercise_state = "up"
        #     self.rep_count += 1
        #     self.rep_count_var.set(f"Reps: {self.rep_count}")
            
        
        # Form analysis
        form_status = "Good Form" if 30 <= elbow_angle <= 170 else "Check Form"
        
        # Update UI
        self.primary_angle_var.set(f"Elbow Angle: {int(elbow_angle)}°")
        self.secondary_angle_var.set(f"Range: 30-170°")
        self.form_status_var.set(f"Form: {form_status}")
        self.form_status_label.config(fg='green' if form_status == "Good Form" else 'red')
        self.exercise_state_var.set(f"State: {self.exercise_state.title()}")
        
        return elbow_angle, form_status
    
    def analyze_pushup(self, landmarks, frame):
        # Get keypoints for pushup analysis
        l_shoulder = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_SHOULDER.value, frame)
        l_elbow = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_ELBOW.value, frame)
        l_wrist = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_WRIST.value, frame)
        l_hip = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_HIP.value, frame)
        l_knee = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_KNEE.value, frame)
        
        # Calculate angles
        elbow_angle = self.calculate_angle(l_shoulder, l_elbow, l_wrist)
        body_angle = self.calculate_angle(l_shoulder, l_hip, l_knee)
        
        self.pushup_angles.append(elbow_angle)
        
        # Rep counting for pushups
        if elbow_angle < 90 and self.pushup_state == "up":
            self.pushup_state = "down"
        elif elbow_angle > 160 and self.pushup_state == "down":
            self.pushup_state = "up"
            self.rep_count += 1
            self.rep_count_var.set(f"Reps: {self.rep_count}")
    
        # Form analysis
        elbow_form = "Good" if 70 <= elbow_angle <= 180 else "Check Elbow"
        body_form = "Good" if 160 <= body_angle <= 180 else "Straighten Body"
        overall_form = "Good Form" if elbow_form == "Good" and body_form == "Good" else "Check Form"
        
        # Update UI
        self.primary_angle_var.set(f"Elbow Angle: {int(elbow_angle)}")
        self.secondary_angle_var.set(f"Body Angle: {int(body_angle)}")
        self.form_status_var.set(f"Form: {overall_form}")
        self.form_status_label.config(fg='green' if overall_form == "Good Form" else 'red')
        self.exercise_state_var.set(f"State: {self.pushup_state.title()}")

        
        return elbow_angle, body_angle, overall_form
    
    def analyze_squat(self, landmarks, frame):
        # Get keypoints for squat analysis
        l_hip = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_HIP.value, frame)
        l_knee = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_KNEE.value, frame)
        l_ankle = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_ANKLE.value, frame)
        l_shoulder = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_SHOULDER.value, frame)
        
        # Calculate angles
        knee_angle = self.calculate_angle(l_hip, l_knee, l_ankle)
        hip_angle = self.calculate_angle(l_shoulder, l_hip, l_knee)
        
        # Rep counting for squats
        if knee_angle < 90 and self.exercise_state == "up":
            self.exercise_state = "down"
        elif knee_angle > 90 and self.exercise_state == "down":
            self.exercise_state = "up"
            self.rep_count += 1
            self.rep_count_var.set(f"Reps: {self.rep_count}")
        
        # Form analysis
        knee_form = "Good" if 70 <= knee_angle <= 180 else "Check Depth"
        hip_form = "Good" if 70 <= hip_angle <= 180 else "Check Posture"
        overall_form = "Good Form" if knee_form == "Good" and hip_form == "Good" else "Check Form"
        
        # Update UI
        self.primary_angle_var.set(f"Knee Angle: {int(knee_angle)}°")
        self.secondary_angle_var.set(f"Hip Angle: {int(hip_angle)}°")
        self.form_status_var.set(f"Form: {overall_form}")
        self.form_status_label.config(fg='green' if overall_form == "Good Form" else 'red')
        self.exercise_state_var.set(f"State: {self.exercise_state.title()}")

        return knee_angle, hip_angle, overall_form
    
    def get_coords(self, landmarks, idx, frame):
        lm = landmarks[idx]
        return [lm.x * frame.shape[1], lm.y * frame.shape[0]]
    
    def analyze_frame(self, frame):
        # Convert to RGB for MediaPipe
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(image)
        
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            
            # Exercise-specific analysis
            if self.exercise_mode.get() == "bicep_curl":
                elbow_angle, form_status = self.analyze_bicep_curl(landmarks, frame)
                self.update_realtime_feedback_bicep(elbow_angle, form_status)
                
            elif self.exercise_mode.get() == "pushup":
                elbow_angle, body_angle, form_status = self.analyze_pushup(landmarks, frame)
                self.update_realtime_feedback_pushup(elbow_angle, body_angle, form_status)
                
            elif self.exercise_mode.get() == "squat":
                knee_angle, hip_angle, form_status = self.analyze_squat(landmarks, frame)
                self.update_realtime_feedback_squat(knee_angle, hip_angle, form_status)
                
            else:  # general_pose
                self.analyze_general_pose(landmarks, frame)
            
            # Posture analysis (common for all exercises)
            self.analyze_posture(landmarks, frame)
            
            # Draw pose landmarks
            self.mp_drawing.draw_landmarks(
                frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
                self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2)
            )
        
        return frame
    
    def analyze_general_pose(self, landmarks, frame):
        # General pose analysis (similar to original code)
        l_shoulder = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_SHOULDER.value, frame)
        l_elbow = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_ELBOW.value, frame)
        l_wrist = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_WRIST.value, frame)
        
        elbow_angle = self.calculate_angle(l_shoulder, l_elbow, l_wrist)
        
        self.primary_angle_var.set(f"Elbow Angle: {int(elbow_angle)}°")
        self.secondary_angle_var.set(f"General Analysis")
        self.form_status_var.set("Pose Detected")
        self.form_status_label.config(fg='blue')
    
    def analyze_posture(self, landmarks, frame):
        # Posture analysis
        l_shoulder = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_SHOULDER.value, frame)
        r_shoulder = self.get_coords(landmarks, self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value, frame)
        l_hip = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_HIP.value, frame)
        r_hip = self.get_coords(landmarks, self.mp_pose.PoseLandmark.RIGHT_HIP.value, frame)
        
        shoulder_symmetry = abs(l_shoulder[1] - r_shoulder[1])
        hip_symmetry = abs(l_hip[1] - r_hip[1])
        
        posture_status = "Good Posture" if shoulder_symmetry <= 30 and hip_symmetry <= 30 else "Check Posture"
        
        self.posture_status_var.set(f"Status: {posture_status}")
        self.posture_status_label.config(fg='green' if posture_status == "Good Posture" else 'orange')
    
    def update_realtime_feedback_bicep(self, elbow_angle, form_status):
        feedback = f"[{time.strftime('%H:%M:%S')}] Bicep Curl\n"
        feedback += f"• Elbow angle: {int(elbow_angle)}°\n"
        feedback += f"• Form: {form_status}\n"
        feedback += f"• Reps completed: {self.rep_count}\n"
        
        if form_status == "Good Form":
            feedback += "• Keep it up! Excellent form!\n"
        else:
            if elbow_angle < 30:
                feedback += "• Angle too small, extend more\n"
            elif elbow_angle > 170:
                feedback += "• Lower the weight, bring curl closer\n"
        
        feedback += "\n"
        
        # Update feedback text (keep last 20 lines)
        self.feedback_text.insert(tk.END, feedback)
        lines = self.feedback_text.get("1.0", tk.END).split('\n')
        if len(lines) > 50:
            self.feedback_text.delete("1.0", f"{len(lines)-50}.0")
        self.feedback_text.see(tk.END)
    
    def update_realtime_feedback_pushup(self, elbow_angle, body_angle, form_status):
        feedback = f"[{time.strftime('%H:%M:%S')}] Push-up\n"
        feedback += f"• Elbow angle: {int(elbow_angle)}\n"
        feedback += f"• Body alignment: {int(body_angle)}\n"
        feedback += f"• Form: {form_status}\n"
        feedback += f"• Reps completed: {self.rep_count}\n"
        
        if form_status == "Good Form":
            feedback += "• Excellent form! Keep going!\n"
        else:
            if elbow_angle < 70:
                feedback += "• Go deeper for a full push-up\n"
            if body_angle < 160:
                feedback += "• Keep your body straight\n"
        
        feedback += "\n"
        
        # Update feedback text
        self.feedback_text.insert(tk.END, feedback)
        lines = self.feedback_text.get("1.0", tk.END).split('\n')
        if len(lines) > 50:
            self.feedback_text.delete("1.0", f"{len(lines)-50}.0")
        self.feedback_text.see(tk.END)
    
    def update_realtime_feedback_squat(self, knee_angle, hip_angle, form_status):
        feedback = f"[{time.strftime('%H:%M:%S')}] Squat\n"
        feedback += f"• Knee angle: {int(knee_angle)}\n"
        feedback += f"• Hip angle: {int(hip_angle)}\n"
        feedback += f"• Form: {form_status}\n"
        feedback += f"• Reps completed: {self.rep_count}\n"
        
        if form_status == "Good Form":
            feedback += "• Perfect squat form!\n"
        else:
            if knee_angle < 70:
                feedback += "• Great depth! Keep it up\n"
            elif knee_angle > 160:
                feedback += "• Go deeper for better results\n"
            if hip_angle < 160:
                feedback += "• Keep chest up and back straight\n"
        
        feedback += "\n"
        
        # Update feedback text
        self.feedback_text.insert(tk.END, feedback)
        lines = self.feedback_text.get("1.0", tk.END).split('\n')
        if len(lines) > 50:
            self.feedback_text.delete("1.0", f"{len(lines)-50}.0")
        self.feedback_text.see(tk.END)
    
    def analyze_pose(self):
        if self.original_frame is None:
            messagebox.showwarning("Warning", "Please load an image first")
            return
        
        try:
            self.status_var.set("Analyzing pose...")
            self.root.update()
            
            # Analyze the loaded image
            analyzed_frame = self.analyze_frame(self.original_frame.copy())
            self.display_image(analyzed_frame)
            
            self.status_var.set("Analysis complete")
            
        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed: {str(e)}")
            self.status_var.set("Analysis failed")
    
    def __del__(self):
        # Cleanup when the object is destroyed
        if self.cap:
            self.cap.release()
        if self.video_cap:
            self.video_cap.release()
        cv2.destroyAllWindows()

def main():
    root = tk.Tk()
    app = PoseAnalysisGUI(root)
    
    # Handle window closing
    def on_closing():
        app.stop_video()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()