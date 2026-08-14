import argparse
import base64
import logging
from bisect import bisect
from datetime import datetime
from importlib.metadata import PackageNotFoundError
from importlib.metadata import distribution
from pathlib import Path

import transaction
import zc.buildout
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from Products.CMFPlone.factory import _DEFAULT_PROFILE
from Products.CMFPlone.factory import addPloneSite
from Testing import makerequest
from zExceptions.unauthorized import Unauthorized
from zope.component.hooks import setSite


try:
    from collective.upgrade import run as upgrade
except ImportError:
    upgrade = None

try:
    distribution('plone.classicui')
    HAS_CLASSIC = True
except PackageNotFoundError:
    HAS_CLASSIC = False

try:
    distribution('plone.volto')
    HAS_VOLTO = True
except PackageNotFoundError:
    HAS_VOLTO = False


logger = logging.getLogger('collective.recipe.plonesite')


def getDistributionName(override=''):
    """Pick the plone.distribution to create the site with.

    ``plone.distribution`` is a core add-on, so it ships with Plone but is
    not a dependency of Products.CMFPlone.  Passing a distribution name to
    ``addPloneSite`` makes it import ``plone.distribution``, so only do that
    when a distribution package is actually installed.  Returning ``None``
    makes ``addPloneSite`` fall back to creating a bare site.

    ``override`` is the ``distribution`` buildout option: a distribution name
    to use verbatim, or ``none`` to skip distributions entirely.  Policy
    packages that run their own profile usually want ``none``, because the
    ``Plone`` metapackage pulls in both distribution packages and would
    otherwise always select ``classic``.
    """
    override = override.strip()
    if override:
        if override.lower() == 'none':
            return None
        return override
    if HAS_CLASSIC:
        return "classic"
    if HAS_VOLTO:
        return "volto"
    return None


# the madness with the comma is a result of product names with spaces
def getProductsWithSpace(opts):
    return [x.replace(',', '') for x in opts]


def runProfiles(plone, profiles):
    logger.info("Running profiles: %s", profiles)
    stool = plone.portal_setup
    for profile in profiles:
        if not profile.startswith('profile-'):
            profile = f"profile-{profile}"
        try:
            stool.runAllImportStepsFromProfile(
                profile, dependency_strategy='reapply'
            )
        except BaseException:
            stool.runAllImportStepsFromProfile(profile)


def create(
        container,
        site_id,
        site_replace,
        default_language,
        distribution=''):
    oids = container.objectIds()
    if site_id in oids:
        if site_replace:
            # Delete the site, ignoring events
            container._delObject(site_id, suppress_events=True)
            transaction.commit()
            logger.warning("Removed existing Plone Site")
        else:
            logger.warning(
                "A Plone Site already exists and will not be replaced"
            )
            return getattr(container, site_id), False

    distribution_name = getDistributionName(distribution)
    logger.info("Creating Plone Site with distribution: %s", distribution_name)
    addPloneSite(
        container,
        site_id,
        title="Plone",
        profile_id=_DEFAULT_PROFILE,
        distribution_name=distribution_name,
        setup_content=False,
        default_language=default_language,
        portal_timezone="UTC",
    )
    transaction.commit()
    logger.info("Added Plone Site")

    plone = getattr(container, site_id)
    setSite(plone)
    return plone, True


def main(app, parser):
    options = parser.parse_args()
    site_id = options.site_id
    site_replace = options.site_replace
    admin_user = options.admin_user
    admin_password = options.admin_password
    post_extras = options.post_extras
    pre_extras = options.pre_extras
    container_path = options.container_path
    default_language = options.default_language
    distribution = options.distribution
    host = options.vhm_host
    use_vhm = options.use_vhm == 'True'
    add_mountpoint = options.add_mountpoint == 'True'
    protocol = options.vhm_protocol
    port = options.vhm_port
    log_level = options.log_level

    # set up logging
    try:
        log_level = int(log_level)
    except ValueError:
        raise zc.buildout.UserError(
            f'The configured log-level is not valid: {log_level}'
        )
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

    # normalize our profile lists
    profiles_initial = getProductsWithSpace(options.profiles_initial)
    profiles = getProductsWithSpace(options.profiles)

    if upgrade is not None:
        if options.upgrade_profiles and options.upgrade_all_profiles:
            raise zc.buildout.UserError(
                'Using upgrade-profiles conflicts with upgrade-all-profiles'
            )

    if host and port and not use_vhm:
        environ = {'SERVER_NAME': host, 'SERVER_PORT': port}
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
                    paths=[container_path], create_mount_points=1
                )
            except Exception as e:
                raise zc.buildout.UserError(
                    f'An error ocurred while trying to add ZODB '
                    f'Mount Point {container_path}: {e}'
                )
        else:
            raise zc.buildout.UserError(
                f'No ZODB Mount Point at container-path {container_path} '
                f'and add-mountpoint not specified.'
            )

    container = app.unrestrictedTraverse(container_path)
    # create the plone site if it doesn't exist
    portal, created = create(
        container, site_id, site_replace, default_language, distribution
    )
    # set the site so that the component architecture will work
    # properly
    setSite(portal)

    if use_vhm:
        logger.info("******* UPDATING VHM INFORMATION ********")
        vhm_string = (
            f"/VirtualHostBase/{protocol}/{host}:{port}"
            f"/{site_id}/VirtualHostRoot"
        )
        portal.REQUEST['PARENTS'] = [app]
        try:
            portal.REQUEST._auth = b'Basic ' + base64.b64encode(
                f'{admin_user}:{admin_password}'.encode()
            )
            traverse = portal.REQUEST.traverse
            traverse(vhm_string)
            newSecurityManager(None, user)
            logger.info("******* SET VHM INFO TO %s *******", vhm_string)
        except Unauthorized:
            logger.info(
                "******* UNABLE TO SET VHM, this happens when the root "
                "object in the site is not accessible by Anonymous. If "
                "you provide the admin-password in the plonesite part, "
                "this error can be avoided. Otherwise, you need to "
                "publish that object. *******"
            )

    if portal and created:
        runProfiles(portal, profiles_initial)
        logger.info("Finished")

    def runExtras(portal, script_path):
        script = Path(script_path)
        if not script.exists():
            raise zc.buildout.UserError(
                f'The path to the extras script does not exist: {script_path}'
            )
        exec(compile(script.read_bytes(), str(script), 'exec'))

    for pre_extra in pre_extras:
        runExtras(portal, pre_extra)

    if upgrade is not None and (
        options.upgrade_portal
        or options.upgrade_profiles
        or options.upgrade_all_profiles
    ):
        runner = portal.restrictedTraverse('@@collective.upgrade.form')
        runner.upgrade(
            upgrade_portal=options.upgrade_portal,
            upgrade_profiles=options.upgrade_profiles,
            upgrade_all_profiles=options.upgrade_all_profiles,
        )

    if profiles:
        runProfiles(portal, profiles)

    for post_extra in post_extras:
        runExtras(portal, post_extra)

    # commit the transaction
    transaction.commit()
    noSecurityManager()


if __name__ == '__main__':
    now_str = datetime.now().strftime('%Y-%m-%d-%H%M%S')
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s", "--site-id",
        dest="site_id", default=f"Plone-{now_str}",
    )
    parser.add_argument(
        "-c", "--container-path", dest="container_path", default="/",
    )
    parser.add_argument(
        "-r", "--site-replace",
        dest="site_replace", action="store_true", default=False,
    )
    parser.add_argument(
        "-l", "--default-language", dest="default_language", default="en",
    )
    parser.add_argument(
        "-d", "--distribution", dest="distribution", default="",
    )
    parser.add_argument(
        "-u", "--admin-user", dest="admin_user", default="admin",
    )
    parser.add_argument(
        "-P", "--admin-password", dest="admin_password", default="",
    )

    parser.add_argument(
        "-g", "--profiles-initial",
        dest="profiles_initial", action="append", default=[],
    )
    parser.add_argument(
        "-x", "--profiles", dest="profiles", action="append", default=[],
    )

    if upgrade is not None:
        parser.add_argument(
            '-U', '--upgrade-portal', action="store_true",
            help='Run all upgrade steps for the core Plone baseline profile.',
        )
        parser.add_argument(
            '-A', '--upgrade-all-profiles', action="store_true",
            help='Run all upgrade steps for all installed extension profiles.',
        )
        parser.add_argument(
            '-G', '--upgrade-profile',
            action='append', dest='upgrade_profiles',
            help='Run all upgrades for the given profile.  '
                 'May be given multiple times to upgrade multiple profiles.',
        )

    parser.add_argument(
        "-e", "--post-extras",
        dest="post_extras", action="append", default=[],
    )
    parser.add_argument(
        "-b", "--pre-extras",
        dest="pre_extras", action="append", default=[],
    )

    parser.add_argument("--use-vhm", dest="use_vhm", default='True')
    parser.add_argument(
        "--add-mountpoint", dest="add_mountpoint", default='False',
    )
    parser.add_argument("--host", dest="vhm_host", default='')
    parser.add_argument("--protocol", dest="vhm_protocol", default='http')
    parser.add_argument("--port", dest="vhm_port", default='80')

    parser.add_argument("--log-level", dest="log_level", default='20')
    main(app, parser)  # noqa
