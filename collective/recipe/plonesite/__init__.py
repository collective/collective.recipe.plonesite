# -*- coding: utf-8 -*-
"""Recipe plonesite"""

import os
import sys
import subprocess
import pkg_resources

class Recipe(object):
    """zc.buildout recipe"""

    def __init__(self, buildout, name, options):
        self.buildout, self.name, self.options = buildout, name, options
        options['location'] = os.path.join(
            buildout['buildout']['bin-directory'],
            self.name,
            )
        # suppress script generation.
        self.options['scripts'] = ''
        options['bin-directory'] = buildout['buildout']['bin-directory']
        self.site_id = options['site-id']
        self.admin_user = options['admin-user']
        self.products_initial = options.get('products-initial', "").split()
        self.profiles_initial = options.get('profiles-initial', "").split()
        self.products = options.get('products', "").split()
        self.profiles = options.get('profiles', "").split()
        options['args'] = self.createArgs()
        is_win = sys.platform[:3].lower() == "win"
        instance = buildout[options["instance"]]
        instance_home = instance['location']
        instance_script = os.path.basename(instance_home)
        if is_win:
            instance_script = "%s.exe" % instance_script
        options['instance-script'] = instance_script
        self.zeoserver = options.get('zeoserver', False)
        if self.zeoserver:
            if is_win:
                zeo_script = 'zeoservice.exe'
            else:
                zeo_home = buildout[self.zeoserver]['location']
                zeo_script = os.path.basename(zeo_home)
            options['zeo-script'] = zeo_script

    def install(self):
        """Installer"""
        options = self.options
        location = options['location']
        # start the zeo if it exists
        if self.zeoserver:
            zeo_cmd = "%(bin-directory)s/%(zeo-script)s" % options
            zeo_start = "%s start" % zeo_cmd
            subprocess.call(zeo_start.split())
        # XXX This seems wrong...
        options['script'] = pkg_resources.resource_filename(__name__, 'plonesite.py')
        # run the script
        cmd = "%(bin-directory)s/%(instance-script)s run %(script)s %(args)s" % options
        subprocess.call(cmd.split())
        # stop the zeo
        if self.zeoserver:
            zeo_stop = "%s stop" % zeo_cmd
            subprocess.call(zeo_stop.split())
        return location

    def update(self):
        """Updater"""
        pass

    def createArgs(self):
        """Helper method to create an argument list
        """
        args = []
        args.append("--site-id=%s" % self.site_id)
        args.append("--admin-user=%s" % self.admin_user)
        def createArgList(arg_name, arg_list):
            if arg_list:
                for arg in arg_list:
                    args.append("%s=%s" % (arg_name, arg))
        createArgList('--products-initial', self.products_initial)
        createArgList('--products', self.products)
        createArgList('--profiles-initial', self.profiles_initial)
        createArgList('--profiles', self.profiles)
        return " ".join(args)
