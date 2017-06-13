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
import logging
import os

import pmb.flasher
import pmb.install
import pmb.chroot.apk
import pmb.chroot.initfs
import pmb.chroot.other


def kernel(args):
    # Make sure, that at least one kernel is installed
    suffix = "rootfs_" + args.device
    pmb.chroot.apk.install(args, ["device-" + args.device], suffix)

    # Parse the kernel flavor
    flavor = args.flavor
    flavors = pmb.chroot.other.kernel_flavors_installed(args, suffix)
    if flavor:
        if flavor not in flavors:
            raise RuntimeError("No kernel installed with flavor " + flavor + "!" +
                               " Run 'pmbootstrap flasher list_flavors' to get a list.")
    elif not len(flavors):
        raise RuntimeError(
            "No kernel flavors installed in chroot " + suffix + "! Please let"
            " your device package depend on a package starting with 'linux-'.")
    else:
        flavor = flavors[0]

    # Rebuild the initramfs, just to make sure (see #69)
    pmb.chroot.initfs.build(args, flavor, "rootfs_" + args.device)

    # Generate the paths and run the flasher
    pmb.flasher.init(args)
    mnt = "/mnt/rootfs_" + args.device
    kernel = mnt + "/boot/vmlinuz-" + flavor
    ramdisk = mnt + "/boot/initramfs-" + flavor
    if args.action_flasher == "boot":
        logging.info("(native) boot " + flavor + " kernel")
        pmb.flasher.run(args, "boot", kernel, ramdisk)
    else:
        logging.info("(native) flash kernel " + flavor)
        pmb.flasher.run(args, "flash_kernel", kernel, ramdisk)


def list_flavors(args):
    suffix = "rootfs_" + args.device
    logging.info("(" + suffix + ") installed kernel flavors:")
    for flavor in pmb.chroot.other.kernel_flavors_installed(args, suffix):
        logging.info("* " + flavor)


def system(args):
    # Generate system image, install flasher
    img_path = "/home/user/rootfs/" + args.device + ".img"
    if not os.path.exists(args.work + "/chroot_native" + img_path):
        setattr(args, "sdcard", None)
        pmb.install.install(args, False)
    pmb.flasher.init(args)

    # Run the flasher
    logging.info("(native) flash system image")
    pmb.flasher.run(args, "flash_system", image=img_path)


def list_devices(args):
    pmb.flasher.run(args, "list_devices")


def frontend(args):
    action = args.action_flasher
    if action in ["boot", "flash_kernel"]:
        kernel(args)
    if action == "flash_system":
        system(args)
    if action == "list_flavors":
        list_flavors(args)
    if action == "list_devices":
        list_devices(args)
