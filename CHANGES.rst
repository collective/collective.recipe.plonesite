1.9.5 (2016-06-22)
==================

-  for GenericSetup 1.8.0+ set runAllImportStepsFromProfile to reapply
   the dependency profiles. This will keep our buildouts running as
   previously expected, with the profiles listed in the policy's metadata.xml
   being run every time
   [cdw9]

1.9.4 (2016-01-20)
==================

- Nothing new, but pypi was having issues with 1.9.3

1.9.3 (2016-01-15)
==================

- Plone 5 compatibility
  [santonelli]

1.9.2 (2015-06-22)
==================

- Only use valid Python logging levels. Round up to the closest level
  if the passed in value does not exist.
  [claytron]

1.9.1 (2014-12-01)
==================

- Add ability to ``use_vhm`` when the homepage is not accessible by
  ``Anonymous`` by setting the ``admin-password`` option.
  [claytron]

- PEP8 and pyflakes
  [claytron]

- Restore Python 2.4 compatibility
  [bryanlandia]

- Plone 5 compat, re-use add site form default profile logic.
  [@rpatterson]

1.9.0 (2014-08-29)
==================

- Add the ``add-mountpoint`` option to automatically create the mount-point if
  it does not exist.
  [fabiorauber]

- Add options for running profile upgrade steps if ``collective.upgrade`` is
  installed.
  [@rpatterson]

- Add an option to allow the use of sudo, if you have specified different UIDs for
  Zope and the ZEO server.
  [muellert]

- Clean up the docs and separate the options by headers.
  [claytron]

1.8.2 (2013-04-08)
==================

- Handle ``setSite`` import for Plone 4.3
  [claytron]

1.8.1 (2012-11-16)
==================

- Add changelog entry for 1.8.90
  [nrb]

1.8.0 (2012-11-16)
==================

- Add the ``use-vhm`` option to select traversal mode.
  Setting ``use-vhm`` to ``False`` will cause the traversal to use
  regular Zope traversal when running the recipe.
  [nrb]

1.7.3 (2012-11-02)
==================

- Use ``_delObject(site_id, suppress_events=True)`` to delete the site.
  This ignores all events and just removes the site completely when
  using the ``site-replace`` option.
  [claytron]

1.7.2 (2012-08-06)
==================

- Fixed typo on logger when removing existing Plone site.
  [hvelarde]

1.7.1 (2012-07-13)
==================

- Add support for changing the logging level used when the part runs,
  honoring the buildout log-level and verbosity. [davidblewett]

- Update version check to correctly differentiate between Plone 4.1.x
  and Plone 4.0 and below. [davidblewett]

1.6.3 (2012-07-03)
==================

- Update VirtualHostMonster support to correct loss of elevated security
  context. [davidblewett]

1.6.1 (2012-06-27)
==================

- Fix reST formatting. [nrb]

- Correct some doc oversights. [nrb]

1.6 (2012-06-26)
================

- Add VirtualHostMonster path support for the 'portal' variable 
  available in ``pre-extras`` and ``post-extras`` scripts. [nrb]

- ``host`` recipe option specifices a hostname to be used in
  a VirtualHostMonster path for extra recipe scripts. [nrb]

- ``port`` recipe option specifies a port to be used in a
  VirtualHostMonster path for extra recipe scripts. [nrb]

- ``protocol`` recipe option specifies a protocol to be used in 
  a VirtualHostMonster path from extra recipe scripts. [nrb]

- Fixed typo in documentation.
  [hvelarde]

- ``container-path`` recipe option specifies the path to the
  container where the Plone site will be added.
  [gotcha]

- ``default-language`` recipe option specifies the default language
  of the Plone site.
  [sgeulette]

1.5 (2011-09-22)
================

- Support for ``zope.globalrequest``.
  [gotcha]

- Support Plone 4.1
  [gotcha]

1.4.3 (2011-07-07)
==================

- Minor doc updates.
  [claytron]

1.4.2 (2011-07-07)
==================

- Released to plone.org
  [claytron]

- Doc updates.
  [claytron]

1.4.1 (2011-02-15)
==================

- Minor doc updates
  [claytron]

1.4 (2011-02-15)
================

- PEP8 cleanup
  [claytron]

- Handle new zeoserver recipe on windows which changes the name of the
  executable.
  [claytron]

- Use the ``plone`` variable not ``portal`` otherwise ``plonesite.py`` raises 
  ``NameError: global name 'portal' is not defined`` on a new install.
  [pelle]

- Enable GS profiles to work in plone 2.5
  [davismr]

- Use ``setSite`` in the initial creation as well.
  [claytron]

1.3 (2010-02-11)
================

- Use ``setSite`` in the ``plonesite`.py` script so that the component
  architecture gets initialized properly. This will allow the
  installation of a product like ``plone.app.dexterity``
  [clayton]

1.2 (2010-02-10)
================

- Update docs with info about how to add a ``Product``
  [claytron]

- Adjusted the support for Plone4 since the ``addPloneSite()`` has 
  changed slightly.
  [pelle]

1.1 (2009-11-10)
================

- Make sure to commit the transaction after adding the plone site to
  avoid some strange behavior.
  [claytron]

- Add support for Plone4
  [toutpt]

1.0 (2009-08-24)
================

- Added a ``before-install`` and ``after-install`` option to the recipe. this
  allows you to use something like supervisor to launch the processes.
  Thanks to Shane Hathaway for the patch.
  [claytron]

0.9 (2009-08-10)
================

- Fixed the ``site-id`` option so that it defaults to ``Plone`` properly.
  Thanks to aclark for the bug report.
  [claytron]

0.8 (2009-06-24)
================

- Subversion 1.6 and setuptools are not friends yet. Fixed upload.
  [claytron]

0.7 (2009-06-23)
================

- Clarification to docs.  Cleaning up copy/paste error to post-extras
  [andrewb]

- Fixed the ``instance`` option so that it defaults to ``instance`` properly
  [claytron]

0.6 (2008-12-16)
================

- Make ``admin-user`` configuration option truly optional per the documentation.  
  Fallback to ``admin`` which would be the common default per ZopeSkel's
  plone3_buildout template
  [andrewb]

- Added new options ``pre-extras`` and ``post-extras``.  The two options are files that
  can be run before and after the quickinstaller and profiles have been run.
  [claytron]

- Add condition so that the script can be used on older versions of plone
  [claytron]

0.5 (2008-11-11)
================

- Fixed a bug where already installed Products would not be re-installed
  [claytron]

- Added example buildout config and updated the READMEs
  [claytron]

- Re-factored the ``plonesite.py`` script
  [claytron]

- A dash of PEP 8
  [claytron]

0.4 (2008-11-11)
================

- Added a ``enabled`` option so that you can switch the part
  off from the command line. (``buildout:parts-=plonesite`` doesn't
  work yet)
  [claytron]

- Change the script so that profiles prefixed with ``profile-`` can
  also be given.
  [claytron]

- Added some docs to the recipe
  [claytron]

0.3 (2008-10-30)
================

- Added ``site-replace`` option to the readme
  [claytron]

- The ``site-replace`` option is no longer required
  [claytron]

0.2 (2008-10-30)
================

- new Plone sites will be created with a datetime suffix
  which is helpful if you need to re-run new instances
  over and over again e.g. for migration purposes. If you
  need a fixed site id then explictely set the id using
  the ``site-id`` option.
  [ajung]

- Fixed error with uninitialized variable
  [jeffk]

- Add buildout recipe option site-replace, defaults to
  off. Use with ``site-id``.

  New recipe option ``site-replace = on`` will remove any
  existing object in app named ``site-id``. A new plone site
  will be created to replace it.

  Default option setting ``site-replace = off`` will not remove
  existing objects in app named site-id.
  [jeffk]

0.1 (2008-10-11)
================

- Created recipe with ZopeSkel
  [claytron]
