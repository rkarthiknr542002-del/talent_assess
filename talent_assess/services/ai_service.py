import google.genai as genai
import json
import random
from django.conf import settings

# Initialize the client directly (no configure method)
client = genai.Client(api_key=settings.GEMINI_API_KEY)

class QuestionGenerator:
    """Generate questions using Google Gemini API"""
    
    @staticmethod
    def generate_aptitude_questions(level, count=10):
        """Generate aptitude questions for given experience level"""
        
        level_descriptions = {
            'intern': 'basic/fresher level',
            'junior': 'junior level with 1-2 years experience',
            'mid': 'mid-level with 3-5 years experience',
            'senior': 'senior level with 5+ years experience'
        }
        
        prompt = f"""
        Generate {count} aptitude questions for {level_descriptions.get(level, level)} candidates.
        
        Each question should be in JSON format with:
        - question_text: The question
        - options: Array of 4 options (A, B, C, D)
        - correct_answer: Index of correct option (0-3)
        - explanation: Brief explanation of the answer
        
        Return ONLY a JSON array of questions, no other text.
        """
        
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash',  
                contents=prompt
            )
            
            text = response.text.strip()
            
            if '[' in text and ']' in text:
                start = text.find('[')
                end = text.rfind(']') + 1
                json_str = text[start:end]
                questions = json.loads(json_str)
            else:
                questions = json.loads(text)
            
            return questions
        except Exception as e:
            print(f"Error generating aptitude questions: {e}")
            return QuestionGenerator.get_fallback_aptitude_questions(level, count)
    
    @staticmethod
    def generate_technical_questions(level, technology, count=10):
        """Generate technical questions for given level and technology"""
        
        level_descriptions = {
            'intern': 'basic/fresher level',
            'junior': 'junior level with 1-2 years experience',
            'mid': 'mid-level with 3-5 years experience',
            'senior': 'senior level with 5+ years experience'
        }
        
        prompt = f"""
        Generate {count} technical questions about {technology} for {level_descriptions.get(level, level)} candidates.
        
        Each question should be in JSON format with:
        - question_text: The question
        - options: Array of 4 options (A, B, C, D)
        - correct_answer: Index of correct option (0-3)
        - explanation: Brief explanation of the answer
        - technology: "{technology}"
        
        Return ONLY a JSON array of questions, no other text.
        """
        
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash',  
                contents=prompt
            )
            
            text = response.text.strip()
            
            if '[' in text and ']' in text:
                start = text.find('[')
                end = text.rfind(']') + 1
                json_str = text[start:end]
                questions = json.loads(json_str)
            else:
                questions = json.loads(text)
            
            return questions
        except Exception as e:
            print(f"Error generating technical questions: {e}")
            return QuestionGenerator.get_fallback_technical_questions(level, technology, count)
    
    @staticmethod
    def get_fallback_aptitude_questions(level, count=10):
        """Fallback aptitude questions if API fails"""
        questions = []
        
        base_questions = [
            {
                "question_text": "If a train travels 300 km in 5 hours, what is its speed?",
                "options": ["50 km/h", "60 km/h", "70 km/h", "80 km/h"],
                "correct_answer": 1,
                "explanation": "Speed = Distance/Time = 300/5 = 60 km/h"
            },
            {
                "question_text": "What is 15% of 200?",
                "options": ["20", "25", "30", "35"],
                "correct_answer": 2,
                "explanation": "15% of 200 = (15/100) × 200 = 30"
            },
            {
                "question_text": "A man buys a book for Rs. 100 and sells it for Rs. 120. What is his profit percentage?",
                "options": ["10%", "15%", "20%", "25%"],
                "correct_answer": 2,
                "explanation": "Profit = 20, CP = 100, Profit% = (20/100)*100 = 20%"
            },
            {
                "question_text": "What is the average of 10, 20, 30, 40, 50?",
                "options": ["25", "30", "35", "40"],
                "correct_answer": 1,
                "explanation": "Average = (10+20+30+40+50)/5 = 150/5 = 30"
            },
            {
                "question_text": "If 5 workers can complete a task in 10 days, how many days will 10 workers take?",
                "options": ["5 days", "10 days", "15 days", "20 days"],
                "correct_answer": 0,
                "explanation": "More workers, less days: 5×10 = 10×x, x = 5 days"
            }
        ]
        
        # Repeat questions if needed
        while len(questions) < count:
            for q in base_questions:
                if len(questions) >= count:
                    break
                questions.append(q.copy())
        
        return questions[:count]
    
    @staticmethod
    def get_fallback_technical_questions(level, technology, count=10):
        """Fallback technical questions if API fails"""
        questions = []
        
        tech_questions = {
            'python': [
                {
                    "question_text": "What is a list comprehension in Python?",
                    "options": ["A way to create lists concisely", "A type of loop", "A built-in function", "An error handling method"],
                    "correct_answer": 0,
                    "explanation": "List comprehension provides a concise way to create lists in Python",
                    "technology": "python"
                },
                {
                    "question_text": "What is PEP 8?",
                    "options": ["Python compiler", "Python style guide", "Python package", "Python IDE"],
                    "correct_answer": 1,
                    "explanation": "PEP 8 is Python's official style guide",
                    "technology": "python"
                },
                {
                    "question_text": "What is a decorator in Python?",
                    "options": ["A design pattern", "A function that modifies other functions", "A class", "A module"],
                    "correct_answer": 1,
                    "explanation": "Decorators allow modifying function behavior",
                    "technology": "python"
                }
            ],
            'javascript': [
                {
                    "question_text": "What is closure in JavaScript?",
                    "options": ["A loop", "Function with access to outer scope", "An error", "A data type"],
                    "correct_answer": 1,
                    "explanation": "Closure is a function that has access to its outer function scope",
                    "technology": "javascript"
                }
            ],
            'django': [
                {
                    "question_text": "What is Django's ORM used for?",
                    "options": ["Database operations", "Template rendering", "URL routing", "Form validation"],
                    "correct_answer": 0,
                    "explanation": "ORM (Object-Relational Mapping) is used for database operations",
                    "technology": "django"
                }
            ]
        }
        
        # Get questions for the requested technology, default to python if not found
        tech_questions_list = tech_questions.get(technology.lower(), tech_questions.get('python', []))
        
        while len(questions) < count:
            for q in tech_questions_list:
                if len(questions) >= count:
                    break
                q_copy = q.copy()
                q_copy['technology'] = technology  
                questions.append(q_copy)
        
        return questions[:count]


class QuestionShuffler:
    """Shuffle questions for different users"""
    
    @staticmethod
    def shuffle_questions(questions, user_id):
        """Shuffle questions based on user ID for consistent but unique ordering"""
        random.seed(str(user_id))
        shuffled = questions.copy()
        random.shuffle(shuffled)
        return shuffled


class TestGenerator:
    """Generate complete tests with aptitude and technical questions"""
    
    @staticmethod
    def generate_test(user, experience_level, technologies, 
                     num_aptitude=10, num_technical=10):
        """
        Generate a complete test for a user
        
        Returns:
        {
            'aptitude_questions': [...],
            'technical_questions': {tech1: [...], tech2: [...]}
        }
        """
        result = {
            'aptitude_questions': [],
            'technical_questions': {}
        }
        
        aptitude_qs = QuestionGenerator.generate_aptitude_questions(
            experience_level, num_aptitude
        )
        result['aptitude_questions'] = QuestionShuffler.shuffle_questions(
            aptitude_qs, user.id
        )
        
        for tech in technologies:
            tech_qs = QuestionGenerator.generate_technical_questions(
                experience_level, tech, num_technical
            )
            result['technical_questions'][tech] = QuestionShuffler.shuffle_questions(
                tech_qs, f"{user.id}_{tech}"
            )
        
        return result