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
import sys
import pytest
import filecmp

# Import from parent directory
sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__) + "/..")))
import pmb.aportgen


@pytest.fixture
def args(tmpdir, request):
    import pmb.parse
    sys.argv = ["pmbootstrap.py", "chroot"]
    args = pmb.parse.arguments()
    setattr(args, "logfd", open("/dev/null", "a+"))
    setattr(args, "_aports_real", args.aports)
    args.aports = str(tmpdir)
    request.addfinalizer(args.logfd.close)
    return args


def test_aportgen(args):
    # Create aportgen folder -> code path where it still exists
    pmb.helpers.run.user(args, ["mkdir", "-p", args.work + "/aportgen"])

    # Generate all valid packages (gcc-armhf twice, so the output folder
    # exists)
    for pkgname in ["binutils-armhf", "musl-armhf", "gcc-armhf", "gcc-armhf"]:
        pmb.aportgen.generate(args, pkgname)
        path_new = args.aports + "/" + pkgname + "/APKBUILD"
        path_old = args._aports_real + "/" + pkgname + "/APKBUILD"
        assert os.path.exists(path_new)
        assert filecmp.cmp(path_new, path_old, False)


def test_aportgen_invalid_generator(args):
    with pytest.raises(ValueError) as e:
        pmb.aportgen.generate(args, "pkgname-with-no-generator")
    assert "No generator available" in str(e.value)
