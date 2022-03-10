import logging
import sqlite3
import sys

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

# db connection count since start
db_connection_count = 0
# current number of posts (will be update on every index retrieval)
number_of_posts = 0


# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row

    global db_connection_count
    db_connection_count += 1

    return connection


# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()

    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                              (post_id,)).fetchone()
    connection.close()
    return post


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'


# Define the main route of the web application
@app.route('/')
def index():
    global number_of_posts
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    number_of_posts = len(posts)

    app.logger.debug('DEBUG: retrieved {} posts'.format(number_of_posts))

    connection.close()
    return render_template('index.html', posts=posts)


# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.warn('Non-existing page with id {} requested :('.format(post_id))
        return render_template('404.html'), 404
    else:
        app.logger.info('Article {} retrieved successfully!'.format(post['title']))
        return render_template('post.html', post=post)


# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('\"About us\" page retrieved !')
    return render_template('about.html')


# Define the post creation functionality
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                               (title, content))
            connection.commit()
            connection.close()

            app.logger.info('New article \"{}|" created!'.format(title))
            return redirect(url_for('index'))

    return render_template('create.html')


@app.route('/healthz')
def checkhealth():
    # try to connect
    connection = get_db_connection()
    if connection:
         # then check if there are rows
        table_exists = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='posts'")
        if table_exists:
            response = app.response_class(
                response=json.dumps({"result": "OK - healthy"}),
                status=200,
                mimetype='application/json'
            )
            app.logger.info('Health request successful')
            return response
        else:
            app.logger.warn('No posts found')
    else:
        app.logger.error('No database was found or created')
    
    response = app.response_class(
                response=json.dumps({"result": "ERROR - unhealthy"}),
                status=500,
                mimetype='application/json'
            )
    return response


@app.route('/metrics')
def metrics():
    response = app.response_class(
        response=json.dumps({"db_connection_count": db_connection_count, "post_count": number_of_posts}),
        status=200,
        mimetype='application/json'
    )
    app.logger.debug('Metrics request successfull')
    return response


# start the application on port 3111
if __name__ == "__main__":
    logging.basicConfig(filename='app.log', level=logging.DEBUG)

    # we don't want to use print for stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)

    app.logger.addHandler(stdout_handler)

    app.run(host='0.0.0.0', port='3111')
