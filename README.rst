***************************
collective.recipe.plonesite
***************************

Introduction
************

This recipe enables you to create and update a Plone site as part of a
buildout run. It runs GenericSetup profiles on creation and on every
buildout run. It is assumed that the install methods, setuphandlers,
upgrade steps, and other recipes will handle the rest of the work.

By default the site is created with a `plone.distribution
<https://github.com/plone/plone.distribution>`_ distribution when one is
available: ``classic`` if ``plone.classicui`` is installed, otherwise
``volto`` if ``plone.volto`` is installed. ``plone.distribution`` is a core
add-on rather than a dependency of ``Products.CMFPlone``, so when neither
package is present a plain Plone site is created instead. Use the
``distribution`` option to override that choice.

.. contents::

- Code repository: https://github.com/collective/collective.recipe.plonesite
- Report bugs at https://github.com/collective/collective.recipe.plonesite/issues

Options
=======

General Settings
----------------

site-id
    The id of the Plone site that the script will create. This will
    also be used to update the site once created. Default: Plone

admin-user
    The id of an admin user that will be used as the ``Manager``.
    Default: ``admin``

admin-password
    The password for the admin user. This is only needed when the ``use_vhm``
    option is set and the root object of the site is not accessible by
    ``Anonymous``.

instance
    The name of the instance that will run the script.
    Default: instance

zeoserver
    The name of the ``zeoserver`` part that should be used. This is
    only required if you are using a zope/zeo setup. Default: not set

container-path
    The path (relative from Zope root) to the container that should hold the
    Plone site.
    Default: ``/``

default-language
    The default language of the Plone site.
    Default: ``en``

distribution
    The name of the ``plone.distribution`` distribution to create the site
    with. The named distribution has to be registered, otherwise the site
    creation fails.

    The `Plone
    <https://github.com/plone/Plone/blob/6.2.1/setup.cfg#L43-L54>`_ package
    requires both ``plone.classicui`` and ``plone.volto``, thus auto-detection
    always picks ``classic`` and applies its base profiles first. This does not
    apply to a bare ``Products.CMFPlone`` install.

    Set it to ``none`` to create a plain Plone site without using
    ``plone.distribution`` at all. E.g. policies not shipping a distribution
    should::

        [plonesite]
        recipe = collective.recipe.plonesite
        site-id = mysite
        distribution = none
        profiles-initial = my.policy:default

    Default: not set, the distribution is auto-detected, see the introduction
    above.

use-sudo
    Run the task under a different user, as specified in the
    appropriate instance's buildout section. You need to configure
    sudo appropriately.

add-mountpoint
    Adds the ZODB Mount Point at the path specified by ``container-path``, if
    it doesn't exist. Very handy when used in conjunction with
    collective.recipe.filestorage.

Logging
-------

This recipe honors the ``log-level`` buildout-level config value, and the
``verbosity`` setting, overriding the running Zope instance's ``eventlog``
level. This allows you to get more logging output when running the part,
but have less verbosity when the site is actually running.

Install Profiles
----------------

profiles-initial
    A list of GenericSetup profiles to run just after initial site
    creation. See below for information on the expected profile id
    format [1]_.

profiles
    A list of GenericSetup profiles to run each time buildout is run.
    See below for information on the expected profile id format [1]_.

.. [1] Profiles have the following format: ``<package_name>:<profile>``
       (e.g. ``my.package:default``). The profile can also be prepended
       with the ``profile-`` if you so choose
       (e.g. ``profile-my.package:default``).

Run Scripts
-----------

pre-extras
    An absolute path to a file with python code that will be evaluated
    before running GenericSetup profiles. Multiple files can be given.
    Two variables will be available to you. The app variable is the Zope
    root. The portal variable is the plone site as defined by the
    site-id option. NOTE: file path cannot contain spaces. Default: not set

post-extras
    An absolute path to a file with python code that will be evaluated
    after running GenericSetup profiles. Multiple files can be given.
    Two variables will be available to you. The app variable is the Zope
    root. The portal variable is the plone site as defined by the
    site-id option. NOTE: file path cannot contain spaces. Default: not set

before-install
    A system command to execute before installing Plone. You could use
    this to start a Supervisor daemon to launch ZEO, instead of
    launching ZEO directly. You can use this option in place of the
    zeoserver option. Default: not set

after-install
    A system command to execute after installing Plone.
    Default: not set

Upgrading
---------

upgrade-portal
    Upgrade the site to the current version on the filesystem by
    running all upgrade steps for the site's base GenericSetup
    profile.  Requires `collective.upgrade`_ be installed.  Default: false

upgrade-all-profiles
    Upgrade all GenericSetup profiles installed in the site to their current
    versions on the filesystem by running all their upgrade steps.  Requires
    `collective.upgrade`_ be installed. Default: false

upgrade-profiles
    A list of GenericSetup profiles to run upgrade steps for each time buildout
    is run. Upgrades are run after ``profiles-initial`` and before
    ``profiles``. See above for information on the expected profile id format
    [1]_.  Requires `collective.upgrade`_ be installed.

site-replace
    Replace any existing plone site named ``site-id``. Default: false

enabled
    Option to start up the instance/zeoserver. Default: true. This can
    be a useful option from the command line if you do not want to
    start up Zope, but still want to run the complete buildout.

    $ bin/buildout -Nv plonesite:enabled=false

VHM (VirtualHostMonster)
------------------------

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
    # A profile with proper upgrade steps
    profiles-initial = addon.package:default
    profiles =
    # A profile not using upgrade steps, such as a simple policy package
        my.package:default
    upgrade-portal = True
    upgrade-all-profiles = True
    post-extras =
        ${buildout:directory}/my_script.py
    pre-extras =
        ${buildout:directory}/my_other_script.py
    host = www.mysite.com
    protocol = https
    port = 443


Example with default content
============================

Here is another example buildout.cfg that creates default Plone content
(News, Events, the front page, etc.) on initial site creation::

    [buildout]
    parts =
        ...
        plonesite-with-content

    [plonesite-with-content]
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


.. _collective.upgrade: https://pypi.python.org/pypi/collective.upgrade

Example with Multiple Mount Points
==================================

This uses collective.recipe.filestorage to create the mount point configuration::

    [buildout]
    parts =
        filestorage
        instance
        zeoserver
        plonesite1
        plonesite2

    [filestorage]
    recipe = collective.recipe.filestorage
    parts =
        mp1
        mp2

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

    [plonesite1]
    recipe = collective.recipe.plonesite
    add-mountpoint = true
    container-path = /mp1
    profiles-initial = Products.CMFPlone:plone-content
    site-id = portal

    [plonesite2]
    recipe = collective.recipe.plonesite
    add-mountpoint = true
    container-path = /mp2
    profiles-initial = Products.CMFPlone:plone-content
    site-id = portal
