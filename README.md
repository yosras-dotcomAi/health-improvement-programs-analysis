# -health-improving-programs
import csv

# Questionnaire questions
questions = [
    "Department: ",
    "Position/Role: ",
    "Years of experience in healthcare: ",
    "Are you aware of any current staff health or wellness programs in the hospital? (Yes/No): ",
    "If yes, which programs have you participated in? (e.g., Fitness, Nutrition, Stress Management): ",
    "How often do you participate in these programs? (Regularly/Occasionally/Rarely/Never): ",
    "How effective do you find the current health programs? (Very effective/Somewhat effective/Neutral/Not effective): ",
    "What benefits have you noticed from participating? (e.g., Better health, Less stress, Work-life balance): ",
    "What types of health-improving programs would you like the hospital to provide in the future?: ",
    "What barriers prevent you from participating? (Time, Awareness, Schedule, Options, Other): "
]

# CSV file setup
filename = "staff_health_survey_responses.csv"

# Create CSV file with headers if it doesn’t exist
with open(filename, "a", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    if file.tell() == 0:  # Only add header once
        writer.writerow([f"Q{i+1}" for i in range(len(questions))])

def run_survey():
    print("\n🏥 Hospital Staff Health-Improving Programs – Questionnaire 🏥\n")
    responses = []
    for q in questions:
        answer = input(q)
        responses.append(answer.strip())
    
    # Save responses
    with open(filename, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(responses)
    
    print("\n✅ Thank you! Your response has been recorded.\n")

# Run the survey
if __name__ == "__main__":
    run_survey()
 python hospital_staff_health_survey.py

