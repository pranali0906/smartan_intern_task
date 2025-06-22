# Form assessment for Bicep curl
form_status = "Good Form" if 30 <= elbow_angle <= 170 else "Check Form"
    
#Form assessment for pushup
elbow_form = "Good" if 70 <= elbow_angle <= 180 else "Check Elbow"
body_form = "Good" if 160 <= body_angle <= 180 else "Straighten Body"
overall_form = "Good Form" if both conditions met else "Check Form"

#Form assessment for squat
knee_form = "Good" if 70 <= knee_angle <= 180 else "Check Depth"
hip_form = "Good" if 160 <= hip_angle <= 180 else "Check Posture"

