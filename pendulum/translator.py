# -*- coding: utf-8 -*-

import os
import re
import glob

import python_translate.selector as selector

from ._compat import load_module

LOCALE_REGEX = re.compile('^[a-z0-9@_\\.\\-]*$', re.I)


def load_locales():
    translations = {}
    root_path = os.path.join(os.path.dirname(__file__), 'lang')
    root = os.path.join(root_path, '__init__.py')

    # Loading parent module
    load_module('lang', root)

    for locale_file in glob.glob1(root_path, '*.py'):
        if locale_file.startswith('_'):
            continue

        locale = os.path.splitext(locale_file)[0]
        locale_file = os.path.join(root_path, '%s.py' % locale)

        # Loading locale
        locale_mod = load_module('lang.{}'.format(locale), locale_file)

        translations[locale] = locale_mod.translations

    return translations


class Translator(object):

    translations = load_locales()

    def __init__(self, locale):
        self._locale = self._normalize_locale(locale)

    @property
    def locale(self):
        """
        Returns the current locale.
        @rtype: str:
        @return: locale:
        """
        return self._locale

    @locale.setter
    def locale(self, value):
        """
        Sets the current locale.

        @type value: str
        @raises: ValueError If the locale contains invalid characters
        """
        self._assert_valid_locale(value)
        self._locale = value

    def trans(self, id, parameters=None, locale=None):
        """
        Translates the given message.

        :type id: str
        :param id: The message id

        :type parameters: dict
        :param parameters: A dict of parameters for the message

        :type locale: str
        :param locale: The locale or null to use the default

        :rtype: str
        :return: Translated message
        """
        if parameters is None:
            parameters = {}
        assert isinstance(parameters, dict)

        if locale is None:
            locale = self.locale
        else:
            locale = self._normalize_locale(locale)

        translations = self.load_translations(locale)
        while not translations:
            locale = self._get_fallback_locale(locale)
            translations = self.load_translations(locale)

        if id not in translations:
            return id

        msg = translations[id]

        return self.format(msg, parameters)

    def transchoice(self, id, number, parameters=None, locale=None):
        """
        Translates the given choice message by choosing a translation according
        to a number.

        :type id: str
        :param id: message id

        :type number: int
        :param number: number to use to find the indice of the message

        :type parameters: dict or None
        :param parameters: array of parameters for the message

        :type locale: str or None
        :param locale: locale or null to use the default

        :raises: ValueError

        :rtype: str
        :return: Translated message
        """
        if parameters is None:
            parameters = {}
        assert isinstance(parameters, dict)

        if locale is None:
            locale = self.locale
        else:
            self._normalize_locale(locale)


        translations = self.load_translations(locale)
        while not translations:
            locale = self._get_fallback_locale(locale)
            translations = self.load_translations(locale)

        if id not in translations:
            return id

        parameters['count'] = number
        msg = selector.select_message(
            translations[id],
            number,
            locale)

        return self.format(msg, parameters)

    def format(self, msg, parameters):
        return msg.format(**parameters)

    def load_translations(self, locale):
        locale = self._normalize_locale(locale)

        if locale in self.translations:
            return self.translations[locale]

        return False

    def _get_fallback_locale(self, locale):
        fallback = re.split('[-_]', locale)
        if fallback == locale:
            raise RuntimeError(
                'The "{0}" translations are not '
                'registered'.format(locale)
            )

        return fallback

    def _normalize_locale(self, locale):
        """
        Properly format locale.

        :param locale: The locale
        :type locale: str

        :rtype: str
        """
        self._assert_valid_locale(locale)

        m = re.match('([a-z]{2})[-_]([a-z]{2})', locale, re.I)
        if m:
            return '{}_{}'.format(m.group(1).lower(), m.group(2).lower())
        else:
            return locale.lower()

    def _assert_valid_locale(self, locale):
        """
        Asserts that the locale is valid, throws a ValueError if not.
        """
        if locale is not None and not LOCALE_REGEX.match(locale):
            raise ValueError("Invalid locale '%s'" % locale)
