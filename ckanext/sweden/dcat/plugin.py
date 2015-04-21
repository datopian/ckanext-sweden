import requests

from pylons import config

import ckan.plugins as p

from ckanext.dcat.interfaces import IDCATRDFHarvester


VALIDATION_SERVICE = 'https://validator.dcat-editor.com/service'


class SwedenDCATRDFHarvester(p.SingletonPlugin):

    p.implements(IDCATRDFHarvester, inherit=True)

    def after_download(self, content, harvest_job):

        if not p.toolkit.asbool(config.get('ckanext.sweden.harvest.use_validation', True)):
            return content, []

        validation_service = config.get('ckanext.sweden.harvest.validation_service', VALIDATION_SERVICE)

        stop_on_errors = p.toolkit.asbool(config.get('ckanext.sweden.harvest.stop_on_validation_errors', False))

        errors = []
        try:
            r = requests.post(validation_service, data=content)
        except requests.exceptions.RequestException, e:
            errors.append('Error contacting the validation service: {0}'.format(str(e)))

            if stop_on_errors:
                return None, errors
            else:
                return content, errors

        if r.status_code != 200:

            errors.append('The validation service returned an error: {0}'.format(
                r.status_code))

            if stop_on_errors:
                return None, errors
            else:
                return content, errors

        else:
            response = r.json()

            if not response.get('rdfError') and not response.get('errors'):
                # All clear
                return content, []

            if response.get('rdfError'):
                errors.append(response.get('rdfError'))
            else:
                if response.get('mandatoryError'):
                    for _class in response['mandatoryError']:
                        errors.append('Mandatory class {0} missing'.format(_class))
                for resource in response.get('resources', []):
                    for error in resource.get('errors', []):
                        msg = 'Error in resource {uri} (type {type}): {path}, {reason}'
                        code = error.get('code')
                        if code == 1:
                            reason = 'Too few values'
                        elif code == 2:
                            reason = 'Too many values'
                        else:
                            reason = ''

                        errors.append(msg.format(
                            uri=resource.get('uri'),
                            type=resource.get('type'),
                            path=error.get('path'),
                            reason=reason))

            if stop_on_errors:
                return None, errors
            else:
                return content, errors
