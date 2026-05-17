from decimal import Decimal

def calculate_bmr(gender, weight, height, age):
    """
    Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation.
    weight in kg, height in cm, age in years.
    """
    if not all([weight, height, age]):
        return Decimal('0')
    
    weight = float(weight)
    height = float(height)
    age = int(age)

    if gender == 'male':
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        # Female or other/prefer_not_to_say (default to female for safety in estimation)
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
    
    return Decimal(str(bmr))

def estimate_met(heart_rate=None, step_cadence=None, age=None):
    """
    Estimate MET based on heart rate zones or step cadence.
    Max HR = 220 - age
    """
    # Default to Resting MET
    met = 1.0

    if heart_rate and age:
        try:
            heart_rate = float(heart_rate)
        except (ValueError, TypeError):
            heart_rate = None

    if heart_rate and age:
        max_hr = 220 - age
        hr_percentage = (heart_rate / max_hr) * 100

        if hr_percentage >= 70:
            met = 7.0
        elif hr_percentage >= 60:
            met = 5.0
        elif hr_percentage >= 50:
            met = 3.0
        else:
            met = 1.0
    elif step_cadence:
        # Fallback to steps per minute
        if step_cadence >= 130:
            met = 7.0
        elif step_cadence >= 110:
            met = 5.0
        elif step_cadence >= 80:
            met = 3.0
        else:
            met = 1.0
            
    return met

def calculate_calories_for_period(user, heart_rate, step_count, duration_minutes):
    """
    Calculate total calories burned for a specific duration.
    Total = (BMR / 1440 * minutes) + (Active Calories)
    """
    if duration_minutes <= 0:
        return Decimal('0')

    # Ensure we have required user data
    if not user.age or not user.current_weight or not user.height:
        return Decimal('0')

    bmr = calculate_bmr(user.gender, user.current_weight, user.height, user.age)
    
    # Active Calories/min = (MET * 3.5 * weight) / 200
    # For active calories, we only count MET > 1.0? 
    # Actually, MET 1.0 is essentially BMR. 
    # The formula (MET * 3.5 * weight) / 200 includes BMR if MET=1.0 is used.
    # But the requirement says: Total = (BMR / 1440 * active_minutes) + active calories burned.
    # This might imply "active calories" is the *extra* above BMR.
    # Standard formula for Total Calories: (MET * 3.5 * weight / 200) * minutes.
    # Let's stick closer to the client's provided formula.
    
    # Step cadence estimation for MET fallback (assuming step_count is for this period)
    step_cadence = (step_count / duration_minutes) if duration_minutes > 0 else 0
    met = estimate_met(heart_rate, step_cadence, user.age)
    
    # If MET is 1.0 (resting), active_calories should technically be 0 or accounted for in BMR.
    # If MET > 1.0, we calculate the active portion.
    # MET 3.5 means you are burning 3.5x BMR. So Active = (MET - 1) * BMR? 
    # No, the client gave a specific formula for active calories per minute.
    
    # Active calories per minute = (MET * 3.5 * weight) / 200
    active_cal_per_min = (met * 3.5 * float(user.current_weight)) / 200
    
    # Total = (BMR / 1440 * minutes) + (active_cal_per_min * minutes)
    # Wait, if MET=1, active_cal_per_min is basically the resting burn.
    # Let's refine: if met <= 1.0, we just use BMR.
    if met <= 1.0:
        total_calories = (bmr / 1440) * Decimal(str(duration_minutes))
    else:
        # Total = BMR portion + Active portion
        # Actually, the MET formula (MET * 3.5 * weight / 200) IS the total calories burned per minute.
        # But let's follow the client's explicit formula if it's meant to be additive.
        # "Total calories = (BMR / 1440 × active minutes) + active calories burned"
        # This is a bit ambiguous. Usually MET 1 = 1 kcal/kg/hour (approx BMR).
        # Let's assume 'active calories burned' is calculated with MET >= 3.0.
        
        bmr_portion = (bmr / 1440) * Decimal(str(duration_minutes))
        active_portion = Decimal(str(active_cal_per_min * duration_minutes))
        total_calories = bmr_portion + active_portion

    return total_calories.quantize(Decimal('0.01'))

def get_bmi_info(bmi):
    """
    Determine BMI category and message based on the BMI value.
    """
    if bmi is None:
        return None

    if bmi < 18.5:
        category, label = "Underweight", "underweight"
        message = "You are in the underweight range. It's important to consume enough nutrients and consult with a healthcare provider or nutritionist for a healthy weight gain plan."
    elif 18.5 <= bmi < 25:
        category, label = "Normal weight", "normal"
        message = "You are in a healthy range. Maintain your current weight with regular exercise and a balanced diet to stay on track."
    elif 25 <= bmi < 30:
        category, label = "Overweight", "overweight"
        message = "You are in the overweight range. Incorporating more physical activity and focusing on a balanced, calorie-controlled diet can help you reach a healthier weight."
    else:
        category, label = "Obesity", "obesity"
        message = "You are in the obesity range. We recommend consulting with a healthcare professional to develop a safe and effective plan for weight management and overall health."
    
    return {
        'category': category,
        'label': label,
        'message': message,
        'scale': [
            {'label': 'Underweight', 'range': 'Below 18.5'},
            {'label': 'Normal weight', 'range': '18.5 - 24.9'},
            {'label': 'Overweight', 'range': '25.0 - 29.9'},
            {'label': 'Obesity', 'range': '30.0 or greater'}
        ]
    }
