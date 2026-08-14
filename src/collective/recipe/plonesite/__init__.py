"""Recipe plonesite"""

import os
import subprocess
import sys
from importlib.resources import files

import zc.buildout


TRUISMS = {
    'yes',
    'y',
    'on',
    'true',
    'sure',
    'ok',
    '1',
}


def system(c):
    if os.system(c):
        raise SystemError("Failed", c)


class Recipe:
    """zc.buildout recipe"""

    def __init__(self, buildout, name, options):
        removed = [opt for opt in ('products', 'products-initial')
                   if options.get(opt, '').strip()]
        if removed:
            raise zc.buildout.UserError(
                f"The option(s) {', '.join(removed)} are no longer "
                f"supported in collective.recipe.plonesite 2.0+. "
                f"Plone 6 has no Quickinstaller; use GenericSetup "
                f"profiles via 'profiles' / 'profiles-initial' instead."
            )
        self.buildout, self.name, self.options = buildout, name, options
        options['location'] = os.path.join(
            buildout['buildout']['parts-directory'],
            self.name,
        )
        # suppress script generation.
        self.options['scripts'] = ''
        options['bin-directory'] = buildout['buildout']['bin-directory']

        # all the options that will be passed on to the 'run' script
        self.site_id = options.get('site-id', 'Plone')
        self.container_path = options.get('container-path', '/')
        self.site_replace = options.get('site-replace', '').lower() in TRUISMS
        self.default_language = options.get('default-language', 'en')
        self.distribution = options.get('distribution', '').strip()
        self.admin_user = options.get('admin-user', 'admin')
        self.admin_password = options.get('admin-password', '')

        self.profiles_initial = options.get('profiles-initial', "").split()
        self.profiles = options.get('profiles', "").split()

        self.upgrade_portal = options.get(
            'upgrade-portal', '').lower() in TRUISMS
        self.upgrade_all_profiles = options.get(
            'upgrade-all-profiles', '').lower() in TRUISMS
        self.upgrade_profiles = options.get('upgrade-profiles', '').split()

        self.post_extras = options.get('post-extras', "").split()
        self.pre_extras = options.get('pre-extras', "").split()

        self.vhm_protocol = options.get('protocol', "http")
        self.vhm_host = options.get('host', "")
        self.vhm_port = options.get('port', "80")
        self.use_vhm = options.get('use-vhm', True)

        self.use_sudo = options.get('use-sudo', False)
        add_mountpoint = options.get('add-mountpoint', '').lower()
        self.add_mountpoint = add_mountpoint in TRUISMS

        self.log_level = buildout._log_level
        options['args'] = self.createArgs()

        # We can disable the starting of zope and zeo.  useful from the
        # command line:
        # $ bin/buildout -v plonesite:enabled=false
        self.enabled = options.get('enabled', 'true').lower() in TRUISMS

        # figure out if we need a zeo server started, and if it's on windows
        # this code was borrowed from plone.recipe.runscript
        is_win = sys.platform == 'win32'
        # grab the 'instance' option and default to 'instance' if it does not
        # exist
        instance = buildout[options.get('instance', 'instance')]
        instance_home = instance['location']
        instance_script = os.path.basename(instance_home)
        if is_win:
            instance_script = f"{instance_script}.exe"
        options['instance-script'] = instance_script
        self.zeoserver = options.get('zeoserver', False)
        if self.zeoserver:
            if is_win:
                exe = os.path.join(options['bin-directory'], 'zeoservice.exe')
                if os.path.exists(exe):
                    zeo_script = 'zeoservice.exe'
                else:
                    zeo_script = f"{self.zeoserver}_service.exe"
            else:
                zeo_home = buildout[self.zeoserver]['location']
                zeo_script = os.path.basename(zeo_home)
            options['zeo-script'] = zeo_script
        self.before_install = options.get('before-install')
        self.after_install = options.get('after-install')

    def install(self):
        """
        1. Run the before-install command if specified
        2. Start up the zeoserver if specified
        3. Run the script
        4. Stop the zeoserver if specified
        5. Run the after-install command if specified
        """
        options = self.options
        # XXX is this needed?
        location = options['location']
        if self.enabled:
            if self.before_install:
                system(self.before_install)
            if self.zeoserver:
                zeo_cmd = (
                    f"{options['bin-directory']}/{options['zeo-script']}"
                )
                zeo_start = f"{zeo_cmd} start"

                if self.use_sudo:
                    zeo_start = f"sudo {zeo_start}"
                subprocess.call(zeo_start.split())

            # XXX This seems wrong...
            options['script'] = str(files(__name__).joinpath('plonesite.py'))
            # run the script
            cmd = (
                f"{options['bin-directory']}/{options['instance-script']} "
                f"run {options['script']} {options['args']}"
            )
            if self.use_sudo:
                cmd = f"sudo {cmd}"
            subprocess.call(cmd.split())

            if self.zeoserver:
                zeo_stop = f"{zeo_cmd} stop"
                if self.use_sudo:
                    zeo_stop = f"sudo {zeo_stop}"
                subprocess.call(zeo_stop.split())
            if self.after_install:
                system(self.after_install)

        return location

    def update(self):
        """Updater"""
        self.install()

    def createArgs(self):
        """Helper method to create an argument list
        """
        args = [
            f"--site-id={self.site_id}",
        ]
        # only pass the site replace option if it's True
        if self.site_replace:
            args.append("--site-replace")
        # leave the distribution auto-detection alone unless configured
        if self.distribution:
            args.append(f"--distribution={self.distribution}")
        args.extend([
            f"--admin-user={self.admin_user}",
            f"--admin-password={self.admin_password}",
            f"--container-path={self.container_path}",
            f"--default-language={self.default_language}",
            f"--host={self.vhm_host}",
            f"--port={self.vhm_port}",
            f"--use-vhm={self.use_vhm}",
            f"--protocol={self.vhm_protocol}",
            f"--log-level={self.log_level}",
            f"--add-mountpoint={self.add_mountpoint}",
        ])

        def createArgList(arg_name, arg_list):
            if arg_list:
                for arg in arg_list:
                    args.append(f"{arg_name}={arg}")

        createArgList('--pre-extras', self.pre_extras)
        createArgList('--post-extras', self.post_extras)

        createArgList('--profiles-initial', self.profiles_initial)
        createArgList('--profiles', self.profiles)

        if self.upgrade_portal:
            args.append("--upgrade-portal")
        if self.upgrade_all_profiles:
            args.append("--upgrade-all-profiles")
        createArgList('--upgrade-profile', self.upgrade_profiles)

        return " ".join(args)
