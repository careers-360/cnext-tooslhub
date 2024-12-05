import os
import datetime
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from django.contrib.auth import login as django_login, logout as django_logout
from django.utils.deprecation import MiddlewareMixin
from django.contrib.sessions.models import Session
from users.models import User

from django.conf import settings
from rest_framework_simplejwt.settings import api_settings as jwt_settings

class CookieHandlerJWTAuthentication(JWTAuthentication):
	
	def authenticate(self, request):
		"""
		If cookie contains access token, put it inside authorization header

		If We want to create an access token from refresh_token we can do:
		token = RefreshToken(refresh_token)
		access_token = token.access_token
		"""
		request.auth_header = None
		authentication_response = super().authenticate(request)
		return authentication_response

	def authenticate_header(self, request):
		if request.auth_header:
			#We have set a custom Error Code here in case we get an Access Expired
			#Basically we get a refresh token but we dont get an access token
			#In this case client needs to send a request to refresh token url
			#That will set a new access token along with a new refresh token
			#thus completing the process, ideally we can set a long Access Token
			#as access tokens are being stored in Same Site Secure Cookies
			#On Logout we need to clear any cookies set by us
			return 409
		return super().authenticate_header(request)

class CustomAuthMiddleware(MiddlewareMixin):

	def process_request(self, request):
		careers_cookie_session_id = ''
		if request.COOKIES:
			for k in request.COOKIES.keys():
				if 'CSESS360__' in k:
					careers_cookie_session_id = k

		if careers_cookie_session_id:
			session = Session.objects.filter(session_key=careers_cookie_session_id.replace('CSESS360__','')).first()
			if session:
				session_data = session.get_decoded()
				user_id = session_data.get('_auth_user_id')

				if User.objects.filter(id=user_id).exists():
					user = User.objects.get(id=user_id)
					token = user.token
					access_token = token.get('access')
					refresh_token = token.get('refresh')
					request.META['HTTP_AUTHORIZATION'] = 'Bearer %s' %(access_token)



	def process_response(self, request, response):
		careers_cookie_session_id = ''
		careers_cookie_logout_session_id = ''
		if request.COOKIES:
			for k in request.COOKIES.keys():
				if 'CSESS360__' in k:
					careers_cookie_session_id = k

				if 'SESS' in k and 'CSESS360__' not in k:
					careers_cookie_logout_session_id = k

		if not careers_cookie_session_id:
			response.delete_cookie('c360_jwt_access', domain=settings.SESSION_DOMAIN_NAME)
			response.delete_cookie('c360_jwt_refresh', domain=settings.SESSION_DOMAIN_NAME)


		if 'logout' in request.path:
			response.delete_cookie('c360_jwt_access')
			response.delete_cookie('c360_jwt_refresh')
			response.delete_cookie('sessionid')
			#Done for Careers360 Domain
			if careers_cookie_session_id:
				response.delete_cookie(careers_cookie_session_id)

			if careers_cookie_logout_session_id:
				response.delete_cookie(careers_cookie_logout_session_id)


			response.delete_cookie('c360_jwt_access', domain=settings.SESSION_DOMAIN_NAME)
			response.delete_cookie('c360_jwt_refresh', domain=settings.SESSION_DOMAIN_NAME)
			response.delete_cookie('sessionid', domain=settings.SESSION_DOMAIN_NAME)
			#Done for Careers360 Domain
			if careers_cookie_session_id:
				response.delete_cookie(careers_cookie_session_id, domain=settings.SESSION_DOMAIN_NAME)

			if careers_cookie_logout_session_id:
				response.delete_cookie(careers_cookie_logout_session_id, domain=settings.SESSION_DOMAIN_NAME)
		else:

			# if request.COOKIES and request.COOKIES.get('sessionid') and not request.COOKIES.get('c360_jwt_access'):
			# 	user_id = request.session.get('_auth_user_id')

			# 	if User.objects.filter(id=user_id).exists():
			# 		user = User.objects.get(id=user_id)
			# 		token = user.token
			# 		access_token = token.get('access')
			# 		refresh_token = token.get('refresh')
			# 		response.set_cookie('c360_jwt_access', access_token, max_age=jwt_settings.ACCESS_TOKEN_LIFETIME.total_seconds(), domain=settings.SESSION_DOMAIN_NAME)
			# 		response.set_cookie('c360_jwt_refresh', refresh_token, max_age=jwt_settings.REFRESH_TOKEN_LIFETIME.total_seconds(), domain=settings.SESSION_DOMAIN_NAME)
			
			if request.COOKIES and careers_cookie_session_id and not request.COOKIES.get('c360_jwt_access'):
				session = Session.objects.filter(session_key=careers_cookie_session_id.replace('CSESS360__','')).first()
				if session:
					session_data = session.get_decoded()
					user_id = session_data.get('_auth_user_id')

					if User.objects.filter(id=user_id).exists():
						user = User.objects.get(id=user_id)
						token = user.token
						access_token = token.get('access')
						refresh_token = token.get('refresh')
						response.set_cookie('c360_jwt_access', access_token, max_age=jwt_settings.ACCESS_TOKEN_LIFETIME.total_seconds(), domain=settings.SESSION_DOMAIN_NAME)
						response.set_cookie('c360_jwt_refresh', refresh_token, max_age=jwt_settings.REFRESH_TOKEN_LIFETIME.total_seconds(), domain=settings.SESSION_DOMAIN_NAME)
						response.set_cookie('sessionid', careers_cookie_session_id.replace('CSESS360__',''), max_age=jwt_settings.REFRESH_TOKEN_LIFETIME.total_seconds(), domain=settings.SESSION_DOMAIN_NAME)

		return response



