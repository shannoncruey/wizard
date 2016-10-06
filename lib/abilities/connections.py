"""
Holds the global dictionary of active connections, as well
as functions for managing them.
"""

import sys
import pexpect
import time

import shared

# a dictionary of all defined active connections (made by the 'connect' function)
CONNECTIONS = {}


# taken directly from the excellent work done by Patrick Dunnigan on Cato
class Connection:
    def __init__(self, conn_name, conn_type=None, debug=False, initial_prompt=None, winrm_transport=None):

        self.conn_name = conn_name
        self.conn_handle = None
        self.conn_type = conn_type
        self.debug = debug
        self.initial_prompt = initial_prompt
        self.winrm_transport = winrm_transport


def connect_expect(type, host, user, password=None, passphrase=None, key=None, default_prompt=None, debug=False):

    at_prompt = False
    timeout = 20
    buffer = ""

    if not default_prompt:
        default_prompt = "~ #|# $|% $|\$ $|> $"

    if not host:
        raise Exception("Connection address is required to establish a connection")
    if not user:
        raise Exception("User id is required to establish a connection")

    expect_list = [
        "No route to host|Network is unreachable|onnection reset by peer|onnection refused|onnection closed by|Read from socket failed|Name or service not known|Connection timed out",
        "Please login as the user .* rather than the user|expired|Old password:|Host key verification failed|Authentication failed|Permission denied|denied|incorrect|Login Failed|This Account is NOT Valid",
        "yes/no",
        "passphrase for key.*:",
        default_prompt,
        "password will expire(.*)assword: ",
        "assword: $|assword:$",
        pexpect.EOF,
        pexpect.TIMEOUT]

    if debug == "1":
        verbose = "-vv"
    else:
        verbose = ""

    if key:
        kf_name = "%s/%s.pem" % (shared.TMPDIR, shared.uuid())
        kf = file(kf_name, "w",)
        kf.write(key)
        kf.close()
        os.chmod(kf_name, 0400)
        shared.log.info("Attempting ssh private key authentication to %s@%s" % (user, host))
        cmd = "ssh %s -i %s -o ForwardAgent=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null %s@%s" % (verbose, kf_name, user, host)
    else:
        shared.log.info("Attempting ssh password authentication to %s@%s" % (user, host))
        cmd = "ssh %s -o ForwardAgent=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null %s@%s" % (verbose, user, host)

    reattempt = True
    attempt = 1
    while reattempt is True:
        c = pexpect.spawn(cmd, timeout=timeout, logfile=sys.stdout)
        buffer = cmd + "\n"

        # TODO - telnet support
        # TODO - regenerate host key if failure

        msg = None
        cpl = c.compile_pattern_list(expect_list)

        sent_password = False
        while not at_prompt:

            index = c.expect_list(cpl)
            try:
                buffer += str(c.before) + str(c.after)
            except:
                buffer += str(c.before)
            if debug == "1":
                shared.log.warning("%s" % str(c))

            if index in [0, 7, 8]:
                msg = ""
                if index == 7:
                    msg = "The connection to %s closed unexpectedly." % (host)
                elif index == 8:
                    if sent_password:
                        msg = "Authenticated but timeout waiting for initial prompt using regular expression \"%s\" on address %s." % (default_prompt, host)
                    else:
                        msg = "Timeout attempting waiting for password prompt on address %s." % (host)
                if attempt != 10:
                    msg = "%s\nssh connection address %s unreachable on attempt %d. %s Sleeping and reattempting" % (buffer, host, attempt, msg)
                    shared.log.info(msg)
                    time.sleep(20)
                    attempt += 1
                    break
                else:
                    msg = "%s\nThe address %s is unreachable, check network or firewall settings %s" % (buffer, host, msg)
            elif index == 1:
                if key:
                    more_msg = "key authentication. Check that the private key matches the server public key or that the user has permission to login to this server using ssh."
                else:
                    more_msg = "password authentication. Check that the password for the user is correct or that the user has permission to login to this server using ssh."
                msg = "%s\nAuthentication failed for address %s, user %s using ssh %s" % (buffer, host, user, more_msg)
            elif index == 2:
                c.sendline("yes")
            elif index == 3:
                if not password:
                    msg = "%s\nA passphrase for the private key requested by the target ssh server %s, but none was provided." % (buffer, host)
                else:
                    c.sendline(passphrase)
            elif index == 4:
                at_prompt = True
                reattempt = False
            elif index == 5:
                shared.log.warning("The password for user %s will expire soon! Continuing ..." % (user))
                c.logfile = None
                if not password:
                    msg = "%s\nA password was requested by the target ssh server %s, but none was provided for the user %s." % (buffer, host, user)
                else:
                    c.sendline(password)
                    sent_password = True
            elif index == 6:
                c.logfile = None
                if not password:
                    msg = "%s\nA password was requested by the target ssh server %s, but none was provided for the user %s." % (buffer, host, user)
                else:
                    c.sendline(password)
                    sent_password = True
                    c.delaybeforesend = 0
            if msg and len(msg):
                if key:
                    remove_pk(kf_name)
                raise Exception(msg)

    if key:
        remove_pk(kf_name)

    c.sendline("unset PROMPT_COMMAND;export PS1='PROMPT>'")
    index = c.expect(["PROMPT>.*PROMPT>$", pexpect.EOF, pexpect.TIMEOUT])
    buffer += str(c.before) + str(c.after)
    if index == 0:
        pass
    elif index == 1:
        msg = "The connection to %s closed unexpectedly." % (host)
        try:
            msg = msg + "\n" + str(c.before) + c.match.group() + str(c.after)
        except:
            pass
        raise Exception(msg)
    elif index == 2:
        msg = "Timeout resetting command prompt."
        try:
            msg = msg + "\n" + str(c.before) + c.match.group() + str(c.after)
        except:
            pass
        raise Exception(msg)
    c.sendline("stty -onlcr;export PS2='';stty -echo;unalias ls")
    index = c.expect(["PROMPT>$", pexpect.EOF, pexpect.TIMEOUT])
    buffer += str(c.before) + str(c.after)
    if index == 0:
        pass
    elif index == 1:
        msg = "The connection to %s closed unexpectedly." % (host)
        try:
            msg = msg + "\n" + str(c.before) + c.match.group() + str(c.after)
        except:
            pass
        raise Exception(msg)
    elif index == 2:
        msg = "Timeout configuring TTY."
        try:
            msg = msg + "\n" + str(c.before) + c.match.group() + str(c.after)
        except:
            pass
        raise Exception(msg)

    shared.log.info(buffer)
    shared.log.info("ssh connected to address [%s] with user [%s] established.\n%s" % (host, user, buffer))

    return c


def remove_pk(kf_name):
    # we successfully logged in, let's get rid of the private key
    try:
        os.remove(kf_name)
    except:
        pass


def disconnect_expect(self, handle):

    try:
        handle.close()
    except:
        pass


def execute_expect(c, cmd, pos="PROMPT>", neg=None, timeout=20):

    expect_list = [pos, pexpect.EOF, pexpect.TIMEOUT]
    if neg:
        expect_list.append(neg)

    c.timeout = timeout
    c.sendline(cmd)
    index = c.expect(expect_list)
    if index == 0:
        pass
    elif index == 1:
        msg = "The connection to closed unexpectedly."
        try:
            msg = msg + "\n" + str(c.before) + c.match.group() + str(c.after)
        except:
            pass
        raise Exception(msg)
    elif index == 2:
        msg = "%s\nCommand timed out after %s seconds." % (cmd, timeout)
        raise Exception(msg)
    elif index == 3:
        msg = "Negative response %s received ..." % (neg)
        try:
            msg = cmd + "\n" + msg + "\n" + str(c.before) + c.match.group() + str(c.after)
        except:
            pass
        raise Exception(msg)

    # remove any trailing newline
    return str(c.before).rstrip("\n")


