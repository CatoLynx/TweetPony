TweetPony – A Twitter library for Python
========================================
This API wrapper was inspired by [Tweepy](https://github.com/tweepy/tweepy). It's called TweetPony because I developed it with ponies in mind.

License
-------
This program is licensed under the AGPLv3. See the `LICENSE` file for more information.

Usage basics
------------
You can see the internal names of all the API endpoints in the file `endpoints.py`.
For example, to update your status, you would do:

	status = api.update_status(status = "Hello world!")

All the parameter names are the same as in the API documentation. Values will be automatically converted to their correct representation. For example, the boolean `True` will become the string `true`.

TweetPony has an internal model system which lets you perform actions related to the model quite easily!
Suppose you have a `Status` model:

	status = api.get_status(id = 12345)

Now if you want to favorite this status, you would probably do this:

	api.favorite(id = status.id)

But TweetPony makes this easier! You can just do:

	status.favorite()

and the pony will favorite the tweet!
Of course, this will only work if you obtained the `Status` instance through an API call, which should be the case 99% of the time. It won't work if you create the `Status` instance directly from a dictionary. But why would you do that?
You can also manually connect an `API` instance to a model instance by using the model's `connect_api` method.
For example, if you have two `API` instances (e.g. for two different users) and want to fetch a tweet with the first user's account and retweet it with the second user's account, you do:

	status = api1.get_status(id = 12345)
	status.connect_api(api2)
	status.retweet()

Look into `models.py` to see which methods exist for which models.

Attribute access
----------------
You can access a model's attributes as actual attributes, like `status.text` or as dictionary keys, like `status['text']`.

Image uploading
---------------
For all API endpoints that take an image as a parameter, just pass the image file object to upload as the appropriate parameter and the pony will do the rest for you.

Error handling
--------------
On error, TweetPony will raise either an `APIError`, `NotImplementedError` or `ParameterError` exception.
An `APIError` instance has the following attributes:

`code`: The error code returned by the API *or* the HTTP status code in case of HTTP errors
`description`: The error description returned by the API *or* the HTTP status text in case of HTTP errors

`NotImplementedError` and `ParameterError` instances have only one attribute, the error description.

Models
------
If you're not using the raw API call method, every API call will return a parsed model instance representing the response data.
There are `User`, `Status`, `Message`, `List` and `APIError` models.
You can access the response data as instance attributes like `status.text` or using a dictionary lookup like `status['text']`.

Authentication
--------------
You can either pass your access token and access token secret when initializing the API instance or go through the normal authentication flow.
The authentication flow works like this:

	api = tweetpony.API(consumer_key = "abc", consumer_secret = "def")
	auth_url = api.get_auth_url()
	print "Open this link to obtain your authentication code: %s" % auth_url
	code = raw_input("Please enter your authentication code: ")
	api.authenticate(code)

After you've done this, the access token and access token secret can be obtained from the `API` instance as `api.access_token` and `api.access_token_secret`.

Usage example
-------------

	import tweetpony
	api = tweetpony.API(consumer_key = "abc", consumer_secret = "def", access_token = "ghi", access_token_secret = "jkl")
	user = api.me
	print "Hello, @%s!" % user.screen_name
	text = raw_input("What would you like to tweet? ")
	try:
		api.post_statuses__update(status = text)
	except tweetpony.APIError as err:
		print "Oops, something went wrong! Twitter returned error #%i and said: %s" % (err.code, err.description)
	else:
		print "Yay! Your tweet has been sent!"
