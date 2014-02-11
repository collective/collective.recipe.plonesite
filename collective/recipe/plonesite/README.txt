Options
=======

This recipe honors the ``log-level`` buildout-level config value, and the
``verbosity`` setting, overriding the running Zope instance's ``eventlog``
level. This allows you to get more logging output when running the part,
but have less verbosity when the site is actually running.

.. [1] Profiles have the following format: ``<package_name>:<profile>``
       (e.g. ``my.package:default``). The profile can also be prepended
       with the ``profile-`` if you so choose
       (e.g. ``profile-my.package:default``).

.. [2] The product name is typically **not** the package name such as
       ``Products.MyProduct``, but just the product name ``MyProduct``.
       Quickest way to find out the name that is expected is to
       'inspect' the Quickinstaller page and see what value it is
       passing in.

site-id
    The id of the Plone site that the script will create. This will
    also be used to update the site once created. Default: Plone

container-path
    The path (relative from Zope root) to the container that should hold the
    Plone site.
    Default: ``\``

admin-user
    The id of an admin user that will be used as the ``Manager``.
    Default: ``admin``

default-language
    The default language of the Plone site.
    Default: ``en``

products-initial
    A list of products to quick install just after initial site
    creation. See above for information about the product name
    format [2]_.

profiles-initial
    A list of GenericSetup profiles to run just after initial site
    creation. See above for information on the expected profile id
    format [1]_.

products
    A list of products to quick install each time buildout is run. See
    above for information about the product name format [2]_.

profiles
    A list of GenericSetup profiles to run each time buildout is run.
    See above for information on the expected profile id format [1]_.

instance
    The name of the instance that will run the script.
    Default: instance

zeoserver
    The name of the ``zeoserver`` part that should be used. This is
    only required if you are using a zope/zeo setup. Default: not set

before-install
    A system command to execute before installing Plone. You could use
    this to start a Supervisor daemon to launch ZEO, instead of
    launching ZEO directly. You can use this option in place of the
    zeoserver option. Default: not set

after-install
    A system command to execute after installing Plone.
    Default: not set

site-replace
    Replace any existing plone site named ``site-id``. Default: false

enabled
    Option to start up the instance/zeoserver. Default: true. This can
    be a useful option from the command line if you do not want to
    start up Zope, but still want to run the complete buildout.
    
    $ bin/buildout -Nv plonesite:enabled=false

pre-extras
    An absolute path to a file with python code that will be evaluated
    before running Quickinstaller and GenericSetup profiles. Multiple
    files can be given. Two variables will be available to you. The app
    variable is the Zope root. The portal variable is the plone site as
    defined by the site-id option. NOTE: file path cannot contain
    spaces. Default: not set

post-extras
    An absolute path to a file with python code that will be evaluated
    after running Quickinstaller and GenericSetup profiles. Multiple
    files can be given. Two variables will be available to you. The app
    variable is the Zope root. The portal variable is the plone site as
    defined by the site-id option. NOTE: file path cannot contain
    spaces. Default: not set

host
    A hostname used in VirtualHostMonster traversal.  This will set the
    root URL for the `portal` variable in any `pre-extras` or `post-extras`
    scripts. Default: not set

protocol
    Either 'http' or 'https' for a VirtualHostMonster path. Requires the
    host option be set. Default: http

port
    Port for the Zope site used in a VirtualHostMonster path. Requires the
    host option be set. Default: 80

use-vhm
    Signals whether Plone site should use VirtualHostMonster or ordinary
    Zope traversal when generating a request. Useful for setting up instances
    that will not be proxied behind Apache or Nginx, such as local development.
    Default: True

use-sudo
    Run the task under a different user, as specified in the
    appropriate instance's buildout section. You need to configure
    sudo appropriately.


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
    recipe = plone.recipe.zope2install
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
    post-extras =
        ${buildout:directory}/my_script.py
    pre-extras =
        ${buildout:directory}/my_other_script.py
    host = www.mysite.com
    protocol = https
    port = 443


Example with Plone 4 content enabled
====================================
    
Here is another example buildout.cfg with the plone4site recipe::
    
    [buildout]
    parts = 
        ...
        plone4site
    
    [plone4site]
    recipe = collective.recipe.plonesite
    site-id = test
    instance = instance
    zeoserver = zeoserver
    # Create default plone content like News, Events...
    profiles-initial = 
        Products.CMFPlone:plone-content 
        my.package:initial
    profiles = 
        my.package:default
        my.other.package:default
