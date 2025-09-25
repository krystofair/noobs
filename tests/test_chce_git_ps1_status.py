"""
Automatyczny test sprawdzania czy skrypt bash poprawnie wprowadza nową zmienną PS1.

"""
# XXX: Czy da się podpiąć pod terminal i sprawdzać co wyświetla.

import os
import sys
import shlex
import re
import tempfile
import pytest
import itertools
import subprocess
# import unittest
import warnings

import shutil
import contextlib as ctxlib


@ctxlib.contextmanager
def make_backup_file(filename):
    """Thanks to that this not gonna hurt your .bashrc file :)"""
    FN_BAK= f"{filename}.bak"
    try:  # make backup
        shutil.copyfile(filename, FN_BAK)
        yield
    finally:  # restore file
        if os.path.exists(FN_BAK):
            os.remove(filename)
            shutil.move(FN_BAK, filename)

# Check it just like that, but I know this is not the best approach
# to determine tested script path
# This require that in /usr/src/ is a link to repository

# XXX: Jak te ścieżki powinny rzeczywiście wyglądać?
SCRIPT_PATH="/usr/src/noobs/actions/chce_git_status_PS1.sh"
USER_BASHRC_FILE = f"{os.environ['HOME']}/.bashrc"


def exp_ps1_formats(onl=''):
    """
    Returns list of good format, but in regex format because of some optional chars.
    Pass arguments to get concrete version of PS1 formats.
    """
    ps1_formats = [
        r"($(__git_ps1 %s))[\u@\h] \w<ONL>$ ",
        r"($(__git_ps1 %s)) [\u@\h] \w<ONL>$ ",
        r"\u@\h \w ($(__git_ps1 %s))<ONL>$ ",
        r"\u@\h \e[33m\w\e[00m ($(__git_ps1 %s))<ONL>$ ",
        r"\u@\h \e[33m\w\e[00m $(__git_ps1 %s)<ONL>$ "
    ]
    return [x.replace('<ONL>', onl) for x in ps1_formats]



# Prompts which user will be asked for.
# warnings.filterwarnings("ignore", category=DeprecationWarning)
PROMPTS = [
"Wybierz powłokę[$def_sh] spośród $all_shells: ", #0
"Czy zainstalować dla wszystkich użytkowników? ${all_user_install_hint}: ", #1
"Czy wyświetlać stan kiedy występuje konflikt podczas 'merge'u itp? y/N: ", #2
"Czy wyświetlać tzw dirty state (pliki zmodyfikowane itp)? Y/n: ", #3
"Czy wyświetlać symbol \$ kiedy są pliki w 'git stash'? y/N: ", #4
"Czy ukrywać status kiedy folder jest ignorowany przez GITa? Y/n: ", #5
"Czy chcesz, aby status wyświetlał się w różnym kolorze w zależności od stanu? Y/n: ", #6
"Wybierz format: ", #7
"Czy chcesz mieć znak zachęty w nowej linii? Y/n: " #8
]
# warnings.resetwarnings()

# Content produced by script in bashrc
INFO_ABOUT_ADDITION = "# === Dodane przez skrypt 'chce_git_status_PS1.sh'. ===\n"
EXPORT_GITDIRTYSTATE_VAR = "export GIT_PS1_SHOWDIRTYSTATE=y;\n"

def defaults_choices(choices=None):
    if not choices:
        choices = ['' for _ in range(len(PROMPTS))]
    choices[0] = ''  # always default shell
    choices[7] = '1' # for almost all tests choose first format
    return choices

@pytest.fixture
def off_all_choices():
    """With default format 1"""
    choices = ['n' for _ in range(len(PROMPTS))]
    return defaults_choices(choices)


def run_script(inputs):
    cmd = SCRIPT_PATH
    command = shlex.split(cmd)
    # Pass inputs with '\n' will work well
    return subprocess.run(command, text=True, shell=True, input='\n'.join(inputs),
                         capture_output=True)


def test_user_install_branch_name_only(off_all_choices):
    """Show git status without state like * or + or *+"""
    user_inputs=off_all_choices
    # test default and set explicit
    # for opt in ['y', '']:
    user_inputs[3] = 'n'
    with make_backup_file(USER_BASHRC_FILE):
        cp = run_script(user_inputs)
        if cp.returncode != 0:
            assert False, cp.stdout + cp.stderr
        with open(USER_BASHRC_FILE, 'r', encoding='utf-8') as bashrc:
            content = bashrc.read()

        assert EXPORT_GITDIRTYSTATE_VAR not in content, "Flag is set, but shouldn't"
        match = re.search("PS1.*\$\(__git_ps1.*\%s\)", content)
        assert bool(match), "There should be one %s argument placeholder."

def test_user_install_colored(off_all_choices):
    """
    Branch name will be visible with color, this is based on GIT_PS1_SHOWCOLORHINTS
    variable so when it is exported in .bashrc the branch-name line will be in color.
    Here we test present of this variable, no is there color sentence, cause this
    is functionality provided by external script.
    """
    user_inputs = off_all_choices
    # test default and set explicit
    for opt in ['y', '']:
        user_inputs[6] = opt
        with make_backup_file(USER_BASHRC_FILE):
            cp = run_script(user_inputs)
            if cp.returncode != 0:
                assert False, cp.stdout + cp.stderr
            with open(USER_BASHRC_FILE, 'r', encoding='utf-8') as bashrc:
                content = bashrc.read()

            assert "export GIT_PS1_SHOWCOLORHINTS=y" in content, \
                    "GIT_PS1_SHOWCOLORHINTS not found"


def test_choosen_format(off_all_choices):
    user_inputs = off_all_choices
    possible_formats_choices = range(1, len(exp_ps1_formats()))
    for format_nr in possible_formats_choices:
        user_inputs[7] = str(format_nr)
        for new_line_before_dollar in ['n', '', 'y']:
            user_inputs[8] = new_line_before_dollar
            onl = '' if new_line_before_dollar == 'n' else r'\n'
            exp_ps1_format = exp_ps1_formats(onl)[format_nr-1]
            with make_backup_file(USER_BASHRC_FILE):
                cp = run_script(user_inputs)
                if cp.returncode != 0:
                    assert False, cp.stdout + cp.stderr
                with open(USER_BASHRC_FILE, 'r', encoding='utf-8') as bashrc:
                    content = bashrc.read()

                assert exp_ps1_format in content, \
                        "Properly format is not found in bashrc/profile file."

