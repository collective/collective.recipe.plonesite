"""
Options are as follows:

The id of the plone site to be created.
    --site-id=Plone
Replace any existing plone site named site-id. Defaults to off.
    --site-replace=off
The user to run the script as (needs to be a Manager at the root)
    --admin-user=admin
Add one --products argument per product you want to quickinstall when 
initially creating the site.
    --products-initial=MyProductName
Add one --products argument per product you want to quickinstall upon
every run of buildout.
    --products=MyProductName
Add one --profiles-initial argumanet per profile you want to run after the
quickinstall has run when initially creating the site.
    --profiles-inital=my.package:default
Add one --profiles argument per profile you want to run after the
quickinstall has run each time the buildout has been run.
    --profiles=my.package:default
"""

from datetime import datetime
import transaction
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from Testing import makerequest
from optparse import OptionParser
from plone.app.linkintegrity.exceptions import LinkIntegrityNotificationException

# the madness with the comma is a result of product names with spaces
def getProductsWithSpace(opts):
    return [x.replace(',', '') for x in opts]

def runProfiles(plone, profiles):
    print "Running profiles: %s" % profiles
    stool = plone.portal_setup
    for profile in profiles:
        if not profile.startswith('profile-'):
            profile = "profile-%s" % profile
        stool.runAllImportStepsFromProfile(profile)

def quickinstall(plone, products):
    print "Quick installing: %s" % products
    qit = plone.portal_quickinstaller
    not_installed_ids = [
        x['id'] for x in qit.listInstallableProducts(skipInstalled=1)
    ]
    installed_ids = [x['id'] for x in qit.listInstalledProducts()]
    installed_products = filter(installed_ids.count, products)
    not_installed = filter(not_installed_ids.count, products)
    if installed_products:
        qit.reinstallProducts(installed_products)
    if not_installed_ids:
        qit.installProducts(not_installed)

def create(app, site_id, products_initial, profiles_initial, site_replace):
    oids = app.objectIds()
    if site_id in oids:
        if site_replace and hasattr(app, site_id):
            try:
                app.manage_delObjects([site_id,])
            except LinkIntegrityNotificationException:
                pass
            transaction.commit()
            print "Removed existing Plone Site"
            oids = app.objectIds()
        else:
            print "A Plone Site already exists and will not be replaced"
            return
    # actually add in Plone
    if site_id not in oids:
        factory = app.manage_addProduct['CMFPlone']
        factory.addPloneSite(site_id, create_userfolder=1)
        print "Added Plone Site"
    # install some products
    plone = getattr(app, site_id)
    if plone:
        quickinstall(plone, products_initial)
    # run GS profiles
    runProfiles(plone, profiles_initial)
    print "Finished"

def main(app, parser):
    (options, args) = parser.parse_args()
    site_id = options.site_id
    site_replace = options.site_replace
    admin_user = options.admin_user
    
    # normalize our product/profile lists
    products_initial = getProductsWithSpace(options.products_initial)
    products = getProductsWithSpace(options.products)
    profiles_initial = getProductsWithSpace(options.profiles_initial)
    profiles = getProductsWithSpace(options.profiles)

    app = makerequest.makerequest(app)
    # set up security manager
    acl_users = app.acl_users
    user = acl_users.getUser(admin_user)
    if user:
        user = user.__of__(acl_users)
        newSecurityManager(None, user)
        print "Retrieved the admin user"
    else:
        print "Retrieving admin user failed"
    # create the plone site
    create(app, site_id, products_initial, profiles_initial, site_replace)
    # run profiles or install products
    if products or profiles:
        plone = getattr(app, site_id)
    if products:
        quickinstall(plone, products)
    if profiles:
        runProfiles(plone, profiles)
    # commit the transaction
    transaction.commit()
    noSecurityManager()

if __name__ == '__main__':
    now_str = datetime.now().strftime('%Y-%m-%d-%H%M%S')
    parser = OptionParser()
    parser.add_option("-s", "--site-id",
                      dest="site_id", default="Plone-%s" % now_str)
    parser.add_option("-r", "--site-replace",
                      dest="site_replace", action="store_true", default=False)
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
    main(app, parser)
