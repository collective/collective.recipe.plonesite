Options
=======

NOTE: Profiles have the following format: <package_name>:<profile> (e.g. my.package:default).  The profile can also be prepended with the 'profile-' if you so choose (e.g. profile-my.package:default).

site-id
    The id of the Plone site that the script will create.  This will also be used to update the site once created.  Default: Plone

admin-user
    The id of an admin user that will be used as the 'Manager'.  Default: admin

products-initial
    A list of products to quickinstall just after initial site creation

profiles-inital
    A list of GenericSetup profiles to run just after initial site creation

products
    A list of products to quickinstall each time buildout is run

profiles
    A list of GenericSetup profiles to run each time buildout is run

instance
    The name of the instance that will run the script. Default: instance

zeoserver
    The name of the zeoserver part that should be used.  This is only required if you are using a zope/zeo setup. Default: not set

site-replace
    Replace any existing plone site named site-id. Default: false

enabled
    Option to start up the instance/zeoserver.  Default: true.  This can be a useful option from the command line if you do not want to start up Zope, but still want to run the complete buildout.
    
    $ bin/buildout -Nv plonesite:enabled=false

Example
=======

Here is an example buildout.cfg with the plonesite recipe::

    [buildout]
    parts = 
        zope2
        instance
        zeoserver
        plonesite
    
    [zope2]
    recipe = plone.reciepe.zope2install
    ...
    
    [instance]
    recipe = plone.recipe.zope2instance
    ...
    eggs = 
        ...
        my.package
        my.other.package
    
    zcml = 
        ...
        my.package
        my.other.package
    
    [zeoserver]
    recipe = plone.recipe.zope2zeoserver
    ...
    
    [plonesite]
    recipe = collective.recipe.plonesite
    site-id = test
    instance = instance
    zeoserver = zeoserver
    profiles-initial = my.package:initial
    profiles = 
        my.package:default
        my.other.package:default
