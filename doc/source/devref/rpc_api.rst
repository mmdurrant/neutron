=====================
Neutron RPC API Layer
=====================

Neutron uses the oslo.messaging library to provide an internal communication
channel between Neutron services.  This communication is typically done via
AMQP, but those details are mostly hidden by the use of oslo.messaging and it
could be some other protocol in the future.

RPC APIs are defined in Neutron in two parts: client side and server side.

Client Side
===========

Here is an example of an rpc client definition:

::

  from oslo import messaging

  from neutron.common import rpc as n_rpc


  class ClientAPI(object):
      """Client side RPC interface definition.

      API version history:
          1.0 - Initial version
          1.1 - Added my_remote_method_2
      """

      def __init__(self, topic):
          target = messaging.Target(topic=topic, version='1.0')
          self.client = n_rpc.get_client(target)

      def my_remote_method(self, context, arg1, arg2):
          cctxt = self.client.prepare()
          return cctxt.call(context, 'my_remote_method', arg1=arg1, arg2=arg2)

      def my_remote_method_2(self, context, arg1):
          cctxt = self.client.prepare(version='1.1')
          return cctxt.call(context, 'my_remote_method_2', arg1=arg1)


This class defines the client side interface for an rpc API.  The interface has
2 methods.  The first method existed in version 1.0 of the interface.  The
second method was added in version 1.1.  When the newer method is called, it
specifies that the remote side must implement at least version 1.1 to handle
this request.

Server Side
===========

The server side of an rpc interface looks like this:

::

  from oslo import messaging


  class ServerAPI(object):

      target = messaging.Target(version='1.1')

      def my_remote_method(self, context, arg1, arg2):
          return 'foo'

      def my_remote_method_2(self, context, arg1):
          return 'bar'


This class implements the server side of the interface.  The messaging.Target()
defined says that this class currently implements version 1.1 of the interface.

Versioning
==========

Note that changes to rpc interfaces must always be done in a backwards
compatible way.  The server side should always be able to handle older clients
(within the same major version series, such as 1.X).

It is possible to bump the major version number and drop some code only needed
for backwards compatibility.  For more information about how to do that, see
https://wiki.openstack.org/wiki/RpcMajorVersionUpdates.

Neutron RPC APIs
================

As discussed before, RPC APIs are defined in two parts: a client side and a
server side.  Several of these pairs exist in the Neutron code base.

DHCP
----

The DHCP agent includes a client API, neutron.agent.dhcp_agent.DhcpPluginAPI.
The DHCP agent uses this class to call remote methods back in the Neutron
server.  The server side is defined in
neutron.api.rpc.handlers.dhcp_rpc.DhcpRpcCallback.  It is up to the Neutron
plugin in use to decide whether the DhcpRpcCallback interface should be
exposed.

Similarly, there is an RPC interface defined that allows the Neutron plugin to
remotely invoke methods in the DHCP agent.  The client side is defined in
neutron.api.rpc.agentnotifiers.dhcp_rpc_agent_api.DhcpAgentNotifyApi.  The
server side of this interface that runs in the DHCP agent is
neutron.agent.dhcp_agent.DhcpAgent.

More Info
=========

For more information, see the oslo.messaging documentation:
http://docs.openstack.org/developer/oslo.messaging/.
