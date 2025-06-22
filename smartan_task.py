# Enhanced Pose Analysis with Real-time Video Support
import cv2
import mediapipe as mp
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import threading
import time

class PoseAnalysisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Pose Analysis Tool")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize MediaPipe
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.7, min_tracking_confidence=0.7)
        
        # Video capture
        self.cap = None
        self.is_recording = False
        self.video_thread = None
        
        # Variables
        self.current_image = None
        self.analyzed_image = None
        self.original_frame = None
        
        # Exercise tracking
        self.exercise_mode = tk.StringVar(value="bicep_curl")
        self.rep_count = 0
        self.exercise_state = "down"  # For bicep curls: "up", "down"
        self.pushup_state = "up"      # For pushups: "up", "down"
        
        # Exercise history
        self.bicep_angles = []
        self.pushup_angles = []
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main title
        title_frame = tk.Frame(self.root, bg='#f0f0f0')
        title_frame.pack(pady=10)
        
        title_label = tk.Label(title_frame, text="🏋️ Enhanced Pose Analysis Tool", 
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
                                    values=["bicep_curl", "pushup", "general_pose"],
                                    state="readonly", width=15)
        exercise_combo.pack(pady=5)
        exercise_combo.bind("<<ComboboxSelected>>", self.on_exercise_change)
        
        # File selection
        file_frame = tk.Frame(control_frame, bg='#f0f0f0')
        file_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(file_frame, text="Image File:", font=('Arial', 12, 'bold'), 
                bg='#f0f0f0').pack()
        
        self.file_path_var = tk.StringVar()
        self.file_entry = tk.Entry(file_frame, textvariable=self.file_path_var, 
                                  width=30, font=('Arial', 10))
        self.file_entry.pack(pady=5)
        
        # Buttons
        button_frame = tk.Frame(control_frame, bg='#f0f0f0')
        button_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(button_frame, text="Controls:", font=('Arial', 12, 'bold'), 
                bg='#f0f0f0').pack()
        
        button_row1 = tk.Frame(button_frame, bg='#f0f0f0')
        button_row1.pack(pady=2)
        
        browse_btn = tk.Button(button_row1, text="Browse Image", 
                              command=self.browse_file,
                              bg='#3498db', fg='white', 
                              font=('Arial', 9, 'bold'),
                              padx=10)
        browse_btn.pack(side=tk.LEFT, padx=2)
        
        analyze_btn = tk.Button(button_row1, text="Analyze Image", 
                               command=self.analyze_pose,
                               bg='#27ae60', fg='white', 
                               font=('Arial', 9, 'bold'),
                               padx=10)
        analyze_btn.pack(side=tk.LEFT, padx=2)
        
        button_row2 = tk.Frame(button_frame, bg='#f0f0f0')
        button_row2.pack(pady=2)
        
        self.start_video_btn = tk.Button(button_row2, text="Start Video", 
                                        command=self.start_video,
                                        bg='#e74c3c', fg='white', 
                                        font=('Arial', 9, 'bold'),
                                        padx=10)
        self.start_video_btn.pack(side=tk.LEFT, padx=2)
        
        self.stop_video_btn = tk.Button(button_row2, text="Stop Video", 
                                       command=self.stop_video,
                                       bg='#95a5a6', fg='white', 
                                       font=('Arial', 9, 'bold'),
                                       padx=10, state=tk.DISABLED)
        self.stop_video_btn.pack(side=tk.LEFT, padx=2)
        
        reset_btn = tk.Button(button_row2, text="Reset Count", 
                             command=self.reset_count,
                             bg='#f39c12', fg='white', 
                             font=('Arial', 9, 'bold'),
                             padx=10)
        reset_btn.pack(side=tk.LEFT, padx=2)
        
        # Main content area
        content_frame = tk.Frame(self.root, bg='#f0f0f0')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Image display area
        image_frame = tk.LabelFrame(content_frame, text="Video/Image Analysis", 
                                   font=('Arial', 12, 'bold'),
                                   bg='#f0f0f0', fg='#2c3e50')
        image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Canvas for image display
        self.canvas = tk.Canvas(image_frame, bg='white', width=700, height=500)
        self.canvas.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Analysis results panel
        results_frame = tk.LabelFrame(content_frame, text="Analysis Results", 
                                     font=('Arial', 12, 'bold'),
                                     bg='#f0f0f0', fg='#2c3e50',
                                     width=400)
        results_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        results_frame.pack_propagate(False)
        
        
        self.exercise_state_var = tk.StringVar(value="State: Ready")
        
        
        # Exercise-specific Analysis
        self.exercise_frame = tk.LabelFrame(results_frame, text="💪 Exercise Analysis", 
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
        else:
            self.exercise_frame.config(text="General Pose Analysis")
        
        self.status_var.set(f"Exercise mode changed to: {mode.replace('_', ' ').title()}")
    
    def reset_count(self):
        self.bicep_angles = []
        self.pushup_angles = []
    
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
                
                self.status_var.set("Real-time video analysis started")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start video: {str(e)}")
    
    def stop_video(self):
        self.is_recording = False
        if self.cap:
            self.cap.release()
        
        self.start_video_btn.config(state=tk.NORMAL)
        self.stop_video_btn.config(state=tk.DISABLED)
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
    
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
            ]
        )
        if file_path:
            self.file_path_var.set(file_path)
            self.load_image(file_path)
    
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
                canvas_width, canvas_height = 700, 500
            
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
        
        # Rep counting logic
        if elbow_angle > 160 and self.exercise_state == "up":
            self.exercise_state = "down"
        elif elbow_angle < 50 and self.exercise_state == "down":
            self.exercise_state = "up"
            
        
        # Form analysis
        form_status = "Good Form" if 30 <= elbow_angle <= 170 else "Check Form"
        
        # Update UI
        self.primary_angle_var.set(f"Elbow Angle: {int(elbow_angle)}")
        self.secondary_angle_var.set(f"Range: 30-170")
        self.form_status_var.set(f"Form: {form_status}")
        self.form_status_label.config(fg='green' if form_status == "Good Form" else 'red')
        self.exercise_state_var.set(f"State: {self.exercise_state.title()}")

        cv2.putText(frame, f"Elbow: {int(elbow_angle)} - {form_status}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        return elbow_angle, form_status
    
    def analyze_pushup(self, landmarks, frame):
        # Get keypoints for pushup analysis
        l_shoulder = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_SHOULDER.value, frame)
        l_elbow = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_ELBOW.value, frame)
        l_wrist = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_WRIST.value, frame)
        l_hip = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_HIP.value, frame)
        l_knee = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_KNEE.value, frame)
        l_ankle = self.get_coords(landmarks, self.mp_pose.PoseLandmark.LEFT_ANKLE.value, frame)
        
        # Calculate angles
        elbow_angle = self.calculate_angle(l_shoulder, l_elbow, l_wrist)
        body_angle = self.calculate_angle(l_shoulder, l_hip, l_knee)
        
        self.pushup_angles.append(elbow_angle)
        
    
        # Form analysis
        elbow_form = "Good" if 70 <= elbow_angle <= 180 else "Check Elbow"
        body_form = "Good" if 160 <= body_angle <= 180 else "Straighten Body"
        overall_form = "Good Form" if elbow_form == "Good" and body_form == "Good" else "Check Form"
        
        # Update UI
        self.primary_angle_var.set(f"Elbow Angle: {int(elbow_angle)}°")
        self.secondary_angle_var.set(f"Body Angle: {int(body_angle)}°")
        self.form_status_var.set(f"Form: {overall_form}")
        self.form_status_label.config(fg='green' if overall_form == "Good Form" else 'red')
        self.exercise_state_var.set(f"State: {self.pushup_state.title()}")

        cv2.putText(frame, f"Elbow: {int(elbow_angle)} Body: {int(body_angle)}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        return elbow_angle, body_angle, overall_form
    
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
        
        self.primary_angle_var.set(f"Elbow Angle: {int(elbow_angle)}")
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
        feedback += f"• Elbow angle: {int(elbow_angle)}\n"
        feedback += f"• Form: {form_status}\n"
        feedback += f"• Reps completed: {self.rep_count}\n"
        
        if form_status == "Good Form":
            feedback += "• Keep it up! \n"
        else:
            if elbow_angle < 30:
                feedback += "It is very small angle, extend more\n"
            elif elbow_angle > 170:
                feedback += "• Lower the weight,and bring the curl closer to the body\n"
        
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
        
        if form_status == "Good Form":
            feedback += "• Excellent form!\n"
        else:
            if elbow_angle < 70:
                feedback += "• Go deeper for a full push-up\n"
            if body_angle < 160:
                feedback += "• Keep your body straight \n"
        
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