import sys
import os
import yaml

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
        Spells should be in a configurable directory, for now assuming BASE/spells.
        """
        filename = os.path.join(basepath, "spells", "%s.yaml" % (self.spellname))
        shared.log.info("Loading [%s] ..." % (filename))
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
