def analyze_pushup(self, landmarks, frame):
    # Multi-point analysis
    l_shoulder = self.get_coords(landmarks, LEFT_SHOULDER, frame)
    l_elbow = self.get_coords(landmarks, LEFT_ELBOW, frame)
    l_wrist = self.get_coords(landmarks, LEFT_WRIST, frame)
    l_hip = self.get_coords(landmarks, LEFT_HIP, frame)
    l_knee = self.get_coords(landmarks, LEFT_KNEE, frame)
    
    # Dual angle assessment
    elbow_angle = self.calculate_angle(l_shoulder, l_elbow, l_wrist)
    body_angle = self.calculate_angle(l_shoulder, l_hip, l_knee)

def analyze_bicep_curl(self, landmarks, frame):
    # Extract key points
    l_shoulder = self.get_coords(landmarks, LEFT_SHOULDER, frame)
    l_elbow = self.get_coords(landmarks, LEFT_ELBOW, frame)
    l_wrist = self.get_coords(landmarks, LEFT_WRIST, frame)
    
    # Calculate elbow angle
    elbow_angle = self.calculate_angle(l_shoulder, l_elbow, l_wrist)

def analyze_squat(self, landmarks, frame):
    # Lower body focus
    l_hip = self.get_coords(landmarks, LEFT_HIP, frame)
    l_knee = self.get_coords(landmarks, LEFT_KNEE, frame)
    l_ankle = self.get_coords(landmarks, LEFT_ANKLE, frame)
    l_shoulder = self.get_coords(landmarks, LEFT_SHOULDER, frame)
    
    # Dual angle measurement
    knee_angle = self.calculate_angle(l_hip, l_knee, l_ankle)
    hip_angle = self.calculate_angle(l_shoulder, l_hip, l_knee)

def analyze_posture(self, landmarks, frame):
    # Bilateral comparison
    l_shoulder = self.get_coords(landmarks, LEFT_SHOULDER, frame)
    r_shoulder = self.get_coords(landmarks, RIGHT_SHOULDER, frame)
    l_hip = self.get_coords(landmarks, LEFT_HIP, frame)
    r_hip = self.get_coords(landmarks, RIGHT_HIP, frame)
    
    # Symmetry calculation
    shoulder_symmetry = abs(l_shoulder[1] - r_shoulder[1])
    hip_symmetry = abs(l_hip[1] - r_hip[1])



