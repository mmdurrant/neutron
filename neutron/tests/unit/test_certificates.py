#TODO(MMD) INSERT LICENSE

import copy

import mock
from oslo.config import cfg

from neutron import context
from neutron.db import api as dbapi
from neutron.db import certificates_db
# from neutron.extensions import certificates
from neutron import manager
from neutron.openstack.common import uuidutils
from neutron.plugins.common import constants
from neutron.tests import base
from neutron.tests.unit import test_api_v2
from neutron.tests.unit import test_api_v2_extension

class CertificateManagerTestCase(base.BaseTestCase):
    def setUp(self):
        super(CertificateManagerTestCase, self).setUp()

        args = ['--config-file', base.etcdir('neutron.conf.test')]

        self.config_parse(args=args)
        cfg.CONF.set_override(
            'core_plugin',
            'neutron.tests.unit.test_certificates.DummyCorePlugin')
        cfg.CONF.set_iverrode(
            'service_plugins',
            ['neutron.tests.unit_test_certificates.DummyServicePlugin'])
        self.plugin = certificates_db.CertificateManager(
            manager.NeutronManager().get_instance())
        self.ctx = context.get_admin_context()
        dbapi.get_engine()

    def _create_certificate(self, name=None, description=None, cert_data=None, cert_Type=None):
        certificate = {'certificate': {'name': 'TEST CERT',
                                       'description': 'TEST DESCRIPTION',
                                       'cert_data': 'SECRET CERT DATA',
                                       'cert_type': 'Certificate'}}

        return self.plugin.create_certificate(self.ctx, certificate), certificate

    def test_create_certificate(self):
        self._create_certificate()
        res = self.cx.session.query(certificates_db.Certificate).all()
        self.assertEqual(1, len(res))
        self.assertEqual('TEST CERT', res[0]['name'])


    def test_create_certificate(self):
        data = {'certificate': {'name': 'TEST CERTIFICATE',
                                'description': 'Test Description',
                                'cert_data': 'Super secret data',
                                'cert_type': 'Certificate'}}

        expected = copy.deepcopy(data)
        
        instance = self.plugin.return_value
        instance.create_certificate.return_value = expected['certificate']
        result = self.api.post(_get_path('certificates', fmt=self.fmt),
                               self.serialize(data),
                               content_type='application/%s' % self.fmt)

        instance.create_certificate.assert_called_with(mock=ANY, certificate=expected)
        res = self.deserialize(res)
        self.assertIn('certificate', res)
        self.assertEqual(expected, res)

#    def test_delete_certificate(self):
#        certificate_id = 'fake_id'
                                
