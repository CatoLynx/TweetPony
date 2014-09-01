TweetPony – A Twitter library for Python
========================================
…it's called TweetPony because I developed it with ponies in mind.

License
-------
This program is licensed under the AGPLv3. See the `LICENSE` file for more information.

Installation
------------
You can easily install TweetPony using the Python Package Index. Just type:

	sudo pip install tweetpony

Usage basics
------------
You can see the internal names of all the API endpoints in the file `endpoints.py`.
For example, to update your status, you would do:

```python
status = api.update_status("Hello world!")
```

All the parameter names are the same as in the API documentation. Values will be automatically converted to their correct representation. For example, the boolean `True` will become the string `true`.

TweetPony has an internal model system which lets you perform actions related to the model quite easily!
Suppose you have a `Status` model:

```python
status = api.get_status(id = 12345)
```

Now if you want to favorite this status, you would probably do this:

```python
api.favorite(id = status.id)
```

But TweetPony makes this easier! You can just do:

```python
status.favorite()
```

and the pony will favorite the tweet!
Of course, this will only work if you obtained the `Status` instance through an API call, which should be the case 99% of the time. It won't work if you create the `Status` instance directly from a dictionary. But why would you do that?
You can also manually connect an `API` instance to a model instance by using the model's `connect_api` method.
For example, if you have two `API` instances (e.g. for two different users) and want to fetch a tweet with the first user's account and retweet it with the second user's account, you do:

```python
status = api1.get_status(id = 12345)
status.connect_api(api2)
status.retweet()
```

Look into `models.py` to see which methods exist for which models.

Details on function parameters
------------------------------
If you omit the paramater names in function calls, the order of parameters is as follows: First come all URL parameters / required parameters in the order they are listed in `endpoints.py`, then come all optional parameters.

Image uploading
---------------
For all API endpoints that take an image as a parameter, just pass the image file object to upload as the appropriate parameter and the pony will do the rest for you.
Multi-image uploading is supported too! Look into the `endpoints.py` and `api.py` files for details.

Error handling
--------------
On error, TweetPony will raise either an `APIError`, `NotImplementedError` or `ParameterError` exception.
An `APIError` instance has the following attributes:

`code`: The error code returned by the API *or* the HTTP status code in case of HTTP errors
`description`: The error description returned by the API *or* the HTTP status text in case of HTTP errors

`NotImplementedError` and `ParameterError` instances have only one attribute, the error description.

Models
------
Almost every API call (except for the ones that return only a list or something equally simple) will return a parsed model instance representing the response data.
There are `User`, `Status`, `Message`, `List`, `APIError` and many more models.
You can access the response data as instance attributes like `status.text` or using a dictionary lookup like `status['text']`.

Authentication
--------------
You can either pass your access token and access token secret when initializing the API instance or go through the normal authentication flow.
The authentication flow works like this:

```python
api = tweetpony.API(consumer_key = "abc", consumer_secret = "def")
auth_url = api.get_auth_url()
print "Open this link to obtain your authentication code: %s" % auth_url
code = raw_input("Please enter your authentication code: ")
api.authenticate(code)
```

After you've done this, the access token and access token secret can be obtained from the `API` instance as `api.access_token` and `api.access_token_secret`.
By default, TweetPony loads the authenticating user's profile as soon as all four authentication tokens are present. This is also a way of checking whether these tokens are correct. If you do not want the user to be loaded, pass `load_user = False` to the `API` constructor.
This is useful if:
* you want to save API calls
* you can be sure that the access tokens are correct
* you don't need the user profile (if you do, you can still load it using the `verify` function of the `API` instance)

Usage example
-------------
This is a simple example script. More can be found in the `examples` directory.

```python
import tweetpony
api = tweetpony.API(consumer_key = "abc", consumer_secret = "def", access_token = "ghi", access_token_secret = "jkl")
user = api.user
print "Hello, @%s!" % user.screen_name
text = raw_input("What would you like to tweet? ")
try:
	api.update_status(status = text)
except tweetpony.APIError as err:
	print "Oops, something went wrong! Twitter returned error #%i and said: %s" % (err.code, err.description)
else:
	print "Yay! Your tweet has been sent!"
```