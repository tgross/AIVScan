#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2012 Team Pwn Stars

import os, sys
import logging
from django.conf.settings import settings

class NmapScriptParser:

    def parse_output(self, script_id, script_output, host_id):
        '''
        Returns a Vulns object if there is a match on the script output.
        taken from pGetTextVulnRef sproc
        CREATE PROCEDURE pGetTextVulnRef_byScriptID (IN v_scriptID VARCHAR(100))
        BEGIN
        SELECT tvid, ScriptID, MatchString, VulnString, FixString FROM TextVulns
        WHERE ScriptID = v_scriptID;
        END
        '''
        try:
            vulnerabilities = Textvulns.filter(scriptid=script_id)
            if vulnerabilities:
                for vulnerability in vulnerabilities:
                    if vulnerability.matchstring in script_output:
                        logging.debug('vuln id: {0}'.format(vulnId))
                        vuln = Vulns()
                        vuln.hid = host_id
                        vuln.tvid = vulnerability.id
                        vuln.save()
                        return vuln
            return None             # either no listing or no matchstring
        except Exception as ex:
            logging.error('Error parsing script output\n{0}'.format(ex))
            return None


if __name__ == '__main__':

    script_id = 'smb-check-vulns'
    script_output = 'bla bla MS08-067: VULNERABLE bla bla'

    sp = cScriptParser()
    sp.parseOutput(script_id, script_output)

