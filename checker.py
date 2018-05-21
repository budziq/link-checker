#!/usr/bin/env python3
"""
Simple script to check directory full of html files for broken links
"""

import os
import sys
from urllib.parse import urlsplit, urldefrag, urljoin
import requests
from bs4 import BeautifulSoup
import click

def info(msg):
    """Show green info message"""
    click.echo(click.style(msg, bold=True, fg="green"))

def warn(msg):
    """Show yellow warning message"""
    click.echo(click.style(msg, bold=True, fg="yellow"))

def error(msg):
    """Show red error message"""
    click.echo(click.style(msg, bold=True, fg="red"))

def html_files_for_dir(pth):
    """gets a list of html files in directory"""
    for root, _dirs, files in os.walk(pth):
        for fname in files:
            fpath = os.path.join(root, fname)
            fext = os.path.splitext(fpath)[1].lower()
            if fext == ".html" or fext == ".htm":
                yield fpath

def rebase_link(lnk, baseurl, referrer_path):
    """Change link base using <base href=""> path"""
    parsed = urlsplit(lnk)
    if parsed.scheme:
        return urljoin(baseurl, lnk)

    return os.path.realpath(os.path.join(os.path.dirname(referrer_path), baseurl, lnk))


def links_in_soup(soup, referrer):
    """Find links to all files referenced by the HTML data."""
    baseurl = ""
    base = soup.find("base")
    if base and "href" in base.attrs:
        baseurl = base.attrs["href"]

    ret = [ln.attrs["href"] for ln in soup.findAll(["a", "link"]) if "href" in  ln.attrs]
    ret += [ln.attrs["src"] for ln in soup.findAll(["img", "script"]) if "src" in  ln.attrs]
    return {rebase_link(lnk, baseurl, referrer) for lnk in ret}


def anchor_in_soup(soup, anchor_name):
    """Find if a given anchor id is present in a HTML data"""
    return bool(soup.find("", {"id" : anchor_name})) or bool(soup.find("", {"name" : anchor_name}))

def test_http_head(link):
    """Check if given remote resource is currently reachable via HTTP HEAD"""
    try:
        return requests.head(link,
                             headers={"Accept": "text/html"},
                             allow_redirects=True, timeout=1).ok
    except:
        # we explictly want to catch all exceptions
        return False

class LinkChecker:
    """Class performing link checking. Basically it is a cache
    retaining known link state and already parsed HTML data."""

    def __init__(self):
        self.soup_mapping = {}
        self.seen_links = {}
        self.link_cnt = 0
        self.fail_cnt = 0
        self.fail_map = {}

    def test_link(self, link):
        """Check single link. Either local or remote"""
        base_link, fragment = urldefrag(link)
        if link in self.seen_links:
            return self.seen_links[link]

        if base_link in self.seen_links and not self.seen_links[base_link]:
            return False

        scheme = urlsplit(link)[0]
        ret = False

        if scheme:
            if fragment:
                # test with HTTP GET and read to soup
                ret = self._test_http_fragment(base_link, fragment)
            else:
                ret = test_http_head(link)
        else:
            if fragment:
                # read file to soup
                ret = self._test_file_fragment(base_link, fragment)
            else:
                # just stat file
                ret = os.path.exists(link)

        self.seen_links[link] = ret
        return ret

    def test_file(self, fname):
        """Find all links in a single HTML file and test test if these are reachable"""
        info("Testing: {}".format(fname))

        if fname in self.soup_mapping:
            soup = self.soup_mapping[fname]
        else:
            with open(fname) as fdata:
                soup = BeautifulSoup(fdata, "html.parser")
                self.soup_mapping[fname] = soup

        fails = []
        with click.progressbar(links_in_soup(soup, fname),
                               fill_char=click.style(u'█', fg='yellow')
                               ) as progress:
            for lnk in progress:
                self.link_cnt += 1
                if not self.test_link(lnk):
                    self.fail_cnt += 1
                    fails.append(lnk)

        if fails:
            for lnk in fails:
                error("'{}' Broken!".format(lnk))
            self.fail_map[fname] = fails

    def test_dir(self, pth):
        """Find all HTML files in directory and perform tests on them"""
        for fname in html_files_for_dir(pth):
            self.test_file(fname)


    def _test_http_fragment(self, link, fragment):
        if link in self.soup_mapping:
            soup = self.soup_mapping[link]
        else:
            try:
                response = requests.get(link, headers={"Accept": "text/html"}, timeout=1)
                if not response.ok:
                    return False
                else:
                    soup = BeautifulSoup(response.content, "html.parser")
                    self.soup_mapping[link] = soup
            except:
                # we explictly want to catch all exceptions
                return False
        return anchor_in_soup(soup, fragment)

    def _test_file_fragment(self, fname, fragment):
        if fname in self.soup_mapping:
            soup = self.soup_mapping[fname]
        else:
            if not os.path.exists(fname):
                return False

            with open(fname) as fdata:
                soup = BeautifulSoup(fdata, "html.parser")
                self.soup_mapping[fname] = soup

        return anchor_in_soup(soup, fragment)

    def get_stats(self):
        """return tuple with post test statistics"""
        return (self.link_cnt, self.fail_cnt, len(self.seen_links))


@click.command()
@click.argument("PATH", default=os.path.curdir)
def check(path):
    """Test a directory of HTML files for broken links"""
    checker = LinkChecker()
    checker.test_dir(path)
    info("\n\nSummary: seen:{} failed:{} unique:{}".format(*checker.get_stats()))
    if checker.fail_cnt:
        for (fname, fails) in checker.fail_map.items():
            warn("* '{}'".format(fname))

            for lnk in fails:
                error("\t{}".format(lnk))
        sys.exit(1)

if __name__ == "__main__":
    check()


def test_rebase_link():
    """tests for rebase_link function"""
    urls = [
        '_FontAwesome/css/font-awesome.css',
        'about.html',
        'algorithms.html',
        'algorithms/randomness.html',
        'ayu-highlight.css',
        'book.css',
        'cli.html',
        'cli/arguments.html',
        'compression.html',
        'compression/tar.html',
        'concurrency.html',
        'concurrency/parallel.html',
        'concurrency/threads.html',
        'cryptography.html',
        'cryptography/encryption.html',
        'cryptography/hashing.html',
        'data_structures.html',
        'data_structures/constant.html',
        'data_structures/custom.html',
        'datetime.html',
        'datetime/duration.html',
        'datetime/parse.html',
        'development_tools.html',
        'development_tools/build_tools.html',
        'development_tools/debugging.html',
        'development_tools/debugging/config_log.html',
        'development_tools/debugging/log.html',
        'development_tools/errors.html',
        'development_tools/versioning.html',
        'encoding.html',
        'encoding/complex.html',
        'encoding/csv.html',
        'encoding/strings.html',
        'favicon.png',
        'file.html',
        'file/dir.html',
        'file/read-write.html',
        'hardware.html',
        'hardware/processor.html',
        'highlight.css',
        'https://crates.io/categories/text-processing',
        'https://doc.rust-lang.org/regex/regex/struct.Regex.html#method.captures_iter',
        'https://doc.rust-lang.org/regex/regex/struct.RegexSet.html',
        'https://doc.rust-lang.org/regex/regex/struct.RegexSetBuilder.html',
        'https://docs.rs/lazy_static/',
        'https://docs.rs/regex/',
        'https://docs.rs/regex/*/regex/struct.Regex.html#method.replace_all',
        'https://docs.rs/regex/*/regex/struct.Regex.html#replacement-string-syntax',
        'https://fonts.googleapis.com/css?family=Open+Sans:300italic,400italic,600italic,700italic,800italic,400,300,600,700,800',
        'https://fonts.googleapis.com/css?family=Source+Code+Pro:500',
        'https://github.com/twitter/twitter-text/blob/c9fc09782efe59af4ee82855768cfaf36273e170/java/src/com/twitter/Regex.java#L255',
        'intro.html',
        'net.html',
        'net/server.html',
        'os.html',
        'os/external.html',
        'print.html',
        'text.html',
        'text/regex.html#extract-a-list-of-unique-hashtags-from-a-text',
        'text/regex.html#extract-phone-numbers-from-text',
        'text/regex.html#filter-a-log-file-by-matching-multiple-regular-expressions',
        'text/regex.html#regular-expressions',
        'text/regex.html#replace-all-occurrences-of-one-text-pattern-with-another-pattern',
        'text/regex.html#verify-and-extract-login-from-an-email-address',
        'text/regex.html',
        'theme/custom.css',
        'tomorrow-night.css',
        'web.html',
        'web/clients.html',
        'web/clients/apis.html',
        'web/clients/download.html',
        'web/clients/requests.html',
        'web/mime.html',
        'web/scraping.html',
        'web/url.html']
    base = "../"
    referrer = "./tst/www.yetanother.site/rust-cookbook/hardware/processor.html"

    res_urls = [
        './tst/www.yetanother.site/rust-cookbook/_FontAwesome/css/font-awesome.css',
        './tst/www.yetanother.site/rust-cookbook/about.html',
        './tst/www.yetanother.site/rust-cookbook/algorithms.html',
        './tst/www.yetanother.site/rust-cookbook/algorithms/randomness.html',
        './tst/www.yetanother.site/rust-cookbook/ayu-highlight.css',
        './tst/www.yetanother.site/rust-cookbook/book.css',
        './tst/www.yetanother.site/rust-cookbook/cli.html',
        './tst/www.yetanother.site/rust-cookbook/cli/arguments.html',
        './tst/www.yetanother.site/rust-cookbook/compression.html',
        './tst/www.yetanother.site/rust-cookbook/compression/tar.html',
        './tst/www.yetanother.site/rust-cookbook/concurrency.html',
        './tst/www.yetanother.site/rust-cookbook/concurrency/parallel.html',
        './tst/www.yetanother.site/rust-cookbook/concurrency/threads.html',
        './tst/www.yetanother.site/rust-cookbook/cryptography.html',
        './tst/www.yetanother.site/rust-cookbook/cryptography/encryption.html',
        './tst/www.yetanother.site/rust-cookbook/cryptography/hashing.html',
        './tst/www.yetanother.site/rust-cookbook/data_structures.html',
        './tst/www.yetanother.site/rust-cookbook/data_structures/constant.html',
        './tst/www.yetanother.site/rust-cookbook/data_structures/custom.html',
        './tst/www.yetanother.site/rust-cookbook/datetime.html',
        './tst/www.yetanother.site/rust-cookbook/datetime/duration.html',
        './tst/www.yetanother.site/rust-cookbook/datetime/parse.html',
        './tst/www.yetanother.site/rust-cookbook/development_tools.html',
        './tst/www.yetanother.site/rust-cookbook/development_tools/build_tools.html',
        './tst/www.yetanother.site/rust-cookbook/development_tools/debugging.html',
        './tst/www.yetanother.site/rust-cookbook/development_tools/debugging/config_log.html',
        './tst/www.yetanother.site/rust-cookbook/development_tools/debugging/log.html',
        './tst/www.yetanother.site/rust-cookbook/development_tools/errors.html',
        './tst/www.yetanother.site/rust-cookbook/development_tools/versioning.html',
        './tst/www.yetanother.site/rust-cookbook/encoding.html',
        './tst/www.yetanother.site/rust-cookbook/encoding/complex.html',
        './tst/www.yetanother.site/rust-cookbook/encoding/csv.html',
        './tst/www.yetanother.site/rust-cookbook/encoding/strings.html',
        './tst/www.yetanother.site/rust-cookbook/favicon.png',
        './tst/www.yetanother.site/rust-cookbook/file.html',
        './tst/www.yetanother.site/rust-cookbook/file/dir.html',
        './tst/www.yetanother.site/rust-cookbook/file/read-write.html',
        './tst/www.yetanother.site/rust-cookbook/hardware.html',
        './tst/www.yetanother.site/rust-cookbook/hardware/processor.html',
        './tst/www.yetanother.site/rust-cookbook/highlight.css',
        'https://crates.io/categories/text-processing',
        'https://doc.rust-lang.org/regex/regex/struct.Regex.html#method.captures_iter',
        'https://doc.rust-lang.org/regex/regex/struct.RegexSet.html',
        'https://doc.rust-lang.org/regex/regex/struct.RegexSetBuilder.html',
        'https://docs.rs/lazy_static/',
        'https://docs.rs/regex/',
        'https://docs.rs/regex/*/regex/struct.Regex.html#method.replace_all',
        'https://docs.rs/regex/*/regex/struct.Regex.html#replacement-string-syntax',
        'https://fonts.googleapis.com/css?family=Open+Sans:300italic,400italic,600italic,700italic,800italic,400,300,600,700,800',
        'https://fonts.googleapis.com/css?family=Source+Code+Pro:500',
        'https://github.com/twitter/twitter-text/blob/c9fc09782efe59af4ee82855768cfaf36273e170/java/src/com/twitter/Regex.java#L255',
        './tst/www.yetanother.site/rust-cookbook/intro.html',
        './tst/www.yetanother.site/rust-cookbook/net.html',
        './tst/www.yetanother.site/rust-cookbook/net/server.html',
        './tst/www.yetanother.site/rust-cookbook/os.html',
        './tst/www.yetanother.site/rust-cookbook/os/external.html',
        './tst/www.yetanother.site/rust-cookbook/print.html',
        './tst/www.yetanother.site/rust-cookbook/text.html',
        './tst/www.yetanother.site/rust-cookbook/text/regex.html#extract-a-list-of-unique-hashtags-from-a-text',
        './tst/www.yetanother.site/rust-cookbook/text/regex.html#extract-phone-numbers-from-text',
        './tst/www.yetanother.site/rust-cookbook/text/regex.html#filter-a-log-file-by-matching-multiple-regular-expressions',
        './tst/www.yetanother.site/rust-cookbook/text/regex.html#regular-expressions',
        './tst/www.yetanother.site/rust-cookbook/text/regex.html#replace-all-occurrences-of-one-text-pattern-with-another-pattern',
        './tst/www.yetanother.site/rust-cookbook/text/regex.html#verify-and-extract-login-from-an-email-address',
        './tst/www.yetanother.site/rust-cookbook/text/regex.html',
        './tst/www.yetanother.site/rust-cookbook/theme/custom.css',
        './tst/www.yetanother.site/rust-cookbook/tomorrow-night.css',
        './tst/www.yetanother.site/rust-cookbook/web.html',
        './tst/www.yetanother.site/rust-cookbook/web/clients.html',
        './tst/www.yetanother.site/rust-cookbook/web/clients/apis.html',
        './tst/www.yetanother.site/rust-cookbook/web/clients/download.html',
        './tst/www.yetanother.site/rust-cookbook/web/clients/requests.html',
        './tst/www.yetanother.site/rust-cookbook/web/mime.html',
        './tst/www.yetanother.site/rust-cookbook/web/scraping.html',
        './tst/www.yetanother.site/rust-cookbook/web/url.html']
    assert len(urls) == len(res_urls)

    base_ref = [
        ("../", "./tst/www.yetanother.site/rust-cookbook/hardware/processor.html"),
        ("", "./tst/www.yetanother.site/rust-cookbook/processor.html"),
        ("./", "./tst/www.yetanother.site/rust-cookbook/processor.html"),
        ("../../", "./tst/www.yetanother.site/rust-cookbook/hardware/proc/essor.html"),
        ("../", "./tst/www.yetanother.site/rust-cookbook/hardware/")]

    for (base, referrer) in base_ref:
        for (left, right) in zip(urls, res_urls):
            if not right.startswith("http"):
                right = os.path.realpath(right)
            assert rebase_link(left, base, referrer) == right
