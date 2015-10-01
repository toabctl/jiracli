#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Thomas Bechtold <thomasbechtold@jpberlin.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function

import os
import os.path
import sys
import argparse
import ConfigParser
import logging
import getpass
import datetime
import subprocess
import tabulate
from collections import OrderedDict
from termcolor import colored as colorfunc
from jira import JIRA
import tempfile

# log object
log = logging.getLogger('jiracli')
# path to the user configuration file
user_config_path = os.path.expanduser('~/.jiracli.ini')

# Force utf8 encoding for output if not defined (useful for piping)
if sys.stdout.encoding is None:
    import codecs
    writer = codecs.getwriter("utf-8")
    sys.stdout = writer(sys.stdout)


def setup_logging(logger, debug):
    sh = logging.StreamHandler()
    if debug:
        logger.setLevel(logging.DEBUG)
        sh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    sh.setFormatter(formatter)
    logger.addHandler(sh)


def file_get_text(fname):
    # get text from an a provided filename
    tf = open(fname, 'r')
    tf.seek(0)
    return "\n".join([line for line in tf.read().split('\n')
                      if not line.startswith("--")])


def editor_get_text(text_template):
    """get text from an editor via a tempfile"""
    tf = tempfile.NamedTemporaryFile()
    tf.write("-- lines starting with '--' will be ignored\n")
    tf.write(text_template)
    tf.flush()
    editor = os.environ.setdefault("EDITOR", "vim")
    os.system("%s %s" % (editor, tf.name))
    tf.seek(0)
    return "\n".join([line for line in tf.read().split('\n')
                      if not line.startswith("--")])


def config_credentials_get():
    # get username, password and url
    user = raw_input("username:")
    password = getpass.getpass()
    url = raw_input("url:")
    return user, password, url


def sprint(jira_obj, project):
    issues = jira_obj.search_issues(
        'project = "%s" AND sprint IN openSprints()' % project)
    width, height = [
        int(v) for v in
        subprocess.check_output(["stty", "size"]).strip().split()]

    content = []
    sizes = [0, 0, 0]
    for issue in issues:
        content.append([issue.key,
                        issue.fields.status.name,
                        issue.fields.assignee.name if issue.fields.assignee
                        else "Nobody",
                        issue.fields.summary])
        for i in range(3):
            if sizes[i] < len(content[-1][i]):
                sizes[i] = len(content[-1][i])
    summary_width = width - sum(sizes) - 7
    for line in content:
        line[-1] = line[-1][:summary_width]

    print(tabulate.tabulate(content,
                            headers=['issue', 'status',
                                     'assignee', 'summary']))


def config_get():
    conf = ConfigParser.SafeConfigParser()
    conf.read([user_config_path])
    section_name = "defaults"
    if not conf.has_section(section_name):
        user, password, url = config_credentials_get()
        conf.add_section(section_name)
        conf.set(section_name, "user", user)
        conf.set(section_name, "password", password)
        conf.set(section_name, "url", url)
        with open(user_config_path, 'w') as f:
            conf.write(f)
            log.info("username and password written to %s", user_config_path)
    else:
        log.debug("%s section already available in %s", section_name,
                  user_config_path)
    return dict(conf.items(section_name))


def jira_obj_get(conf):
    options = {
        'server': conf['url'],
    }
    return JIRA(options, basic_auth=(conf['user'], conf['password']))


def dtstr2dt(dtstr):
    """nicer datetime string
    jira delivers something like '2013-11-07T16:13:24.000+0100'"""
    # TODO: maybe %c is not the best formatter.
    # Output depends on current locale
    return datetime.datetime.strptime(dtstr[:-9],
                                      "%Y-%m-%dT%H:%M:%S").strftime("%c")


def issue_status_color(status):
    """get color for given issue status"""
    if status.lower() == 'closed':
        return 'green'
    elif status.lower() == 'open':
        return 'red'
    elif status.lower() == 'in progress':
        return 'yellow'
    else:
        return 'blue'


def issue_header(issue):
    """get a single line string for an issue"""
    if hasattr(issue.fields, "priority"):
        priority = "%s" % issue.fields.priority.name
    else:
        priority = "n/a"

    return "%s (%s)" % (colorfunc("%s, %s: %s" % (issue.key,
                                                  issue.fields.issuetype.name,
                                                  issue.fields.summary),
                                  None, attrs=['bold', 'underline']),
                        colorfunc("%s, %s" % (issue.fields.status.name,
                                              priority),
                                  issue_status_color(issue.fields.status.name),
                                  attrs=['bold']))


def issue_format(jira_obj, issue, show_desc=False, show_comments=False,
                 show_trans=False):
    """return a dict with fields which describe the issue"""
    fields = OrderedDict()
    if hasattr(issue.fields, "parent"):
        fields['parent'] = "%s" % (issue.fields.parent.key)
    if show_desc:
        fields['description'] = "\n%s" % (issue.fields.description)
    fields['created'] = "%s, by %s" % (dtstr2dt(issue.fields.created),
                                       issue.fields.reporter.name)
    if hasattr(issue.fields.assignee, 'name'):
        fields['assignee'] = issue.fields.assignee.name
    fields['updated'] = dtstr2dt(issue.fields.updated)
    if hasattr(issue.fields, 'versions') and len(issue.fields.fixVersions) > 0:
        fields['versions'] = ", ".join(map(lambda x: x.name,
                                           issue.fields.fixVersions))
    if hasattr(issue.fields, 'components') and \
       len(issue.fields.components) > 0:
        fields['components'] = ", ".join(map(lambda x: x.name,
                                             issue.fields.components))
    if hasattr(issue.fields, 'labels') and len(issue.fields.labels) > 0:
        fields['labels'] = ", ".join(map(lambda x: x, issue.fields.labels))
    if hasattr(issue.fields, 'attachment') and \
       len(issue.fields.attachment) > 0:
        fields['attachment'] = ", ".join(map(lambda x: x.filename,
                                             issue.fields.attachment))
    if hasattr(issue.fields, 'issuelinks') and \
       len(issue.fields.issuelinks) > 0:
        link_list = list()
        # inward issue: the issue to link from
        # outward issue: the issue to link to
        for link in issue.fields.issuelinks:
            if 'outwardIssue' in link.raw:
                link_list.append(link.raw['outwardIssue'])
            elif 'inwardIssue' in link.raw:
                link_list.append(link.raw['inwardIssue'])
        fields['issuelinks'] = ", ".join(map(lambda x: x['key'], link_list))
    if show_comments:
        if hasattr(issue.fields, 'comment'):
            fields['comments'] = "%s\n%s" % (
                len(issue.fields.comment.comments),
                "\n\n".join(map(lambda x: "%s\n%s" % (colorfunc("%s, %s" % (dtstr2dt(x.updated), x.updateAuthor.name), None, attrs=['reverse']), x.body), issue.fields.comment.comments)))  # noqa
        else:
            fields['comments'] = "0"
    else:
        # show only the number of comments
        if hasattr(issue.fields, 'comment') and \
           len(issue.fields.comment.comments) > 0:
            fields['comments'] = "%s" % (len(issue.fields.comment.comments))

    if show_trans:
        transitions = jira_obj.transitions(issue)
        fields['trans'] = ", ".join(map(
            lambda x: x['name'] + "(" + x['id'] + ")", transitions))

    # print(dir(issue.fields))
    # add empty strings if field not available
    for k, v in fields.items():
        if not v:
            fields[k] = ""
    return fields


def issue_list_print(jira_obj, issue_list, show_desc, show_comments,
                     show_trans, oneline):
    """print a list of issues"""
    # disable color if oneline is used
    if oneline:
        global colorfunc
        colorfunc = lambda *a, **k: a[0]

    for issue in issue_list:
        # issue header
        print(issue_header(issue))
        if oneline:
            continue
        # issue description
        desc_fields = issue_format(jira_obj, issue,
                                   show_desc=show_desc,
                                   show_comments=show_comments,
                                   show_trans=show_trans)
        print("\n".join(" : ".join((k.ljust(20), v))
                        for k, v in desc_fields.items()) + "\n")


def issue_search_result_print(jira_obj, args, searchstring_list):
    """print issues for the given search string(s)"""
    for searchstr in searchstring_list:
        issues = jira_obj.search_issues(searchstr)
        # FIXME: debug problem why comments are not available
        # if I use jira_obj.search_issues()
        # get issues again.
        issues = [jira_obj.issue(i.key) for i in issues]
        issue_list_print(jira_obj, issues, args['issue_desc'],
                         args['issue_comments'], args['issue_trans'],
                         args['issue_oneline'])


def filter_list_print(filter_list):
    """print a list of filters"""
    for f in filter_list:
        # header
        print("%s" % (colorfunc("%s, %s" % (f.id,
                                            f.name),
                                None, attrs=['bold', 'underline'])))
        # fields to show for the filter
        fields = OrderedDict()
        fields['Url'] = f.viewUrl
        fields['description'] = getattr(f, 'description', '')
        fields['owner'] = f.owner.name
        fields['jql'] = f.jql
        # add empty strings if field not available
        for k, v in fields.items():
            if not v:
                fields[k] = ""

        print("\n".join(" : ".join((k.ljust(20), v))
                        for k, v in fields.items()) + "\n")


def parse_args():
    """parse command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true',
                        help='print debug information (default: %(default)s)')
    parser.add_argument("--issue-type-list", action='store_true',
                        help='list available issue types')
    parser.add_argument("--issue-link-types-list", action='store_true',
                        help='list available issue link types')
    parser.add_argument("--project-list", action='store_true',
                        help='list available projects')
    parser.add_argument("--project-list-components", nargs=1,
                        metavar='project-key',
                        help='list available project components for the given'
                        'roject-key')
    parser.add_argument("-m", "--message", nargs=1, metavar='message',
                        help='a message. can be ie used together with '
                        '--issue-add-comment')
    parser.add_argument("-mf", "--message-file", nargs=1,
                        metavar='message_file',
                        help='a message. can be supplied via a file  with '
                        '--issue-comment-add')
    parser.add_argument("--filter-list-fav", action='store_true',
                        help='list favourite filters')
    parser.add_argument("--no-color", action='store_true',
                        help='disable colorful output (default: %(default)s)')
    group_issue = parser.add_argument_group('issue')
    # create
    group_issue.add_argument('-c', '--issue-create', nargs=5,
                             metavar=('project-key', 'issue-type',
                                      'summary', 'labels', 'components'),
                             help='create a new issue. "labels" can be a '
                             'single label or a comma seperated list of '
                             'labels. "components" can be a comma seperated '
                             'list of components.')

    group_issue.add_argument('--issues-create', nargs=4,
                             metavar=('project-key', 'parent-issue-type',
                                      'child-issue-type', 'file'),
                             help='Read Issue Summaries from a file. '
                             'Each line is a summary.')

    # show and search
    group_issue.add_argument('-i', '--issue', nargs='+', metavar='issue',
                             help='issue(s) to show')

    group_issue.add_argument('--issue-search', nargs='+',
                             metavar='searchstring',
                             help='search for issues. searchstring is ie: '
                             'assignee=CurrentUser() and status!="Closed"')
    group_issue.add_argument('--issue-search-by-filter', nargs='+',
                             metavar='filter-id',
                             help='search for issues by filter-id.')
    group_issue.add_argument('--issue-desc', action='store_true',
                             help='show issue description '
                             '(default: %(default)s)')
    group_issue.add_argument('--issue-comments', action='store_true',
                             help='show issue comment(s) '
                             '(default: %(default)s)')
    group_issue.add_argument('--issue-trans', action='store_true',
                             help='show possible issue transition(s)'
                             '(default: %(default)s)')
    group_issue.add_argument('--issue-oneline', action='store_true',
                             help='show single line per issue '
                             '(default: %(default)s)')

    # show open sprint for project
    group_issue.add_argument('--sprint', nargs=1, metavar='project',
                             help='show open sprint for project.')

    # comments
    group_issue.add_argument('--issue-comment-add', nargs=1,
                             metavar='issue-key',
                             help='add a comment to given issue.')

    # labels
    group_issue.add_argument("--issue-label-add", nargs=2,
                             metavar=('issue', 'label'),
                             help='Add a label to the given issue')
    group_issue.add_argument("--issue-label-remove", nargs=2,
                             metavar=('issue', 'label'),
                             help='Remove a label from the given issue')

    # components
    group_issue.add_argument("--issue-component-add", nargs=2,
                             metavar=('issue', 'component'),
                             help='Add a component to the given issue')
    group_issue.add_argument("--issue-component-remove", nargs=2,
                             metavar=('issue', 'component'),
                             help='Remove a component from the given issue')
    # transitions
    group_issue.add_argument("--issue-trans-open", nargs='+', metavar='issue',
                             help='Move issue(s) to Open state')
    group_issue.add_argument("--issue-trans-start", nargs='+', metavar='issue',
                             help='Move issue(s) to Start Progress state')
    group_issue.add_argument("--issue-trans-resolve", nargs='+',
                             metavar='issue',
                             help='Move issue(s) to Resolve Issue state')
    group_issue.add_argument("--issue-trans-close", nargs='+', metavar='issue',
                             help='Move issue(s) to Closed state')
    # watchers
    group_issue.add_argument("--issue-watch-add", nargs='+', metavar='issue',
                             help='Add watch to the given issue(s)')
    group_issue.add_argument("--issue-watch-remove", nargs='+',
                             metavar='issue',
                             help='Remove watch from the given issue(s)')
    # fix versions
    group_issue.add_argument("--issue-fix-version-add", nargs='+',
                             metavar='issue',
                             help='Add fix version to the given issue(s)')
    group_issue.add_argument("--issue-fix-version-remove", nargs='+',
                             metavar='issue',
                             help='Remove fix version from the given issue(s)')

    group_issue.add_argument("--issue-parent",
                             help='Parent Issue Key of the Subtask. '
                             'Required for Subtasks.')
    return vars(parser.parse_args())


def main():
    args = parse_args()
    setup_logging(log, args['debug'])
    conf = config_get()
    jira_obj = jira_obj_get(conf)

    # use colorful output?
    if args['no_color']:
        global colorfunc
        colorfunc = lambda *a, **k: str(a[0])

    # print issue link types
    if args['issue_link_types_list']:
        # print("%s%s%s" % ("name".ljust(30), "inward".ljust(25),
        # "outward".ljust(25)))
        for i in jira_obj.issue_link_types():
            print("%s%s%s" % (i.name.ljust(30),
                              i.inward.ljust(25), i.outward.ljust(25)))
        sys.exit(0)

    # print project list and exit
    if args['project_list']:
        for p in jira_obj.projects():
            print(p.id.ljust(10), p.key.ljust(10), p.name.ljust(30))
        sys.exit(0)

    # print issue types
    if args['issue_type_list']:
        for it in jira_obj.issue_types():
            print(it.id.ljust(10), it.name.ljust(30), it.description.ljust(10))
        sys.exit(0)

    # print project components
    if args['project_list_components']:
        for pro in args['project_list_components']:
            components = jira_obj.project_components(pro)
            [print(c.id.ljust(10), c.name) for c in components]
        sys.exit(0)

    # print favourite filters for current user
    if args['filter_list_fav']:
        filter_list_print(jira_obj.favourite_filters())
        sys.exit(0)

    # add a label to an issue
    if args['issue_label_add']:
        issue = jira_obj.issue(args['issue_label_add'][0])
        issue.fields.labels.append(args['issue_label_add'][1])
        issue.update(fields={"labels": issue.fields.labels})
        sys.exit(0)

    # remove label from an issue
    if args['issue_label_remove']:
        issue = jira_obj.issue(args['issue_label_remove'][0])
        labels_new = filter(lambda x: x.lower() !=
                            args['issue_label_remove'][1].lower(),
                            issue.fields.labels)
        issue.update(fields={"labels": labels_new})
        sys.exit(0)

    # add component to an issue
    if args['issue_component_add']:
        issue = jira_obj.issue(args['issue_component_add'][0])
        comp = {'name': args['issue_component_add'][1]}
        components_available = [{'name': c.name}
                                for c in issue.fields.components]
        components_available.append(comp)
        issue.update(fields={"components": components_available})
        sys.exit(0)

    # remove component from an issue
    if args['issue_component_remove']:
        issue = jira_obj.issue(args['issue_component_remove'][0])
        components_new = [
            {'name': x.name}
            for x in filter(lambda x: x.name.lower() !=
                            args['issue_component_remove'][1].lower(),
                            issue.fields.components)]
        issue.update(fields={"components": components_new})
        sys.exit(0)

    # add a fixVersion to an issue
    if args['issue_fix_version_add']:
        issue = jira_obj.issue(args['issue_fix_version_add'][0])
        fix_version_new = {'name': args['issue_fix_version_add'][1]}
        fix_versions_available = [
            {'name': c.name} for c in issue.fields.fixVersions]
        fix_versions_available.append(fix_version_new)
        issue.update(fields={"fixVersions": fix_versions_available})
        sys.exit(0)

    # remove fixVersion from an issue
    if args['issue_fix_version_remove']:
        issue = jira_obj.issue(args['issue_fix_version_remove'][0])
        fix_versions_new = [
            {'name': x.name} for x in filter(
                lambda x: x.name.lower() !=
                args['issue_fix_version_remove'][1].lower(),
                issue.fields.fixVersions)]
        issue.update(fields={"fixVersions": fix_versions_new})
        sys.exit(0)

    # move issue(s) to Open state
    if args['issue_trans_open']:
        for i in args['issue_trans_open']:
            jira_obj.transition_issue(i, 3)
            log.debug("moved to open : issue '%s'", i)
        sys.exit(0)

    # move issue(s) to Start Progress state
    if args['issue_trans_start']:
        for i in args['issue_trans_start']:
            jira_obj.transition_issue(i, 4)
            log.debug("moved to progress : issue '%s'", i)
        sys.exit(0)

    # move issue(s) to Start Resolved state
    if args['issue_trans_resolve']:
        for i in args['issue_trans_resolve']:
            # jira_obj.transition_issue(i, 5, assignee={'name': conf['user']},
            # resolution={'id': '1'})
            jira_obj.transition_issue(i, 5, resolution={'id': '1'})
            log.debug("moved to progress : issue '%s'", i)
        sys.exit(0)

    # add watch to issue(s)
    if args['issue_watch_add']:
        for i in args['issue_watch_add']:
            jira_obj.add_watcher(i, conf['user'])
            log.debug("added watch for issue '%s'", i)
        sys.exit(0)

    # remove watch to issue(s)
    if args['issue_watch_remove']:
        for i in args['issue_watch_remove']:
            jira_obj.remove_watcher(i, conf['user'])
            log.debug("removed watch for issue '%s'", i)
        sys.exit(0)

    # add comment to issue
    if args['issue_comment_add']:
        if args['message']:
            comment = args['message'][0]
            print(comment)
        elif args['message_file']:
            fname = args['message_file'][0]
            if os.path.isfile(fname) and os.access(fname, os.R_OK):
                print("File exists and is readable")
                comment = file_get_text(fname)
                print(comment)
            else:
                print("Either file is missing or is not readable")

        else:
            comment = editor_get_text(
                "-- your comment for issue %s" %
                (args['issue_comment_add'][0]))
            print(comment)
        issue = jira_obj.issue(args['issue_comment_add'][0])
        jira_obj.add_comment(issue, comment)
        log.debug("comment added to issue '%s'", args['issue_comment_add'][0])
        sys.exit(0)

    # print issue by filter search
    if args['issue_search_by_filter']:
        searchstring_list = [
            jira_obj.filter(f).jql for f in args['issue_search_by_filter']]
        issue_search_result_print(jira_obj, args, searchstring_list)
        sys.exit(0)

    # create a new issue
    if args['issue_create']:
        # get description from text editor
        desc = editor_get_text("-- describe the issue here")
        issue_dict = {
            'project': {'key': args['issue_create'][0]},
            'issuetype': {'name': args['issue_create'][1]},
            'summary': args['issue_create'][2],
            'description': desc,
        }

        if len(args['issue_create'][3]) > 0:
            issue_dict['labels'] = args['issue_create'][3].split(',')

        if len(args['issue_create'][4]) > 0:
            issue_dict['components'] = [
                {'name': c} for c in args['issue_create'][4].split(',')]

        if args['issue_parent']:
            issue_dict['parent'] = {'id': args['issue_parent']}

        new_issue = jira_obj.create_issue(fields=issue_dict)
        issue_list_print(jira_obj, [new_issue], True, True, False, False)
        sys.exit(0)

    # create multiple new issues from file
    if args['issues_create']:
        # parent key (ie PROJECT-1234)
        parent_id = None

        if args['issue_parent']:
            parent_id = args['issue_parent']

        with open(args['issues_create'][3], "r") as f:
            for n in f.readlines():
                is_subtask = False
                # ignore empty lines
                if len(n) == 0:
                    continue

                issue_dict = {
                    'project': {'key': args['issues_create'][0]},
                }

                if n.lstrip().startswith("*") or n.lstrip().startswith("-"):
                    #  this is a subtask
                    issue_dict['parent'] = {'id': parent_id}
                    issue_dict['issuetype'] = {
                        'name': args['issues_create'][2]}
                    issue_dict['summary'] = n.lstrip()[1:]
                    is_subtask = True
                else:
                    # this is a task without a parent
                    issue_dict['issuetype'] = {
                        'name': args['issues_create'][1]}
                    issue_dict['summary'] = n

                # create and print the new issue
                new_issue = jira_obj.create_issue(fields=issue_dict)
                issue_list_print(jira_obj, [new_issue], True, True, False)
                if not is_subtask:
                    parent_id = new_issue.key

        sys.exit(0)

    # print issue search results
    if args['issue_search']:
        issue_search_result_print(jira_obj, args, args['issue_search'])
        sys.exit(0)

    if args['sprint']:
        sprint(jira_obj, args['sprint'][0])
        sys.exit(0)

    # print issue(s) and exit
    if args['issue']:
        issues = [jira_obj.issue(i) for i in args['issue']]
        issue_list_print(
            jira_obj,
            issues, args['issue_desc'], args['issue_comments'],
            args['issue_trans'], args['issue_oneline'])
        sys.exit(0)


if __name__ == "__main__":
    main()
