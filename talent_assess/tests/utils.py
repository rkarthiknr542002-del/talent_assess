import random
from questions.models import Question
from bson import ObjectId
from datetime import datetime, date
from rest_framework.response import Response

def shuffle_questions(questions):
    """Shuffle questions list"""
    shuffled = questions.copy()
    random.shuffle(shuffled)
    return shuffled

def shuffle_options(question):
    """Shuffle options for a question"""
    if 'options' in question and 'correct_answer' in question:
        options = question['options']
        correct = question['correct_answer']
        
        pairs = list(enumerate(options))
        random.shuffle(pairs)
        
        new_options = []
        new_correct = None
        for new_idx, (old_idx, opt) in enumerate(pairs):
            new_options.append(opt)
            if old_idx == correct:
                new_correct = new_idx
        
        question['options'] = new_options
        question['correct_answer'] = new_correct
    
    return question

def validate_test_completion(test):
    """Validate if test can be completed"""
    if test.status == 'completed':
        return False, "Test already completed"
    
    if test.status == 'expired':
        return False, "Test expired"
    
    if test.is_expired():
        test.expire()
        return False, "Test time expired"
    
    return True, "OK"


def convert_objectid_to_str(obj):
    """
    Recursively convert all ObjectId instances to strings in any data structure
    """
    if obj is None:
        return None
    elif isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: convert_objectid_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [convert_objectid_to_str(item) for item in obj]
    elif hasattr(obj, '_id'):  # Django model instance
        try:
            return str(obj._id)
        except:
            return str(obj)
    else:
        return obj


def safe_response(data, status_code=200):
    """
    Return a Response with all ObjectIds converted to strings
    """
    converted_data = convert_objectid_to_str(data)
    return Response(converted_data, status=status_code)


class ObjectIdStr(str):
    """A string subclass that knows it came from an ObjectId"""
    pass