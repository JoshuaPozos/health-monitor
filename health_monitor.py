import datetime
import json
from pathlib import Path
import os

def get_version():
    version_file = Path("VERSION.txt")
    if version_file.exists():
        return version_file.read_text().strip()
    return "Unknown"

def get_yes_no_input(prompt):
    while True:
        response = input(prompt).lower().strip()
        if response in ['y', 'yes', 'yeah', '']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")

def get_valid_input(prompt, example, validation_func):
    while True:
        response = input(prompt)
        if response == '' and 'weight' not in prompt.lower():
            print(f"Invalid input. Please enter a valid value. Example: {example}")
        else:
            try:
                return validation_func(response)
            except ValueError:
                print(f"Invalid input. Please enter a valid value. Example: {example}")

class HealthIssue:
    def __init__(self, name, value=0):
        self.name = name
        self.value = value  # 0 means present, 10 means resolved

    def to_dict(self):
        return {"name": self.name, "value": self.value}

    @classmethod
    def from_dict(cls, data):
        return cls(data['name'], data['value'])

class HealthMonitor:
    def __init__(self, name, height, weight, birth_date, avg_daily_steps, is_smoker, avg_work_hours, health_issues):
        self.name = name
        self.height = height
        self.weight = weight
        self.birth_date = birth_date
        self.avg_daily_steps = avg_daily_steps
        self.is_smoker = is_smoker
        self.avg_work_hours = avg_work_hours
        self.health_issues = health_issues
        self.data_file = Path(f"users/health_data_{name.lower().replace(' ', '_')}.json")
        self.health_records = []
        self.load_data()

    def load_data(self):
        if self.data_file.exists():
            with self.data_file.open('r') as f:
                data = json.load(f)
                self.health_records = data.get('health_records', [])
                self.name = data.get('name', self.name)
                self.height = data.get('height', self.height)
                self.weight = data.get('weight', self.weight)
                self.birth_date = data.get('birth_date', self.birth_date)
                self.avg_daily_steps = data.get('avg_daily_steps', self.avg_daily_steps)
                self.is_smoker = data.get('is_smoker', self.is_smoker)
                self.avg_work_hours = data.get('avg_work_hours', self.avg_work_hours)
                self.health_issues = [HealthIssue.from_dict(hi) for hi in data.get('health_issues', [])]
        else:
            self.health_records = []

    def save_data(self):
        data = {
            'name': self.name,
            'height': self.height,
            'weight': self.weight,
            'birth_date': self.birth_date,
            'avg_daily_steps': self.avg_daily_steps,
            'is_smoker': self.is_smoker,
            'avg_work_hours': self.avg_work_hours,
            'health_issues': [hi.to_dict() for hi in self.health_issues],
            'health_records': self.health_records
        }
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        with self.data_file.open('w') as f:
            json.dump(data, f, indent=4)

    def add_daily_record(self, weight, steps, screen_hours, smoking):
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        # Calculate indices
        bmi = round(weight / (self.height ** 2), 1)
        activity_score = self._calculate_activity_score(steps, screen_hours)
        health_habits_score = self._calculate_habits_score(smoking)

        # Calculate overall average
        scores = [
            activity_score,
            health_habits_score,
            self._calculate_screen_time_score(screen_hours)
        ]
        average_health = sum(scores) / len(scores)

        record = {
            "date": today,
            "weight": weight,
            "bmi": bmi,
            "steps": steps,
            "screen_hours": screen_hours,
            "smoking": smoking,
            "activity_score": activity_score,
            "health_habits_score": health_habits_score,
            "average_health": average_health
        }

        self.health_records.append(record)
        self.save_data()
        return self._generate_recommendations(record)

    def _calculate_activity_score(self, steps, screen_hours):
        # Score based on steps (maximum 5 points)
        steps_score = min(steps / 2000, 5)  # 10000 steps = 5 points

        # Score based on screen time (maximum 5 points)
        screen_score = max(5 - (screen_hours / 2.4), 0)  # 12 hours = 0 points

        return (steps_score + screen_score) / 2

    def _calculate_habits_score(self, smoking):
        score = 10
        if smoking:
            score -= 5
        return max(score, 0)

    def _calculate_screen_time_score(self, screen_hours):
        return max(10 - (screen_hours / 1.2), 0)  # 12 hours = 0 points

    def _generate_recommendations(self, record):
        recommendations = []

        if record["steps"] < 7500:
            recommendations.append("You need to increase your physical activity. Try walking more.")
        else:
            recommendations.append("Great job on your physical activity! Keep it up.")

        if record["screen_hours"] > 6:
            recommendations.append("Reduce your screen time. Take breaks every hour.")

        if record["smoking"]:
            recommendations.append("Quitting smoking would significantly improve your health.")

        if record["average_health"] < 5:
            recommendations.append("Your health index is low. Follow the above recommendations.")

        # Add BMI-based recommendation
        bmi = record["bmi"]
        if bmi:
            if bmi < 18.5:
                recommendations.append(f"Your BMI is {bmi:.1f}, which is considered underweight. You should gain {self._calculate_weight_change(bmi, 18.5):.1f} kg to reach a healthy weight.")
            elif bmi < 25:
                recommendations.append(f"Your BMI is {bmi:.1f}, which is within the healthy range.")
            elif bmi < 30:
                recommendations.append(f"Your BMI is {bmi:.1f}, which is considered overweight. You should lose {self._calculate_weight_change(bmi, 25):.1f} kg to reach a healthy weight.")
            else:
                recommendations.append(f"Your BMI is {bmi:.1f}, which is considered obese. You should lose {self._calculate_weight_change(bmi, 25):.1f} kg to reach a healthy weight.")

        return recommendations

    def _calculate_weight_change(self, current_bmi, target_bmi):
        current_weight = current_bmi * (self.height ** 2)
        target_weight = target_bmi * (self.height ** 2)
        return round(abs(current_weight - target_weight), 1)

    def get_health_summary(self):
        if not self.health_records:
            return "No records available."

        latest = self.health_records[-1]
        health_issues_summary = "\n".join([f"- {issue.name}" for issue in self.health_issues]) if self.health_issues else "None"
        
        return f"""
Health Summary for {self.name}:
Date: {latest['date']}
Weight: {latest['weight']:.1f} kg
BMI: {latest['bmi']:.1f}
Average Health Index: {latest['average_health']:.2f}/10
Activity Score: {latest['activity_score']:.2f}/10
Health Habits Score: {latest['health_habits_score']:.2f}/10

Health Issues:
{health_issues_summary}
"""

def get_or_create_user():
    users_dir = Path("users")
    users_dir.mkdir(exist_ok=True)
    users = [f.stem.replace('health_data_', '') for f in users_dir.glob('health_data_*.json')]
    
    choice = get_yes_no_input("Are you an existing user? (yes/no): ")
    
    if choice and users:
        print("Existing users:")
        for i, user in enumerate(users, 1):
            print(f"{i}. {user.replace('_', ' ').title()}")
        
        user_choice = input("Select a user by number: ")
        
        if user_choice.isdigit() and 1 <= int(user_choice) <= len(users):
            return load_user(users[int(user_choice) - 1])
        else:
            print("Invalid option. Creating a new user.")
            return create_new_user()
    else:
        return create_new_user()

def create_new_user():
    name = input("Enter your name: ")
    height = get_valid_input("Enter your height in meters (e.g., 1.80): ", "1.80", lambda x: float(x))
    weight = get_valid_input("Enter your current weight in kg: ", "75.5", lambda x: float(x))
    birth_date = get_valid_input("Enter your birth date (YYYY-MM-DD): ", "1990-01-01", lambda x: x)
    avg_daily_steps = get_valid_input("Enter your average daily steps: ", "7500", lambda x: int(x))
    is_smoker = get_yes_no_input("Are you a smoker? (yes/no): ")
    avg_work_hours = get_valid_input("Enter your average daily hours working in front of a computer: ", "8.5", lambda x: float(x))
    
    health_issues = []
    while get_yes_no_input("Do you have any health issues? (yes/no): "):
        issue_name = input("Enter the name of the health issue: ")
        health_issues.append(HealthIssue(issue_name))
        if not get_yes_no_input("Do you want to add another health issue? (yes/no): "):
            break
    
    return HealthMonitor(name, height, weight, birth_date, avg_daily_steps, is_smoker, avg_work_hours, health_issues)

def load_user(username):
    with open(f"users/health_data_{username}.json", 'r') as f:
        data = json.load(f)
    return HealthMonitor(
        data['name'],
        data['height'],
        data['weight'],
        data['birth_date'],
        data['avg_daily_steps'],
        data['is_smoker'],
        data['avg_work_hours'],
        [HealthIssue.from_dict(hi) for hi in data['health_issues']]
    )

def main():
    print(f"Health Monitor v{get_version()}")
    print("=" * 30)
    monitor = get_or_create_user()

    # Record a day
    weight_input = input("Enter your weight for today in kg (press Enter to use previous weight): ")
    if weight_input:
        weight = float(weight_input)
    else:
        weight = monitor.health_records[-1]['weight'] if monitor.health_records else monitor.weight
        print(f"Using previous weight: {weight:.1f} kg")
    
    steps = get_valid_input("Enter the number of steps taken today: ", "7500", lambda x: int(x))
    screen_hours = get_valid_input("Enter the hours spent in front of a screen: ", "6.5", lambda x: float(x))
    smoking = get_yes_no_input("Did you smoke today? (yes/no): ")

    recommendations = monitor.add_daily_record(
        weight=weight,
        steps=steps,
        screen_hours=screen_hours,
        smoking=smoking
    )

    # Show summary and recommendations
    print(monitor.get_health_summary())
    print("\nRecommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")

if __name__ == "__main__":
    main()

