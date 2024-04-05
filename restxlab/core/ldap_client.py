import logging
import os
from contextlib import contextmanager

import ldap3
from ldap3.core.exceptions import LDAPException
from ldap3.extend.microsoft.addMembersToGroups import (
    ad_add_members_to_groups as addUsersInGroups,
)
from ldap3.extend.microsoft.removeMembersFromGroups import (
    ad_remove_members_from_groups as removeUsersInGroups,
)

logger = logging.getLogger(__name__)

# environment variables
ldap_urls = eval(os.getenv("LDAP_URLS", "[]"))
ldap_username = os.getenv("LDAP_USERNAME", "")
ldap_pwd = os.getenv("LDAP_PASSSWORD", "")
search_base = os.getenv("LDAP_SEARCH_BASE", "")
ou_base = os.getenv("LDAP_OU_BASE", "")

receive_timeout = int(os.getenv("LDAP_RECEIVE_TIMEOUT", "45"))
time_limit = int(os.getenv("LDAP_TIME_LIMIT", "45"))
connect_timeout = int(os.getenv("LDAP_CONNECT_TIMEOUT", "10"))


class LDAPClientException(Exception):
    """exceptions generated from LDAPHandler class"""


@contextmanager
def ldap_exists_error():
    """cross cutting concern context manager exception
    handler for ldap exceptions where the object exists

    Raises:
        LDAPClientException: Only raise exception on actual error
        not when object already exists in AD as connection is
        configured to throw exceptions.
    """
    try:
        yield
    except (LDAPException, Exception) as error:
        if "AlreadyExists" not in str(error):
            raise LDAPClientException(error) from error
        logger.error(error)


class LDAPClient:
    """
    Class to handle LDAP moves, adds, and changes.
    """

    def __init__(self):
        try:
            self.search_base = search_base

            servers = []
            for url in ldap_urls:
                servers.append(ldap3.Server(host=url, connect_timeout=connect_timeout))

            pool = ldap3.ServerPool(servers, pool_strategy=ldap3.ROUND_ROBIN, active=True, exhaust=True)

            self.connection = ldap3.Connection(
                server=pool,
                user=ldap_username,
                password=ldap_pwd,
                auto_bind=True,
                raise_exceptions=True,
                receive_timeout=receive_timeout,
                client_strategy=ldap3.SAFE_SYNC,
            )
            logger.debug("ldap connection open complete.....")
        except (LDAPException, Exception) as error:
            raise LDAPClientException(error) from error

    def modify(self, group_dn, changes):
        """modify attributes of an AD object

        Args:
            group_dn (str): AD object distinguishedName
            changes (Dict[str,obj]): Dictionary of attributes and values

        Returns:
            status (boolean): ldap3 exec status
        """
        with ldap_exists_error():
            # generate ldap3 modifiguation dictionary
            mods = {}
            for key, value in changes.items():
                mods[key] = (ldap3.MODIFY_REPLACE, [value])

            status, result, response, _ = self.connection.modify(group_dn, mods)
            logger.info(status)
            logger.info(result)
            logger.info(response)

            return status

    def search(self, filter, attributes):
        """search for an LDAP object

        Args:
            filter (str): ldap search filter e.g.
            (&(objectCategory=Person)(sAMAccountName=zsvc))

            attributes (list(str)): list of ldap attributes to return

        Raises:
            LDAPClientException: Exception while querying ldap

        Returns:
            Dict: dictionary with attribute names and values or None if search was empty
        """
        try:
            status, result, response, _ = self.connection.search(
                search_base=self.search_base,
                search_filter=filter,
                search_scope=ldap3.SUBTREE,
                attributes=attributes,
                time_limit=time_limit,
            )
            logger.debug(status)
            logger.debug(result)

        except LDAPException as error:
            raise LDAPClientException(error) from error

        if len(response) == 0:
            return None

        return response[0].get("attributes")

    def create_ou(self, ou):
        """create an orginaization unit in the base OU

        Args:
            ou (str): ldap ou string to add

        Returns:
            str: ldap ou string created
        """
        ou_dn = f"OU={ou},{ou_base}"
        with ldap_exists_error():
            logger.info("create ou %s", ou_dn)
            status, result, response, _ = self.connection.add(ou_dn, "organizationalUnit")
            logger.debug(status)
            logger.debug(result)
            logger.debug(response)

        return ou_dn

    def get_ou(self, ou):
        """just return ou name appended to base"""
        return f"OU={ou},{ou_base}"

    def create_group(self, group, ou):
        """create a security group

        Args:
            group (str): group name
            ou (str): ou group is to be added under

        Returns:
            str: group distinguished name
        """
        group_dn = f"CN={group},{ou}"
        with ldap_exists_error():
            logger.info("create group %s", group_dn)
            attr = {"cn": group, "groupType": "-2147483640", "sAMAccountName": group}  # AD security group type

            status, result, response, _ = self.connection.add(group_dn, "group", attr)
            logger.debug(status)
            logger.debug(result)
            logger.debug(response)

        return group_dn

    def user_group_add(self, dn, group_dn):
        """add user DN to group

        Args:
            dn (str): user distinguished name
            group_dn (str): group distinguished name
        """
        with ldap_exists_error():
            logger.info("add user %s to %s", dn, group_dn)
            addUsersInGroups(self.connection, dn, group_dn)

    def user_group_remove(self, dn, group_dn):
        """remove user DN to group

        Args:
            dn (str): user distinguished name
            group_dn (str): group distinguished name
        """
        with ldap_exists_error():
            logger.info("remove user %s from %s", dn, group_dn)
            removeUsersInGroups(self.connection, dn, group_dn, fix=True)

    def close(self):
        """close all open connections in pool"""
        try:
            logger.debug("unbind client...")
            self.connection.unbind()
        except (LDAPException, Exception) as error:
            logger.error(error)
