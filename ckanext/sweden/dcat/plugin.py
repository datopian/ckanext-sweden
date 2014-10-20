import requests

import ckan.plugins as p

from ckanext.dcat.interfaces import IDCATRDFHarvester


VALIDATION_SERVICE = 'http://validator.dcat-editor.com/service'


class SwedenDCATRDFHarvester(p.SingletonPlugin):

    p.implements(IDCATRDFHarvester, inherit=True)

    def after_download(self, content, harvest_job):

        r = requests.post(VALIDATION_SERVICE, data=content)

        if r.status_code == 200:
            return content, []
        else:
            response = r.json()
            errors = []

            if response.get('rdfError'):
                errors.append(response.get('rdfError'))
            else:

                # TODO: expand
                errors.append('Validation errors where found')

            return None, errors
