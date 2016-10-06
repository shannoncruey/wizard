import ast
import base64
import json
import re
from datetime import datetime, timedelta
import dateutil.parser as parser
from bson.objectid import ObjectId

import shared

# eval_get requires a safe environment to support some explicit language features for the eval.
# NOTE: some of these are limited in scope and have non-standard names.
EVAL_ENVIRONMENT = {'datetime': datetime,
                    'timedelta': timedelta,
                    'ObjectId': ObjectId,
                    'b64encode': base64.b64encode,
                    'b64decode': base64.b64decode,
                    'parsedate': parser.parse,
                    'asjson': json.dumps,
                    'fromjson': json.loads}

# There are many useful and safe Python built-ins, so let's add them
# to our eval environment.
for f in [
    'abs', 'all', 'any', 'bin', 'bool', 'bytearray', 'chr', 'cmp', 'divmod', 'enumerate', 'float', 'format',
    'hex', 'int', 'isinstance', 'len', 'list', 'long', 'max', 'min', 'oct', 'ord', 'pow', 'range', 'repr',
    'round', 'set', 'sorted', 'str', 'sum', 'tuple', 'unichr', 'unicode', 'zip'
]:
    EVAL_ENVIRONMENT[f] = eval(f)

class Vars():
    """
    The runtime variable stack for this instance, and supporting methods.
    """

    def __init__(self):
        self.stack = {}


    def _objectify(self, s):
        """ attempt to parse a string into a python object """
        shared.log.debug("_objectify got %s" % (s))
        try:
            out = ast.literal_eval(s)
        except:
            out = s

        shared.log.debug("_objectify resulted in %s" % (s))
        return out


    def set(self, expression, value):
        """
        evaluates an expression to find a specific item in the stack
        and sets it to a new value
        """
        if expression:
            newval = self._objectify(value)
            expression = expression.strip()
            shared.log.debug("update expression is:\n %s" % (expression))
            shared.log.debug("newval is:\n %s" % (newval))
            # exec is dangerous!
            # so, we only allow it to run against our stack collection

            # this isn't perfect, but we have to assume if _objectify returned a basestring
            # then the value is a string.
            # HOWEVER, it may very well contain quotes.
            # so let's use it's 'repr'esentation
            if isinstance(newval, basestring):
                newval = repr(newval)

            setexpr = "%s=%s" % (expression, newval)
            shared.log.debug("trying to execute:\n %s" % (setexpr))

            try:
                exec(setexpr, {}, self.stack)
            except Exception as ex:
                # write a log message, but fail safely by setting the value to ""
                shared.log.error("Variable assignment is not valid.\n%s" % (str(ex)))


    def get(self, expression):
        """evaluates an expression to retrieve data from the stack"""
        if expression:
            expression = expression.strip()
            shared.log.debug("expression is:\n %s" % (expression))
            # shared.log.debug("obj_data is:\n %s" % (self.stack))
            # NOTE: eval is dangerous!
            # so, we only allow it to run against our stack collection
            # and a very strict environment
            try:
                result = eval(expression, EVAL_ENVIRONMENT, self.stack)

                # here's a helper feature
                # IF the result is a list, AND the list has one value, AND the expression is a flat name (no fancy stuff),
                # THEN, we'll return the first item in the list

                # (this regex will only match a 'flat' variable name
                if re.match("^\w+$", expression) and isinstance(result, list):
                    return result[0]
                else:
                    return result
            except Exception as ex:
                # write a log message, but fail safely by setting the value to ""
                shared.log.error("Variable expression %s is not valid.\n%s" % (expression, str(ex)))
                return ""
