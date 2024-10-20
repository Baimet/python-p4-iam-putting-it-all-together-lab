#!/usr/bin/env python3
from flask import request, session, jsonify
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        image_url = data.get('image_url')
        bio = data.get('bio')

        if username and password:
            new_user = User(
                username=username,
                image_url=image_url,
                bio=bio
            )
            new_user.password = password  # Use the password setter here
            db.session.add(new_user)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                return jsonify({"error": "Username already exists"}), 409

            session['user_id'] = new_user.id
            return jsonify({
                'id': new_user.id,
                'username': new_user.username,
                'image_url': new_user.image_url,
                'bio': new_user.bio
            }), 201

        return jsonify({"error": "Invalid data"}), 422

api.add_resource(Signup, '/signup')

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        
        user = User.query.get(user_id)
        if user:
            return jsonify({
                'id': user.id,
                'username': user.username,
                'image_url': user.image_url,
                'bio': user.bio
            }), 200
        return jsonify({"error": "Unauthorized"}), 401

api.add_resource(CheckSession, '/check_session')

class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.verify_password(password):
            session['user_id'] = user.id
            return jsonify({
                'id': user.id,
                'username': user.username,
                'image_url': user.image_url,
                'bio': user.bio
            }), 200
        return jsonify({"error": "Unauthorized"}), 401

api.add_resource(Login, '/login')

class Logout(Resource):
    def delete(self):
        if 'user_id' in session:
            session.pop('user_id')
            return '', 204
        return jsonify({"error": "Unauthorized"}), 401

api.add_resource(Logout, '/logout')

class RecipeIndex(Resource):
    def get(self):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        
        recipes = Recipe.query.all()
        recipe_list = [{
            'id': recipe.id,
            'title': recipe.title,
            'instructions': recipe.instructions,
            'minutes_to_complete': recipe.minutes_to_complete,
            'user': {
                'id': recipe.user.id,
                'username': recipe.user.username
            }
        } for recipe in recipes]

        return jsonify(recipe_list), 200

    def post(self):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        
        data = request.get_json()
        title = data.get('title')
        instructions = data.get('instructions')
        minutes_to_complete = data.get('minutes_to_complete')

        if title and instructions and len(instructions) >= 50:
            new_recipe = Recipe(
                title=title,
                instructions=instructions,
                minutes_to_complete=minutes_to_complete,
                user_id=session['user_id']
            )
            db.session.add(new_recipe)
            db.session.commit()
            return jsonify({
                'id': new_recipe.id,
                'title': new_recipe.title,
                'instructions': new_recipe.instructions,
                'minutes_to_complete': new_recipe.minutes_to_complete,
                'user': {
                    'id': new_recipe.user.id,
                    'username': new_recipe.user.username
                }
            }), 201
        return jsonify({"error": "Invalid data"}), 422

api.add_resource(RecipeIndex, '/recipes')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
