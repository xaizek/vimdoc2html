### Overview ###

This is a script to convert Vim documentation file into HTML.

### Dependencies ###

* Perl
* Python

### Description ###

The basic usage is:

```bash
./vimdoc2html.py plugin.txt
```

or if the script is somewhere in the `$PATH`:

```bash
vimdoc2html.py plugin.txt
```

#### Operation ####

As a first step, `helpztags` script is used to generate `tags` file similar to
what Vim's `:helptags` command produces.  This is needed to know which
references should be turned into hyperlinks.  Then the tags and documentation
in Vim's format are processed to produce HTML output.

#### Options ####

##### `-m,--map FILE=URL` option

Associates a file path as found in `tags` file with a URL.  This option can be
specified multiple times.  By default base name of the input file is mapped to
an empty string (current URL in a browser).  All other unmapped file names in
the `tags` file are mapped to an empty string and cause printing of a warning
which can be used to adjust invocation.

##### `-o,--output path` option

Specifies name of the output file.  The default behaviour is to derive it from
the name of the input file by appending `.html`.

##### `-r,--raw` flag

Instead of outputting complete standalone HTML page, produce only minimal
output without `<html>`/`<head>`/`<body>`/`<pre>` tags.

##### `-t,--template path` option

Overrides builtin template.  The following sequences will be expanded:
 - `{title}` with the name of the source file
 - `{style}` with the contents of `vimhelp.css`
 - `{html}` with documentation formatted as HTML

Default template is trivial:
```html
<html>
    <head>
        <title>{title}</title>
        <style>{style}</style>
    </head>
    <body>
        <pre>
        {html}
        </pre>
    </body>
</html>
```

### Credit ###

HTML formatting is performed via modified version of
[vimh2h.py](https://github.com/c4rlo/vimhelp/blob/master/vimh2h.py) by Carlo
Teubner <(first name) dot (last name) at gmail dot com>.  This one is simplified
to remove unused here code and a bit improved to add anchors to each tag
definition.  CSS style is from
[there too](https://github.com/c4rlo/vimhelp/blob/master/static/vimhelp.css).

Tags are extracted via `helpztags` tool written by Jakub Turski
<yacoob@chruptak.plukwa.net> and Artur R. Czechowski <arturcz@hell.pl>.  It's
supplied alongside for convenience and to provide a couple of changes, see
there.
