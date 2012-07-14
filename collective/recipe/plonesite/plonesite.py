import logging
import os
from datetime import datetime
from zope.app.component.hooks import setSite
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
            stool.runAllImportSteps()
        else:
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


def create(container, site_id, products_initial, profiles_initial,
        site_replace, default_language):
    oids = container.objectIds()
    if site_id in oids:
        if site_replace:
            try:
                container.manage_delObjects([site_id, ])
            except LinkIntegrityNotificationException:
                pass
            transaction.commit()
            logger.warrning("Removed existing Plone Site")
            oids = container.objectIds()
        else:
            logger.warning("A Plone Site already exists and will not be replaced")
            plone = getattr(container, site_id)
            return plone
    # actually add in Plone
    if site_id not in oids:
        if has_setup_content():
            # we have to simulate the new zmi admin screen here - at
            # least provide:
            # extension_ids
            # setup_content (plone default is currently 'true')
            from Products.CMFPlone.factory import addPloneSite
            extension_profiles = (
                'plonetheme.classic:default',
                'plonetheme.sunburst:default',
                )
            addPloneSite(
                container,
                site_id,
                extension_ids=extension_profiles,
                setup_content=False,
                default_language=default_language,
                )
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
    if plone:
        quickinstall(plone, products_initial)
    # run GS profiles
    runProfiles(plone, profiles_initial)
    logger.info("Finished")
    return plone


def setDefaultLanguageOnPortalLanguages(plone, default_language):
    # Plone factory does not set default_language on portal_languages (until
    # 4.1)
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
    post_extras = options.post_extras
    pre_extras = options.pre_extras
    container_path = options.container_path
    default_language = options.default_language
    host = options.vhm_host
    protocol = options.vhm_protocol
    port = options.vhm_port
    log_level = options.log_level

    # set up logging
    try:
        log_level = int(log_level)
    except ValueError:
        msg = 'The configured log-level is not valid: %s' % log_level
        raise zc.buildout.UserError(msg)
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

    container = app.unrestrictedTraverse(container_path)
    # create the plone site if it doesn't exist
    portal = create(container, site_id, products_initial, profiles_initial,
            site_replace, default_language)
    # set the site so that the component architecture will work
    # properly
    if not pre_plone3:
        setSite(portal)

    if host:
        logger.info("******* UPDATING VHM INFORMATION ********")
        vhm_string = "/VirtualHostBase/%s/%s:%s/%s/VirtualHostRoot" % (
                                    protocol, host, port, site_id)
        portal.REQUEST['PARENTS'] = [app]
        traverse = portal.REQUEST.traverse
        traverse(vhm_string)
        newSecurityManager(None, user)
        logger.info("******* SET VHM INFO TO %s *******", vhm_string)

    def runExtras(portal, script_path):
        if os.path.exists(script_path):
            execfile(script_path)
        else:
            msg = 'The path to the extras script does not exist: %s'
            raise zc.buildout.UserError(msg % script_path)

    for pre_extra in pre_extras:
        runExtras(portal, pre_extra)

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
    parser.add_option("-p", "--products-initial",
                      dest="products_initial", action="append", default=[])
    parser.add_option("-a", "--products",
                      dest="products", action="append", default=[])
    parser.add_option("-g", "--profiles-initial",
                      dest="profiles_initial", action="append", default=[])
    parser.add_option("-x", "--profiles",
                      dest="profiles", action="append", default=[])
    parser.add_option("-e", "--post-extras",
                      dest="post_extras", action="append", default=[])
    parser.add_option("-b", "--pre-extras",
                      dest="pre_extras", action="append", default=[])
    parser.add_option("--host",
                      dest="vhm_host", default='')
    parser.add_option("--protocol",
                      dest="vhm_protocol", default='http')
    parser.add_option("--port",
                      dest="vhm_port", default='80')
    parser.add_option("--log-level",
                      dest="log_level", default='20')
    main(app, parser)
