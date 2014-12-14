#TODO(mmd) INSERT LICENSE

from oslo.utils import importutils
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import exc as sa_exc

from neutron.common import exceptions as nexception
from neutron.db import common_db_mixin
from neutron.db import model_base
from neutron.db import models_v2
#TODO Refactor to use lbaas service instead... not sure how thats gonna work.
from neutron.db.loadbalancer import loadbalancer_db 
from neutron.plugins.common import constants

#from neutron import manager
from neutron.openstack.common import log as logging
from neutron.openstack.common import uuidutils

LOG = logging.getLogger(__name__)


class Certificate(model_base.BASEV2, models_v2.HasId, models_v2.HasTenant):
    name = sa.Column(sa.String(255))
    description = sa.Column(sa.String(255))
    cert_data = sa.Column(sa.String(1024))
    cert_type = sa.Column(sa.Enum('Certificate', 'Key', 'CA'), nullable=False)


class CertificateVipBinding(model_base.BASEV2, models_v2.HasId):
    vip_id = sa.Column(sa.String(36), sa.ForeignKey("vips.id"), nullable=False, primary_key=True)
    certificate_id = sa.Column(sa.String(36), sa.ForeignKey("certificates.id"), nullable=False, primary_key=True)


class CertificatesManager(common_db_mixin.CommonDbMixin):
    """Provides DB access to certificates and certificate/VIP bindings"""
    supported_extension_aliases = ["certificates"]

    def __init__(self, manager=None):
        #TODO Investigate usage of manager
        # manager = None is UT usage where CertificateManager is loaded as core plugin
        self.manager = manager

    def get_plugin_name(self):
        #TODO Implement
        return constants.CERTIFICATES

    def get_plugin_name(self):
        #TODO: Implement
        return constants.CERTIFICATES

    def get_plugin_description(self):
        return "Neutron SSL/TLS Certificates and VIP Bindings"

    def _get_certificate(self, context, certificate_id):
        try:
            return self._get_by_id(context, Certificate, certificate_id)
        except sa_exc.NoResultFound:
            raise CertificateNotFound(certificate_id=certificate_id)


    def _make_certificate_dict(self, certificate_db, fields=None):
        res = {'id': certificate_db['id'],
               'name': certificate_db['name'],
               'description': certificate_db['description'],
               'cert_data': certificate_db['cert_data'],
               'cert_type': certificate_db['cert_type']}
        return self._fields(res,fields)

    def _make_certificate_vip_binding_dict(self, binding_db, fields=None):
        res = {'vip_id': binding_db['vip_id'],
               'certificate_id': binding_db['certificate_db']}
        return self._fields(res,fields)


    def create_certificate(self, context, certificate):
        cert = certificate['certificate']
        with context.session.begin(subtransactions=True):
            cert_db = Certificate(id=uuidutils.generate_uuid(),
                                  name=cert['name'],
                                  description=cert['description'],
                                  cert_data=cert['cert_data'],
                                  cert_type=cert['cert_type'])
            context.session.add(cert_db)
        return self._make_certificate_db(cert_db)

    def update_certificate(self, context, certificate_id, certificate):
        cert = certificate['certificate']
        with context.session.begin(subtransactions=True):
            cert_db = self.get_certificate(context, certificate_id)
            cert_db.update(cert)

        return self._make_certificate_dict(cert_db)

    def get_certificate(self, context, certificate_id, fields=None):
        cert = self._get_certificate(context, certificate_id)
        return self._make_certificate_dict(cert, fields)

