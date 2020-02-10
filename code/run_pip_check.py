import os
import sys
import glob
import subprocess
from ruamel.yaml import YAML

YAML = YAML()


def _mumnge_conda_pkg(pkg):
    parts = pkg.split('-')
    ver = parts[-2]
    # build = parts[-1].replace('.json', '')
    pkg = '-'.join(parts[0:-2])
    return pkg, ver


def _run_pip_check(pkg, platform):
    pip_check_ok = None
    os.makedirs("../artifacts/%s" % pkg, exist_ok=True)
    final_output = os.path.join("../artifacts/%s/pip_check.yml" % pkg)

    if os.path.exists(final_output):
        with open(final_output, 'r') as fp:
            res = YAML.load(fp)
            if 'No broken' in res['pip_check']:
                pip_check_ok = True
            else:
                pip_check_ok = False
        return True, pip_check_ok

    recipes = (
        glob.glob("libcfgraph/artifacts/%s/conda-forge/%s/%s*" % (pkg, platform, pkg))
        + glob.glob("libcfgraph/artifacts/%s/conda-forge/noarch/%s*" % (pkg, pkg)))

    ran_it = False
    tried = False
    os.system('rm -f pip_check_results.txt')

    for recipe in recipes:
        recipe = os.path.basename(recipe)
        if '-py37' in recipe or '-py_' in recipe:
            tried = True
            print("build:", recipe)
            _pkg, _ver = _mumnge_conda_pkg(recipe)
            print("install:", _pkg + "==" + _ver)
            print(" ")
            subprocess.run(
                './pip_check_it.sh ' + _pkg + ' ' + _ver,
                shell=True,
                capture_output=False,
            )
            ran_it = True
            break

    if os.path.exists("pip_check_results.txt") and ran_it:
        print("\npip check results:")
        with open("pip_check_results.txt", 'r') as fp:
            pc_res = fp.read()

        print(pc_res)
        res = {
            'pkg': pkg,
            'build': recipe.replace('.json', ''),
            'install': _pkg + "==" + _ver,
            'pip_check': pc_res}

        if 'No broken' in pc_res:
            pip_check_ok = True
        else:
            pip_check_ok = False

        with open(final_output, 'w') as fp:
            YAML.dump(res, fp)
            
        try:
            os.remove('pip_check_results.txt')
        except Exception:
            pass

    else:
        pip_check_ok = False

    return tried, pip_check_ok


if __name__ == '__main__':

    # run git config
    subprocess.run(
        "git config --global user.email 'circle_worker@email.com'",
        shell=True,
        check=True,
    )
    subprocess.run(
        "git config --global user.name 'circle worker'",
        shell=True,
        check=True,
    )

    if len(sys.argv) > 1:
        pkgs = ['libcfgraph/artifacts/' + sys.argv[1]]
    else:
        pkgs = glob.glob('libcfgraph/artifacts/*')

    tot = len(pkgs)
    tot_tried = 0
    tot_good = 0
    for i, pkg in enumerate(pkgs):
        pkg = os.path.basename(pkg)
        if pkg in ['nltk_data', 'nltk-data']:
            continue
        print("==============================================================")
        print("==============================================================")
        print("==============================================================")
        print("%d of %d" % (i+1, tot))
        print("%d of %d are ok" % (tot_good, tot_tried))
        print("pkg:", pkg)
        did_it, ok = _run_pip_check(pkg, 'linux-64')
        tot_tried += int(did_it)
        if did_it:
            tot_good += int(ok)

        subprocess.run(
            ["git add ../artifacts/*"],
            shell=True,
            check=True,
        )

        stat = subprocess.run(
            ["git status"],
            shell=True,
            check=True,
            capture_output=True,
        )
        status = stat.stdout.decode('utf-8')
        print(status)

        if "nothing to commit" not in status:
            subprocess.run(
                ["git commit -m '[ci skip] pip check data for %s: %s'" % (pkg, os.environ['CIRCLE_BUILD_URL'])],
                shell=True,
                check=True,
            )

            subprocess.run(
                ["git push"],
                shell=True,
                check=True,
            )

        print("\n\n")
