"""
Shared globals for this cast.
"""

import vars

TMPDIR = "/tmp"
DEFAULT_TIMEOUT = 60

VARS = vars.Vars()


class log():
    """
    The (to be expanded) central logging function.
    """
    @staticmethod
    def debug(msg):
        print("DEBUG: %s" % (msg))

    @staticmethod
    def info(msg):
        print("INFO: %s" % (msg))

    @staticmethod
    def warning(msg):
        print("WARNING: %s" % (msg))

    @staticmethod
    def error(msg):
        print("ERROR: %s" % (msg))


def uuid():
    return str(uuid.uuid4())


def replace_variables(indoc):
    """
    Analyze the provided 'indoc' (or list), looking for:
    This is recursive on itself for the appropriate data types.
    """
    def _std_eval(v):
        # if the braces aren't matched we log an error and bail.
        lefties = str(v).count("($")
        righties = str(v).count("$)")

        if lefties != righties:
            print("Unmatched braces in variable expression - unable to evaluate, returning ''.")
            # remove braces so it won't try to replace again
            v = v.replace("($", "").replace("$)", "")
            return v

        bail = 0
        while "($" in str(v):
            # We're doing an rfind... coming in from the right(bottom) so nested variables will work
            b = v.rfind("($")
            e = v.find("$)", b)
            expression = v[b + 2:e]

            print("    Evaluating an escaped variable expression: %s" % (expression))

            if expression:
                result = VARS.get(expression)
                print("    Found : %s" % (result))

                v = v.replace("($" + expression + "$)", str(result))
            bail = bail + 1
            if bail >= 100:
                print("Variable replacement on %s in infinite loop.  Check closing braces." % (v))
                # remove braces so it won't try to replace again
                v = v.replace("($" + expression + "$)", "").replace("($", "").replace("$)", "")

        return v

    if type(indoc) is list:
        for ii, item in enumerate(indoc):
            indoc[ii] = replace_variables(item)
    elif type(indoc) is dict:
        for k, v in indoc.iteritems():
            print("Considering Key: %s" % (k))

            # if the value is a dict or list, drill down into it
            if type(v) is dict or type(v) is list:
                print("    [%s] is an object, drilling in..." % (k))
                indoc[k] = replace_variables(v)
                # only report if it was a variable and we replaced
                # (aka if the result is different than what we sent in)
                if indoc[k] != v:
                    print("    [%s] is now [%s]" % (k, indoc[k]))
                # WE MUST CONTINUE NOW, otherwise the following will RECONSIDER
                # the work we just did, with undesirable results
                continue

            print("    [%s] is not a special keyword, looking for escaped variables..." % (k))
            # Not a specific keyword?  we also support an alternate variable
            # replacement on a string value itself.  This matches what we do in
            # the Task Engine.
            indoc[k] = _std_eval(v)
            # only report if it was a variable and we replaced
            # (aka if the result is different than what we sent in)
            if indoc[k] != v:
                print("    [%s] is now [%s]" % (k, indoc[k]))
    else:
        # hmmm, input 'doc' was neither a list nor a dict...
        # let's just give it a try assuming it's a string
        indoc = _std_eval(indoc)

    print("Result: %s" % indoc)
    return indoc
