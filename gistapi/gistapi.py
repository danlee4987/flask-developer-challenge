# coding=utf-8
"""
Exposes a simple HTTP API to search a users Gists via a regular expression.

Github provides the Gist service as a pastebin analog for sharing code and
other develpment artifacts.  See http://gist.github.com for details.  This
module implements a Flask server exposing two endpoints: a simple ping
endpoint to verify the server is up and responding and a search endpoint
providing a search across all public Gists for a given Github account.
"""

import requests
import re
from flask import Flask, jsonify, request


# *The* app object
app = Flask(__name__)


@app.route("/ping")
def ping():
    """Provide a static response to a simple GET request."""
    return "pong"


def gists_for_user(username):
    """Provides the list of gist metadata for a given user.

    This abstracts the /users/:username/gist endpoint from the Github API.
    See https://developer.github.com/v3/gists/#list-a-users-gists for
    more information.

    Args:
        username (string): the user to query gists for

    Returns:
        The dict parsed from the json response from the Github API.  See
        the above URL for details of the expected structure.
    """
    gists_url = 'https://api.github.com/users/{username}/gists'.format(
            username=username)
    response = requests.get(gists_url)
    # BONUS: What failures could happen?
    # BONUS: Paging? How does this work for users with tons of gists?

    return response.json()


def retrieve_content(gist_id):
    """Retrieves content of a gist, given its id.

    Args:
        gist_id(string): the id of the gist to retrieve

    Returns:
        Content of the gist (string).
    """
    id_url = 'https://api.github.com/gists/{id}'.format(id=gist_id)
    response = requests.get(id_url)

    get_data = response.json()['files']
    gist_file = str(get_data.keys()[0])
    g_file = get_data[gist_file]
    content = g_file['content']

    return content


def regex_match(content, pattern):
    """Searches gist content with a Regular Expression.

    Args:
        content(string): content of gist to search
        pattern(string): Regular Expression to search
    Returns:
        Boolean value indicating whether the Regular Expression
        was found or not.
    """
    p = re.compile(pattern)

    if p.match(content):
        return True
    else:
        return False


@app.route("/api/v1/search", methods=['POST'])
def search():
    """Provides matches for a single pattern across a single users gists.

    Pulls down a list of all gists for a given user and then searches
    each gist for a given regular expression.

    Returns:
        A Flask Response object of type application/json.  The result
        object contains the list of matches along with a 'status' key
        indicating any failure conditions.
    """
    post_data = request.get_json()
    # BONUS: Validate the arguments?

    username = post_data['username']
    pattern = post_data['pattern']

    result = {}
    matched = []
    status = 'success'
    return_url = 'https://gist.github.com/{username}/{id}'
    gists = gists_for_user(username)

    for gist in gists:
        try:
            gist_id = gist['id']
            content = retrieve_content(gist_id)

            if regex_match(content, pattern):
                url = return_url.format(username=username, id=gist_id)
                matched.append(url)
        except Exception:
            status = 'fail'
        # BONUS: What about huge gists?
        # BONUS: Can we cache results in a datastore/db?

    result['status'] = status
    result['username'] = username
    result['pattern'] = pattern
    result['matches'] = matched

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
