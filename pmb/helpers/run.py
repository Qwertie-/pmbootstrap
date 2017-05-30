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
import subprocess
import logging


def core(args, cmd, log_message, log, return_stdout, check=True):
    logging.debug(log_message)
    """
    Run the command and write the output to the log.

    :param check: raise an exception, when the command fails
    """

    try:
        ret = None
        if log:
            if return_stdout:
                ret = subprocess.check_output(cmd).decode("utf-8")
                args.logfd.write(ret)
            else:
                subprocess.check_call(cmd, stdout=args.logfd,
                                      stderr=args.logfd)
            args.logfd.flush()
        else:
            logging.debug("*** output passed to pmbootstrap stdout, not" +
                          " to this log ***")
            subprocess.check_call(cmd)

    except subprocess.CalledProcessError as exc:
        if check:
            raise RuntimeError("Command failed: " + log_message) from exc
        else:
            pass
    return ret


def user(args, cmd, log=True, working_dir=None, return_stdout=False,
         check=True):
    """
    :param working_dir: defaults to args.work
    """
    if not working_dir:
        working_dir = args.work

    # TODO: maintain and check against a whitelist
    return core(args, cmd, "% " + " ".join(cmd), log, return_stdout, check)


def root(args, cmd, log=True, working_dir=None, return_stdout=False,
         check=True):
    """
    :param working_dir: defaults to args.work
    """
    cmd = ["sudo"] + cmd
    return user(args, cmd, log, working_dir, return_stdout, check)
