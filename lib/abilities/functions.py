import requests
from requests.auth import HTTPBasicAuth

import shared
import connections

def _validateprops(props, step):
    """
    Given a list of property names, will raise an error if
    one or more do not exist in the step.
    """
    for p in props:
        if p not in step:
            raise Exception("Step [%s] Function [%s] requires property [%s]" % (step["number"], step["function"], p))


def fn_log(step):
    """
    Log expects a 'message' property.
    """
    required = ["message"]
    _validateprops(required, step)
    shared.log.info(step["message"])


def fn_connect(step):
    """
    Requires:

    protocol: ssh, mysql, oracle, sqlserver, http
    host: address/path/url of the target
    """
    required = ["connection", "protocol", "host", "uid"]
    _validateprops(required, step)
    shared.log.info("Attempting to connect to [%s] via [%s]..." % (step["host"], step["protocol"]))

    conn = connections.Connection(step["connection"],
                                  conn_type=step["protocol"],
                                  debug=step.get("debug"),
                                  initial_prompt=step.get("initial_prompt"),
                                  winrm_transport=step.get("winrm_transport"))
    connections.CONNECTIONS[step["connection"]] = conn

    if step["protocol"] == "ssh":

        conn.handle = connections.connect_expect("ssh",
                                            step["host"],
                                            step["uid"],
                                            password=step.get("pwd"),
                                            key=step.get("privatekey"),
                                            default_prompt=conn.initial_prompt)


def fn_shellcommand(step):
    """
    Requires:

    connection: an active connection established by the 'connect' command
    command: the shell command to execute

    Optional:

    timeout: how long to wait
    positive_response: override the default expected prompt response
    negative_response:
    result_variable:
    """
    required = ["connection", "command"]
    _validateprops(required, step)

    conn_name = shared.replace_variables(step["connection"])
    cmd = shared.replace_variables(step["command"])
    timeout = shared.replace_variables(step.get("timeout"))
    pos = shared.replace_variables(step.get("positive_response"))
    neg = shared.replace_variables(step.get("negative_response"))
    result_var = shared.replace_variables(step.get("result_variable"))

    try:
        # get the connection object
        c = connections.CONNECTIONS[conn_name]
    except KeyError:
        msg = "A connection named [%s] has not been established." % (conn_name)
        raise Exception(msg)

    if not pos:
        pos = "PROMPT>"
    if not neg:
        neg = "This is a default response you shouldnt get it 09kjsjkj49"
    if not timeout:
        timeout = shared.DEFAULT_TIMEOUT
    else:
        timeout = int(timeout)

    shared.log.info("Issuing command:\n%s" % (cmd))
    buff = connections.execute_expect(c.handle, cmd, pos, neg, timeout)
    shared.log.info("%s\n%s" % (cmd, buff))

    if buff:
        shared.VARS.set(result_var, buff)

    print shared.VARS.stack
    print "STOPPED HERE!"
    print "IT WORKS, but we gotta now deal with the variable stack."
#     # if 'result variable' is specified, shove the whole buffer into that variable
#     if result_var:
#         self.rt.set(result_var, buff)
#
#     variables = self.get_node_list(step.command, "step_variables/variable", "name", "type", "position",
#         "range_begin", "prefix", "range_end", "suffix", "regex", "xpath")
#     if len(variables):
#         # print variables
#         self.process_buffer(buff, step)


def fn_http(step):
    """
    Makes an HTTP request.

    TODO: auth, verbs, headers, cookies
    """
    required = ["url"]
    _validateprops(required, step)

    url = shared.replace_variables(step["url"])
    verb = shared.replace_variables(step.get("verb"))
    data = shared.replace_variables(step.get("data"))
    result_var = shared.replace_variables(step.get("result_variable"))

    if verb == "POST":
        r = requests.post(
            url=url,
            data=data
        )
    else:
        # the default is GET
        r = requests.get(url)

    # this will raise an error if there is an HTTPError
    # otherwise it'll just pass
    r.raise_for_status()

    # TODO what to do with an xml response??

    # we want to stick this response on the variable stack
    # however we need coaching as to what data type it is.
    # just use the content-type of the response.
    if "application/json" in r.headers['Content-Type']:
        if r.json():
            shared.VARS.set(result_var, r.json())
    else:
        # we assume it was a text response
        if r.text:
            shared.VARS.set(result_var, r.text)

    print shared.VARS.get(result_var)
