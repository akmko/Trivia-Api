import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    #CORS(app)
    cors = CORS(app, resources={r"/": {"origins": "*"}})
    
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    @app.route("/categories")
    def retrieve_categories():
        categories = Category.query.all()
        categories_dict={}
        for category in categories:
            categories_dict[category.id] = category.type


        return jsonify(
            {
                "success": True,
                "categories": categories_dict,
                "total_categories": len(categories),
            }
        )
    
    @app.route("/questions")
    def retrieve_questions():
        selection = Question.query.all()
        current_questions = paginate_questions(request, selection) 
        categories = Category.query.all()
        categories_dict={}
        for category in categories:
            categories_dict[category.id] = category.type
        
        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "total_questions": len(selection),
                "categories": categories_dict,
                "current_category": None
            }
        )
    
    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify(
                {
                    "success": True,
                    "deleted": question_id,
                    "questions": current_questions,
                    "total_questions": len(Question.query.all()),
                }
            )

        except:
            abort(422)

    @app.route("/questions", methods=["POST"])
    def create_question():
        body = request.get_json()

        new_question = body.get("question", None)
        new_answer = body.get("answer", None)
        new_category = body.get("category", None)
        new_difficulty = body.get("difficulty", None)
        search = body.get("searchTerm", None)
        if search:
            try:

                selection = Question.query.order_by(Question.id).filter(
                    Question.question.ilike("%{}%".format(search))
                )
                current_questions = paginate_questions(request, selection)

                return jsonify(
                    {
                        "success": True,
                        "questions": current_questions,
                        "current_category": None,
                        "total_questions": len(selection.all()),
                    }
                )


            except:
                abort(422)
                
        else:
            
            try:

                question = Question(question=new_question, answer=new_answer, category=new_category, difficulty=new_difficulty)
                question.insert()

                selection = Question.query.order_by(Question.id).all()
                current_questions = paginate_questions(request, selection)

                return jsonify(
                    {
                        "success": True,
                        "created": question.id,
                        "questions": current_questions,
                        "total_questions": len(Question.query.all()),
                    }
                )

            except:
                abort(422)


    @app.route('/categories/<int:id>/questions')
    def get_questions_on_category(id):
        category = Category.query.filter(Category.id==id).one_or_none()

        try:
            selection = Question.query.filter(Question.category==category.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                "success": True,
                "questions": current_questions,
                "total_questions": len(Question.query.all()),
                "current_category": category.type
            })

        except:
            abort(422)
            
            
    @app.route('/quizzes', methods=["POST"])
    def post_quizzes():
        try:
            data = request.get_json()
            category_id = int(data["quiz_category"]["id"])
            category = Category.query.get(category_id)
            previous_questions = data["previous_questions"]
            counter = 0
            if category:  
                if previous_questions:
                    questions = Question.query.filter(
                        Question.id.notin_(previous_questions),
                        Question.category == category.id
                        ).all()  
                else:
                    questions = Question.query.filter(Question.category == category.id).all()
            else:
                if previous_questions:
                    questions = Question.query.filter(Question.id.notin_(previous_questions)).all()  
                else:
                    questions = Question.query.all()
            question_length = len(questions)    
                
            if counter<question_length:               
                question = random.choice(questions).format()
                counter = counter + 1
            else:
                question = False

            return jsonify({
                "success": True,
                "question": question
            })
        except:
            abort(500, "An error occured while trying to load the next question")

    

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": 400, "message": "bad request"}), 400
    
    @app.errorhandler(500)
    def bad_request(error):
        return jsonify({"success": False, "error": 500, "message": "HTTP 500 Internal Server Error"}), 400


    return app
