"""
Custom password validators for Django authentication system
Including checks for uppercase letters, lowercase letters, digits, and symbols.
Add these validators to AUTH_PASSWORD_VALIDATORS in settings.py
to enforce password complexity requirements.
For more information, see: https://docs.djangoproject.com/en/5.0/topics/auth/passwords/
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class UpperCaseValidator:
	def validate(self, password, user=None):
		if not any(char.isupper() for char in password):
			raise ValidationError(
				_('This password must contain at least one uppercase letter.'),
				code='password_no_upper',
			)

	def get_help_text(self):
		return _('Your password must contain at least one uppercase letter.')


class LowerCaseValidator:
	def validate(self, password, user=None):
		if not any(char.islower() for char in password):
			raise ValidationError(
				_('This password must contain at least one lowercase letter.'),
				code='password_no_lower',
			)

	def get_help_text(self):
		return _('Your password must contain at least one lowercase letter.')


class DigitValidator:
	def validate(self, password, user=None):
		if not any(char.isdigit() for char in password):
			raise ValidationError(
				_('This password must contain at least one digit.'),
				code='password_no_digit',
			)

	def get_help_text(self):
		return _('Your password must contain at least one digit.')


class SymbolValidator:
	def __init__(self, symbols='!@#$%&*()_+-=[]{}|;:<>/?'):
		self.symbols = symbols

	def validate(self, password, user=None):
		if not any(char in self.symbols for char in password):
			raise ValidationError(
				_('This password must contain at least one of these symbols: %(symbols)s'),
				code='password_no_symbol',
				params={'symbols': self.symbols},
			)

	def get_help_text(self):
		return _('Your password must contain at least one symbol: %(symbols)s') % {'symbols': self.symbols}
