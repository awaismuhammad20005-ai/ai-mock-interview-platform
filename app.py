"""
AI Mock Interview Platform
Adaptive interview questions with AI-powered response analysis
"""

import os
import json
import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'ai_interview_secret_key_2024'
CORS(app)

# Initialize OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Interview Questions Database by Category
INTERVIEW_QUESTIONS = {
    "Technical": {
        "Software Development": [
            "Explain the difference between object-oriented programming and functional programming.",
            "How would you optimize a slow database query?",
            "Describe the MVC architecture and its benefits.",
            "What is your experience with version control systems like Git?",
            "Explain RESTful APIs and their principles.",
            "How do you handle errors and exceptions in your code?",
            "What testing strategies do you use in your projects?"
        ],
        "Data Science": [
            "Explain the difference between supervised and unsupervised learning.",
            "How do you handle missing data in a dataset?",
            "What evaluation metrics would you use for a classification problem?",
            "Explain the bias-variance tradeoff.",
            "How do you prevent overfitting in machine learning models?",
            "What feature selection techniques do you know?",
            "Explain how a decision tree works."
        ],
        "Cloud Computing": [
            "Explain the difference between IaaS, PaaS, and SaaS.",
            "What are the benefits of using containers like Docker?",
            "How would you design a highly available system on AWS?",
            "Explain serverless architecture.",
            "What is infrastructure as code? Give examples.",
            "How do you handle security in the cloud?",
            "Explain load balancing and auto-scaling."
        ]
    },
    "Behavioral": [
        "Tell me about a time you faced a challenge at work and how you overcame it.",
        "Describe a situation where you had to work with a difficult team member.",
        "Give an example of a project you led from start to finish.",
        "Tell me about a time you made a mistake and what you learned from it.",
        "How do you prioritize tasks when you have multiple deadlines?",
        "Describe a situation where you went above and beyond your job duties.",
        "Tell me about a time you received constructive criticism and how you handled it."
    ],
    "Situational": [
        "If you were given a project with a tight deadline, how would you approach it?",
        "How would you handle a disagreement with your manager about a technical solution?",
        "If you discovered a security vulnerability in production, what would you do?",
        "How would you explain a complex technical concept to a non-technical stakeholder?",
        "If you were asked to learn a new technology quickly, how would you proceed?"
    ],
    "HR": [
        "Why do you want to work for this company?",
        "Where do you see yourself in 5 years?",
        "What are your greatest strengths and weaknesses?",
        "Why should we hire you?",
        "Tell me about yourself.",
        "What is your expected salary range?",
        "Why are you leaving your current position?"
    ]
}

# Difficulty levels
DIFFICULTY_LEVELS = {
    "Beginner": 1,
    "Intermediate": 2,
    "Advanced": 3
}

# Store interview sessions
interview_sessions = {}

def generate_question(category, subcategory=None, difficulty="Intermediate", previous_answers=None):
    """Generate adaptive question based on previous answers"""
    
    if subcategory and category == "Technical":
        questions = INTERVIEW_QUESTIONS["Technical"].get(subcategory, INTERVIEW_QUESTIONS["Technical"]["Software Development"])
    elif category in INTERVIEW_QUESTIONS:
        questions = INTERVIEW_QUESTIONS[category]
    else:
        questions = INTERVIEW_QUESTIONS["Behavioral"]
    
    # If no previous answers, return first question
    if not previous_answers:
        return questions[0]
    
    # Adaptive questioning based on answer quality
    answer_count = len(previous_answers)
    if answer_count < len(questions):
        # Adjust difficulty based on previous performance
        if previous_answers and previous_answers[-1].get('quality', 0) < 4:
            # Previous answer was poor, ask easier question
            difficulty = "Beginner"
        elif previous_answers and previous_answers[-1].get('quality', 0) > 8:
            # Previous answer was excellent, ask harder question
            difficulty = "Advanced"
        
        return questions[answer_count % len(questions)]
    
    return questions[len(questions) - 1]

def analyze_answer(question, answer, category="General"):
    """Analyze answer using AI and provide feedback"""
    
    if not client:
        return get_fallback_analysis(question, answer)
    
    prompt = f"""
    You are an expert interviewer. Analyze the candidate's answer and provide feedback.
    
    Question: {question}
    Candidate's Answer: {answer}
    Interview Type: {category}
    
    Return ONLY valid JSON with this structure:
    {{
        "score": 75,
        "strengths": ["Strength 1", "Strength 2"],
        "weaknesses": ["Weakness 1", "Weakness 2"],
        "feedback": "Detailed constructive feedback paragraph",
        "improvement_suggestions": ["Suggestion 1", "Suggestion 2"],
        "follow_up_question": "Suggested follow-up question if needed"
    }}
    
    Scoring guide:
    - 90-100: Excellent, comprehensive answer
    - 75-89: Good answer, minor improvements needed
    - 60-74: Satisfactory, but significant gaps
    - Below 60: Needs substantial improvement
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=600
        )
        
        result = response.choices[0].message.content
        result = re.sub(r'```json\n?', '', result)
        result = re.sub(r'```\n?', '', result)
        analysis = json.loads(result)
        return analysis
        
    except Exception as e:
        print(f"OpenAI error: {e}")
        return get_fallback_analysis(question, answer)

def get_fallback_analysis(question, answer):
    """Fallback analysis without AI"""
    answer_length = len(answer.split())
    
    if answer_length > 100:
        score = 75
        feedback = "Good length and detail. Consider adding more specific examples."
    elif answer_length > 50:
        score = 60
        feedback = "Adequate answer but could be more comprehensive."
    else:
        score = 40
        feedback = "Answer is too brief. Provide more details and examples."
    
    return {
        "score": score,
        "strengths": [
            "Attempted to answer the question",
            "Showed basic understanding" if score > 50 else "Needs more preparation"
        ],
        "weaknesses": [
            "Could provide more specific examples",
            "Answer lacks structure" if score < 70 else "Good structure but add more depth"
        ],
        "feedback": feedback,
        "improvement_suggestions": [
            "Use the STAR method (Situation, Task, Action, Result)",
            "Provide quantifiable achievements",
            "Practice with more questions"
        ],
        "follow_up_question": "Can you provide a specific example from your experience?"
    }

@app.route('/')
def index():
    """Main page"""
    return render_template('interview.html')

@app.route('/start_interview', methods=['POST'])
def start_interview():
    """Start a new interview session"""
    data = request.json
    session_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + str(hash(str(data)))[:6]
    
    interview_sessions[session_id] = {
        "category": data.get('category', 'Behavioral'),
        "subcategory": data.get('subcategory', None),
        "difficulty": data.get('difficulty', 'Intermediate'),
        "questions_asked": [],
        "answers": [],
        "scores": [],
        "feedback": [],
        "current_index": 0,
        "start_time": datetime.datetime.now().isoformat(),
        "completed": False
    }
    
    # Get first question
    question = generate_question(
        data.get('category', 'Behavioral'),
        data.get('subcategory', None),
        data.get('difficulty', 'Intermediate')
    )
    
    interview_sessions[session_id]["questions_asked"].append(question)
    
    return jsonify({
        "session_id": session_id,
        "question": question,
        "question_number": 1,
        "total_questions": 7,
        "category": data.get('category', 'Behavioral')
    })

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    """Submit answer and get feedback"""
    data = request.json
    session_id = data.get('session_id')
    answer = data.get('answer', '')
    question_number = data.get('question_number', 1)
    
    if session_id not in interview_sessions:
        return jsonify({"error": "Session not found"}), 404
    
    session = interview_sessions[session_id]
    
    # Get current question
    current_question = session["questions_asked"][-1] if session["questions_asked"] else ""
    
    # Analyze answer
    analysis = analyze_answer(current_question, answer, session["category"])
    
    # Store answer and analysis
    session["answers"].append({
        "question": current_question,
        "answer": answer,
        "score": analysis.get("score", 0),
        "timestamp": datetime.datetime.now().isoformat()
    })
    session["scores"].append(analysis.get("score", 0))
    session["feedback"].append(analysis)
    
    # Check if interview is complete (7 questions)
    if question_number >= 7:
        session["completed"] = True
        # Calculate overall score
        avg_score = sum(session["scores"]) / len(session["scores"]) if session["scores"] else 0
        
        # Generate overall feedback
        overall_feedback = generate_overall_feedback(avg_score, session["scores"])
        
        return jsonify({
            "completed": True,
            "feedback": analysis,
            "overall_score": avg_score,
            "overall_feedback": overall_feedback,
            "next_question": None,
            "question_number": question_number
        })
    
    # Get next question
    next_question = generate_question(
        session["category"],
        session.get("subcategory"),
        session["difficulty"],
        session["answers"]
    )
    session["questions_asked"].append(next_question)
    
    return jsonify({
        "completed": False,
        "feedback": analysis,
        "next_question": next_question,
        "question_number": question_number + 1,
        "total_questions": 7,
        "progress": (question_number / 7) * 100
    })

def generate_overall_feedback(avg_score, scores):
    """Generate overall interview feedback"""
    if avg_score >= 85:
        return {
            "level": "Excellent",
            "message": "🎉 Outstanding performance! You demonstrated strong communication skills and deep knowledge.",
            "recommendations": [
                "Keep practicing with advanced questions",
                "Start applying for senior positions",
                "Work on leadership examples"
            ]
        }
    elif avg_score >= 70:
        return {
            "level": "Good",
            "message": "👍 Good job! You have solid fundamentals. Focus on the areas mentioned to become exceptional.",
            "recommendations": [
                "Practice with more specific examples",
                "Work on structuring answers using STAR method",
                "Prepare for behavioral questions"
            ]
        }
    elif avg_score >= 50:
        return {
            "level": "Satisfactory",
            "message": "📚 You're on the right track but need more preparation.",
            "recommendations": [
                "Review core concepts in your field",
                "Practice answering out loud daily",
                "Record yourself and listen back",
                "Research common interview questions"
            ]
        }
    else:
        return {
            "level": "Needs Improvement",
            "message": "💪 You need significant preparation before interviews.",
            "recommendations": [
                "Start with basic concepts",
                "Take online courses in your field",
                "Practice with a friend or mentor",
                "Review sample interview answers online",
                "Use the STAR method framework"
            ]
        }

@app.route('/get_session', methods=['GET'])
def get_session():
    """Get session details"""
    session_id = request.args.get('session_id')
    if session_id in interview_sessions:
        session = interview_sessions[session_id]
        return jsonify({
            "completed": session["completed"],
            "scores": session["scores"],
            "average_score": sum(session["scores"]) / len(session["scores"]) if session["scores"] else 0,
            "total_questions": len(session["answers"])
        })
    return jsonify({"error": "Session not found"}), 404

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎯 AI Mock Interview Platform")
    print("="*60)
    print("🌐 URL: http://localhost:5000")
    print("💡 Features: Adaptive questions, AI analysis, feedback")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)