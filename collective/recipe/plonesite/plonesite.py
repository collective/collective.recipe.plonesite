import base64
import logging
import os
from bisect import bisect
from datetime import datetime
from pkg_resources import get_distribution
try:
    # Plone < 4.3
    from zope.app.component.hooks import setSite
except ImportError:
    # Plone >= 4.3
    from zope.component.hooks import setSite  # NOQA
from zExceptions.unauthorized import Unauthorized
import zc.buildout
import transaction
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from Testing import makerequest
from optparse import OptionParser

pre_plone3 = False
try:
    from plone.app.linkintegrity.exceptions import \
        LinkIntegrityNotificationException
except ImportError:
    # we are using a release prior to 3.x
    class LinkIntegrityNotificationException(Exception):
        pass
    pre_plone3 = True

try:
    from collective.upgrade import run as upgrade
except ImportError:
    upgrade = None


logger = logging.getLogger('collective.recipe.plonesite')


# the madness with the comma is a result of product names with spaces
def getProductsWithSpace(opts):
    return [x.replace(',', '') for x in opts]


def has_setup_content():
    try:
        from plone.app.upgrade import v41
        v41  # please pyflakes
        return True
    except ImportError:
        return False


def runProfiles(plone, profiles):
    logger.info("Running profiles: %s", profiles)
    stool = plone.portal_setup
    for profile in profiles:
        if not profile.startswith('profile-'):
            profile = "profile-%s" % profile
        if pre_plone3:
            stool.setImportContext(profile)
            continue
        try:
            stool.runAllImportStepsFromProfile(profile,
                                               dependency_strategy='reapply')
        except:
            stool.runAllImportStepsFromProfile(profile)


def quickinstall(plone, products):
    logger.info("Quick installing: %s", products)
    qit = plone.portal_quickinstaller
    not_installed_ids = [
        x['id'] for x in qit.listInstallableProducts(skipInstalled=1)]
    installed_ids = [x['id'] for x in qit.listInstalledProducts()]
    installed_products = filter(installed_ids.count, products)
    not_installed = filter(not_installed_ids.count, products)
    if installed_products:
        qit.reinstallProducts(installed_products)
    if not_installed_ids:
        qit.installProducts(not_installed)


def create(
        container, site_id, products_initial, profiles_initial,
        site_replace, default_language):
    oids = container.objectIds()
    if site_id in oids:
        if site_replace:
            # Delete the site, ignoring events
            container._delObject(site_id, suppress_events=True)
            transaction.commit()
            logger.warning("Removed existing Plone Site")
            oids = container.objectIds()
        else:
            logger.warning(
                "A Plone Site already exists and will not be replaced")
            plone = getattr(container, site_id)
            created = False
            return (plone, created)
    # actually add in Plone
    if site_id not in oids:
        created = True
        if has_setup_content():
            # we have to simulate the new zmi admin screen here - at
            # least provide:
            # extension_ids
            # setup_content (plone default is currently 'true')
            container.REQUEST.form.update({
                'form.submitted': True,
                'site_id': site_id,
                'setup_content': False,
                'default_language': default_language})
            form = container.restrictedTraverse('@@plone-addsite')
            # Skip the template rendering
            form.index = lambda: None
            form()
        else:
            factory = container.manage_addProduct['CMFPlone']
            factory.addPloneSite(site_id, create_userfolder=1)
        # commit the new site to the database
        transaction.commit()
        logger.info("Added Plone Site")
    plone = getattr(container, site_id)
    setDefaultLanguageOnPortalLanguages(plone, default_language)
    # set the site so that the component architecture will work
    # properly
    if not pre_plone3:
        setSite(plone)
    return (plone, created)


def setDefaultLanguageOnPortalLanguages(plone, default_language):
    # Plone factory does not set default_language on portal_languages (until
    # 4.1)
    if get_distribution('Products.CMFPlone').version < '4.1':
        portal_languages = plone.portal_languages
        portal_languages.setDefaultLanguage(default_language)
        supported = portal_languages.getSupportedLanguages()
        portal_languages.removeSupportedLanguages(supported)
        portal_languages.addSupportedLanguage(default_language)


def main(app, parser):
    (options, args) = parser.parse_args()
    site_id = options.site_id
    site_replace = options.site_replace
    admin_user = options.admin_user
    admin_password = options.admin_password
    post_extras = options.post_extras
    pre_extras = options.pre_extras
    container_path = options.container_path
    default_language = options.default_language
    host = options.vhm_host
    use_vhm = options.use_vhm
    use_vhm = use_vhm == 'True'
    add_mountpoint = options.add_mountpoint
    add_mountpoint = add_mountpoint == 'True'
    protocol = options.vhm_protocol
    port = options.vhm_port
    log_level = options.log_level

    # set up logging
    try:
        log_level = int(log_level)
    except ValueError:
        msg = 'The configured log-level is not valid: %s' % log_level
        raise zc.buildout.UserError(msg)
    current_log_levels = [
        logging.NOTSET,
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL,
    ]
    if log_level not in current_log_levels:
        try:
            # Find the nearest log level and use that
            lvl_index = bisect(current_log_levels, log_level)
            log_level = current_log_levels[lvl_index]
        except IndexError:
            # If the log level is higher, catch that
            log_level = 50
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    logger.setLevel(logging.getLevelName(log_level))
    for handler in root_logger.handlers:
        handler.setLevel(log_level)

    # normalize our product/profile lists
    products_initial = getProductsWithSpace(options.products_initial)
    products = getProductsWithSpace(options.products)
    profiles_initial = getProductsWithSpace(options.profiles_initial)
    profiles = getProductsWithSpace(options.profiles)

    if upgrade is not None:
        if options.upgrade_profiles and options.upgrade_all_profiles:
            raise zc.buildout.UserError(
                'Using upgrade-profiles conflicts with upgrade-all-profiles')

    if host and port and not use_vhm:
        environ = {
            'SERVER_NAME': host,
            'SERVER_PORT': port,
        }
        app = makerequest.makerequest(app, environ=environ)
    else:
        app = makerequest.makerequest(app)

    try:
        from zope.globalrequest import setRequest
        # support plone.subrequest
        app.REQUEST['PARENTS'] = [app]
        setRequest(app.REQUEST)
    except ImportError:
        pass

    # set up security manager
    acl_users = app.acl_users
    user = acl_users.getUser(admin_user)
    if user:
        user = user.__of__(acl_users)
        newSecurityManager(None, user)
        logger.info("Retrieved the admin user")
    else:
        raise zc.buildout.UserError('The admin-user specified does not exist')

    # Verify if the mount-point exists
    try:
        app.unrestrictedTraverse(container_path)
    except KeyError:
        if add_mountpoint:
            try:
                app.manage_addProduct['ZODBMountPoint'].manage_addMounts(
                    paths=[container_path], create_mount_points=1)
            except Exception, e:  # remove Exception as, to keep py2.4 support
                msg = (
                    'An error ocurred while trying to add ZODB '
                    'Mount Point %s: %s'
                )
                raise zc.buildout.UserError(msg % (container_path, str(e)))
        else:
            msg = (
                'No ZODB Mount Point at container-path %s and add-mountpoint '
                'not specified.'
            )
            raise zc.buildout.UserError(msg % container_path)

    container = app.unrestrictedTraverse(container_path)
    # create the plone site if it doesn't exist
    portal, created = create(container, site_id, products_initial,
                             profiles_initial, site_replace, default_language)
    # set the site so that the component architecture will work
    # properly
    if not pre_plone3:
        setSite(portal)

    if use_vhm:
        logger.info("******* UPDATING VHM INFORMATION ********")
        vhm_string = "/VirtualHostBase/%s/%s:%s/%s/VirtualHostRoot" % (
            protocol, host, port, site_id)
        portal.REQUEST['PARENTS'] = [app]
        try:
            portal.REQUEST._auth = 'Basic %s' % base64.encodestring(
                '%s:%s' % (admin_user, admin_password))
            traverse = portal.REQUEST.traverse
            traverse(vhm_string)
            newSecurityManager(None, user)
            logger.info("******* SET VHM INFO TO %s *******", vhm_string)
        except Unauthorized:
            logger.info(
                "******* UNABLE TO SET VHM, this happens when the root object "
                "in the site is not accessible by Anonymous. If you provide "
                "the admin-password in the plonesite part, this "
                "error can be avoided. Otherwise, you need to publish that "
                "object. *******"
            )

    if portal and created:
        quickinstall(portal, products_initial)
        runProfiles(portal, profiles_initial)
        logger.info("Finished")

    def runExtras(portal, script_path):
        if os.path.exists(script_path):
            execfile(script_path)
        else:
            msg = 'The path to the extras script does not exist: %s'
            raise zc.buildout.UserError(msg % script_path)

    for pre_extra in pre_extras:
        runExtras(portal, pre_extra)

    if upgrade is not None and (
            options.upgrade_portal or
            options.upgrade_profiles or options.upgrade_all_profiles):
        runner = portal.restrictedTraverse('@@collective.upgrade.form')
        runner.upgrade(
            upgrade_portal=options.upgrade_portal,
            upgrade_profiles=options.upgrade_profiles,
            upgrade_all_profiles=options.upgrade_all_profiles)

    if products:
        quickinstall(portal, products)
    if profiles:
        runProfiles(portal, profiles)

    for post_extra in post_extras:
        runExtras(portal, post_extra)

    # commit the transaction
    transaction.commit()
    noSecurityManager()

if __name__ == '__main__':
    now_str = datetime.now().strftime('%Y-%m-%d-%H%M%S')
    parser = OptionParser()
    parser.add_option("-s", "--site-id",
                      dest="site_id", default="Plone-%s" % now_str)
    parser.add_option("-c", "--container-path",
                      dest="container_path", default="/")
    parser.add_option("-r", "--site-replace",
                      dest="site_replace", action="store_true", default=False)
    parser.add_option("-l", "--default-language",
                      dest="default_language", default="en")
    parser.add_option("-u", "--admin-user",
                      dest="admin_user", default="admin")
    parser.add_option("-P", "--admin-password",
                      dest="admin_password", default="")

    parser.add_option("-p", "--products-initial",
                      dest="products_initial", action="append", default=[])
    parser.add_option("-a", "--products",
                      dest="products", action="append", default=[])
    parser.add_option("-g", "--profiles-initial",
                      dest="profiles_initial", action="append", default=[])
    parser.add_option("-x", "--profiles",
                      dest="profiles", action="append", default=[])

    if upgrade is not None:
        parser.add_option(
            '-U', '--upgrade-portal', action="store_true",
            help='Run all upgrade steps for the core Plone baseline profile.')
        parser.add_option(
            '-A', '--upgrade-all-profiles', action="store_true",
            help='Run all upgrade steps for all installed extension profiles.')
        parser.add_option(
            '-G', '--upgrade-profile',
            action='append', dest='upgrade_profiles',
            help='Run all upgrades for the given profile.  '
            'May be given multiple times to upgrade multiple profiles.')

    parser.add_option("-e", "--post-extras",
                      dest="post_extras", action="append", default=[])
    parser.add_option("-b", "--pre-extras",
                      dest="pre_extras", action="append", default=[])

    parser.add_option("--use-vhm",
                      dest="use_vhm", default='True')
    parser.add_option("--add-mountpoint",
                      dest="add_mountpoint", default='False')
    parser.add_option("--host",
                      dest="vhm_host", default='')
    parser.add_option("--protocol",
                      dest="vhm_protocol", default='http')
    parser.add_option("--port",
                      dest="vhm_port", default='80')

    parser.add_option("--log-level",
                      dest="log_level", default='20')
    main(app, parser)  # NOQA
