"""
Copyright 2017 Oliver Smith

This file is part of pmbootstrap.

pmbootstrap is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

pmbootstrap is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pmbootstrap.  If not, see <http://www.gnu.org/licenses/>.
"""
import os
import json
import logging
import pmb.chroot
import pmb.chroot.apk
import pmb.parse.apkindex


def get_depends_recursively(args, pkgnames, arch=None):
    """
    :param pkgnames: List of pkgnames, for which the dependencies shall be
                     retrieved.
    """
    todo = list(pkgnames)
    ret = []
    seen = []
    while len(todo):
        pkgname = todo.pop(0)
        index_data = pmb.parse.apkindex.read_any_index(args, pkgname, arch)
        if not index_data:
            logging.debug(
                "NOTE: Could not find dependency " +
                pkgname +
                " in any APKINDEX.")
            continue
        pkgname = index_data["pkgname"]
        if pkgname not in pkgnames and pkgname not in ret:
            ret.append(pkgname)
        for depend in index_data["depends"]:
            if depend not in ret:
                if depend.startswith("!"):
                    continue
                for operator in [">", "="]:
                    if operator in depend:
                        depend = depend.split(operator)[0]
                if depend not in seen:
                    todo.append(depend)
                    seen.append(depend)
    return ret


def generate(args, apk_path, carch, suffix, apkbuild):
    """
    :param apk_path: Path to the .apk file, relative to the packages cache.
    :param carch: Architecture, that the package has been built for.
    :apkbuild: Return from pmb.parse.apkbuild().
    """
    ret = {"pkgname": apkbuild["pkgname"],
           "pkgver": apkbuild["pkgver"],
           "pkgrel": apkbuild["pkgrel"],
           "carch": carch,
           "versions": []}

    # Add makedepends versions
    installed = pmb.chroot.apk.installed(args, suffix)
    relevant = (apkbuild["makedepends"] +
                get_depends_recursively(args, [apkbuild["pkgname"], "abuild", "build-base"]))
    for pkgname in relevant:
        if pkgname in installed:
            ret["versions"].append(installed[pkgname]["package"])
    ret["versions"].sort()
    return ret


def write(args, apk_path, carch, suffix, apkbuild):
    """
    Write a .buildinfo.json file for a package, right after building it.
    It stores all information required to rebuild the package, very similar
    to how they do it in Debian (but as JSON file, so it's easier to parse in
    Python): https://wiki.debian.org/ReproducibleBuilds/BuildinfoFiles

    :param apk_path: Path to the .apk file, relative to the packages cache.
    :param carch: Architecture, that the package has been built for.
    :apkbuild: Return from pmb.parse.apkbuild().
    """
    # Write to temp
    if os.path.exists(args.work + "/chroot_native/tmp/buildinfo"):
        pmb.chroot.root(args, ["rm", "/tmp/buildinfo"])
    buildinfo = generate(args, apk_path, carch, suffix, apkbuild)
    with open(args.work + "/chroot_native/tmp/buildinfo", "w") as handle:
        handle.write(json.dumps(buildinfo, indent=4, sort_keys=True) + "\n")

    # Move to packages
    pmb.chroot.root(args, ["chown", "user:user", "/tmp/buildinfo"])
    pmb.chroot.user(args, ["mv", "/tmp/buildinfo", "/home/user/packages/user/" +
                           apk_path + ".buildinfo.json"])
