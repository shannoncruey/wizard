import sys
import os
import yaml
import requests
basepath = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
import functions
import shared


class Spell():

    def __init__(self, spellname):

        self.spellname = spellname
        self.spell = None

    def concentrate(self):
        """
        Anything that needs to happen before we cast...
        """
        pass

    def _load_spell(self):
        """
        Spells can be in a configurable directory, for now assuming BASE/spells.
        They can also be at a URL.
        """
        if "http" in self.spellname:
            url = self.spellname
            shared.log.info("Obtaining spell from [%s] ..." % (url))
            response = requests.get(url)
            response.raise_for_status()
            if response:
                self.spell = yaml.load(response.content)
                shared.log.info(self.spell)
        else:
            self.spellname = self.spellname if self.spellname.endswith(".yaml") else "%s.yaml" % (self.spellname)
            filename = os.path.join(basepath, "spells", "%s" % (self.spellname))
            shared.log.info("Loading spell file [%s] ..." % (filename))
            with open(filename, 'r') as f_in:
                stream = f_in.read()
                if stream:
                    self.spell = yaml.load(stream)
                    shared.log.info(self.spell)

    def cast(self):
        """
        Execute the spell...

        1) load the definition
        2) execute the first step
        """
        shared.log.info("Casting [%s] ..." % (self.spellname))
        self._load_spell()
        self.run_steps()

    def run_steps(self, branch=None):
        """
        Run the steps in a branch.  'main' is the default if
        'branch' is omitted.
        """
        branch = branch if branch else "main"
        shared.log.info("Processing branch [%s]" % (branch))
        i = 1
        for step in self.spell.get(branch, []):
            # add the step number to the step object
            step["number"] = i
            self.process_step(step)
            i = i + 1

    def process_step(self, step):
        """
        Depending on the 'function' in a step, we act differently
        """
        # all steps support the 'skip' parameter
        if step.get("skip"):
            shared.log.info("Skipping Step [%s]" % (step["number"]))
            return

        shared.log.info(("Processing Step [%s]" % (step["number"])))
        fn = step["function"]
        if fn == "log":
            functions.fn_log(step)
        elif fn == "branch":
            # special case here, just run a different branch of steps
            b = step.get("branch")
            if b:
                self.run_steps(b)
            else:
                raise Exception("'branch' function requires a 'branch' property.")
        elif fn == "connect":
            functions.fn_connect(step)
        elif fn == "shellcommand":
            functions.fn_shellcommand(step)
        elif fn == "http":
            functions.fn_http(step)
        else:
            shared.log.info("No handler for function [%s]" % (fn))
