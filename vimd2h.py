#!/usr/bin/env python
#-*- coding: utf-8 -*-

# converts vim documentation to html

# Based on https://github.com/c4rlo/vimhelp/blob/b0cab7cbac937cdda156efce0fa4d1b1d4b30ff6/vimh2h.py
# by Carlo Teubner <(first name) dot (last name) at gmail dot com>.

import re
from itertools import chain

try:
    import urllib.parse as urllib
except:
    import urllib

RE_TAGLINE = re.compile(r'(\S+)\s+(\S+)')
RE_LINE1_HELP = re.compile(r'^\*\S+\*\s.*')

# grab an ASCII table and carefully note what the embedded X-Y ranges exclude
PAT_WORDCHAR = '[!#-)+-_a-{}~\xC0-\xFF]'

PAT_HEADER   = r'(^.*~$)'
PAT_GRAPHIC  = r'(^.* `$)'
PAT_PIPEWORD = r'(?<!\\)\|([#-)!+-~]+)\|'
PAT_STARWORD = r'\*([#-)!+-~]+)\*(?:(?=\s)|$)'
PAT_COMMAND  = r'`([^`]+)`'
PAT_OPTWORD  = r"('(?:[a-z]{2,}|t_..)')"
PAT_CTRL     = r'(CTRL-(?:W_)?(?:[\w\[\]^+-<>=@]|<[A-Za-z]+?>)?)'
PAT_SPECIAL  = r'(<.*?>|\{.*?}|' \
               r'\[(?:range|line|count|offset|\+?cmd|[-+]?num|\+\+opt|' \
               r'arg|arguments|ident|addr|group)]|' \
               r'(?<=\s)\[[-a-z^A-Z0-9_]{2,}])'
PAT_VIM_REF  = r'(Vim version [0-9.a-z]+|VIM REFERENCE.*)'
PAT_NOTE     = r'((?<!' + PAT_WORDCHAR + r')(?:note|NOTE|Notes?):?' \
                 r'(?!' + PAT_WORDCHAR + r'))'
PAT_URL      = r'((?:https?|ftp)://[^\'"<> \t]+[a-zA-Z0-9/])'
PAT_WORD     = r'((?<!' + PAT_WORDCHAR + r')' + PAT_WORDCHAR + r'+' \
                 r'(?!' + PAT_WORDCHAR + r'))'

RE_LINKWORD = re.compile(
        PAT_OPTWORD  + '|' +
        PAT_CTRL     + '|' +
        PAT_SPECIAL)
RE_TAGWORD = re.compile(
        PAT_HEADER   + '|' +
        PAT_GRAPHIC  + '|' +
        PAT_PIPEWORD + '|' +
        PAT_STARWORD + '|' +
        PAT_COMMAND  + '|' +
        PAT_OPTWORD  + '|' +
        PAT_CTRL     + '|' +
        PAT_SPECIAL  + '|' +
        PAT_VIM_REF  + '|' +
        PAT_NOTE     + '|' +
        PAT_URL      + '|' +
        PAT_WORD)
RE_NEWLINE   = re.compile(r'[\r\n]')
RE_HRULE     = re.compile(r'[-=]{3,}.*[-=]{3,3}$')
RE_EG_START  = re.compile(r'(?:.* )?>$')
RE_EG_END    = re.compile(r'\S')
RE_SECTION   = re.compile(r'[-A-Z .][-A-Z0-9 .()]*(?=\s+\*)')
RE_STARTAG   = re.compile(r'\s\*([^ \t|]+)\*(?:\s|$)')
RE_LOCAL_ADD = re.compile(r'LOCAL ADDITIONS:\s+\*local-additions\*$')

class Link(object):
    __slots__ = 'link_pipe', 'link_plain'

    def __init__(self, link_pipe, link_plain):
        self.link_pipe = link_pipe
        self.link_plain = link_plain

class VimDoc2HTML(object):
    def __init__(self, tags, url_map, version=None):
        self._urls = { }
        self._urlsCI = { }  # lowercased tag -> set of cased versions
        self._urlsUnresolved = set()
        self._version = version
        for line in RE_NEWLINE.split(tags):
            m = RE_TAGLINE.match(line)
            if m:
                tag, filename = m.group(1, 2)

                if filename not in url_map:
                    url_map[filename] = '' # assume current URL
                    print('Unmapped filename: "%s"' % filename)

                self.do_add_tag(url_map[filename], tag)

    def do_add_tag(self, url, tag):
        part1 = '<a href="{url}#{anchor}"'.format(url=url,
                                                  anchor=urllib.quote_plus(tag))
        part2 = '>' + html_escape[tag] + '</a>'
        link_pipe = part1 + ' class="l"' + part2
        classattr = ' class="d"'
        m = RE_LINKWORD.match(tag)
        if m:
            opt, ctrl, special = m.groups()
            if opt is not None: classattr = ' class="o"'
            elif ctrl is not None: classattr = ' class="k"'
            elif special is not None: classattr = ' class="s"'
        link_plain = part1 + classattr + part2
        self._urls[tag] = Link(link_pipe, link_plain)
        lowerTag = tag.lower()
        if lowerTag in self._urlsCI:
            self._urlsCI[lowerTag].add(tag)
        else:
            self._urlsCI[lowerTag] = set((tag,))

    def maplink(self, tag, css_class=None):
        links = self._urls.get(tag)
        if links is not None:
            if css_class == 'l': return links.link_pipe
            else: return links.link_plain
        elif css_class is not None:
            if css_class == 'l':
                if tag not in self._urlsUnresolved:
                    self._urlsUnresolved.add(tag)
                    lowerTag = tag.lower()
                    if lowerTag in self._urlsCI:
                        print('Unresolved reference: |%s|' % tag)
                        for okTag in self._urlsCI[lowerTag]:
                            print('  - tag with different case: |%s|' % okTag)
                    else:
                        print('Unresolved reference: |%s|' % tag)

            return '<span class="' + css_class + '">' + html_escape[tag] + \
                    '</span>'
        else: return html_escape[tag]

    def to_html(self, contents):
        out = [ ]

        inexample = 0
        lineno = 0
        for line in RE_NEWLINE.split(contents):
            lineno += 1
            line = line.rstrip('\r\n')
            line1_help = lineno == 1 and RE_LINE1_HELP.match(line)
            if line1_help:
                out.append('<span class="flh">')
            line_tabs = line
            line = line.expandtabs()
            if RE_HRULE.match(line):
                out.extend(('<span class="h">', line, '</span>\n'))
                continue
            if inexample == 2:
                if RE_EG_END.match(line):
                    inexample = 0
                    if line[0] == '<': line = line[1:]
                else:
                    out.extend(('<span class="e">', html_escape[line],
                               '</span>\n'))
                    continue
            if RE_EG_START.match(line_tabs):
                inexample = 1
                line = line[0:-1]
            if RE_SECTION.match(line_tabs):
                m = RE_SECTION.match(line)
                out.extend((r'<span class="c">', m.group(0), r'</span>'))
                line = line[m.end():]
            lastpos = 0
            for match in RE_TAGWORD.finditer(line):
                pos = match.start()
                if pos > lastpos:
                    out.append(html_escape[line[lastpos:pos]])
                lastpos = match.end()
                header, graphic, pipeword, starword, command, opt, ctrl, \
                        special, vimref, note, url, word = match.groups()
                if pipeword is not None:
                    out.append(self.maplink(pipeword, 'l'))
                elif starword is not None:
                    quoted = urllib.quote_plus(starword)
                    out.extend(('<a name="', quoted, '" href="#', quoted,
                                '" class="t">', html_escape[starword], '</a>'))
                elif command is not None:
                    out.extend(('<span class="e">', html_escape[command],
                                '</span>'))
                elif opt is not None:
                    out.append(self.maplink(opt, 'o'))
                elif ctrl is not None:
                    out.append(self.maplink(ctrl, 'k'))
                elif special is not None:
                    out.append(self.maplink(special, 's'))
                elif vimref is not None:
                    out.extend(('<span class="i">', html_escape[vimref],
                                '</span>'))
                elif note is not None:
                    out.extend(('<span class="n">', html_escape[note],
                                '</span>'))
                elif header is not None:
                    out.extend(('<span class="h">', html_escape[header[:-1]],
                                '</span>'))
                elif graphic is not None:
                    out.append(html_escape[graphic[:-2]])
                elif url is not None:
                    out.extend(('<a class="u" href="', url, '">' +
                                html_escape[url], '</a>'))
                elif word is not None:
                    out.append(self.maplink(word))
            if lastpos < len(line):
                out.append(html_escape[line[lastpos:]])
            if line1_help:
                out.append('</span>')
            out.append('\n')
            if inexample == 1: inexample = 2

        header = []
        return ''.join(chain(header, out))

class HtmlEscCache(dict):
    def __missing__(self, key):
        r = key.replace('&', '&amp;') \
               .replace('<', '&lt;') \
               .replace('>', '&gt;')
        self[key] = r
        return r

html_escape = HtmlEscCache()
