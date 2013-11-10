Jira command line interface
===========================
`jiracli` is a simple command line interface based on the `jira-python` module. The module uses the REST API to communicate with the Jira instance.

Installation
============
`python2.7` and `jira-python` from https://pypi.python.org/pypi/jira-python/ is needed.

 * You can install `jiracli` with pip in a virtual environment::

     virtualenv myenv
     source myenv/bin/activate
     pip install jiracli

 * or without an virtual env::

     pip install jiracli

 * or directly from the extracted source::

     python setup.py install

Configuration
=============
During the first run, `jiracli` asks for username, password and Jira url. All values are stored in `~/.jiracli.ini`.

Usage
=====
Try the help with::

  ./jiracli -h

Example: create a new issue:
----------------------------
The following command creates a new issue for the project PROJECT. Issue type is `Dev Bug`, labels are `abc` and `def` and components are `xxx` and `yyyy`::

  ./jiracli  -c PROJECT "Dev Bug" "my test summary" "abc,def" "xxx,yyyy"


Example: show a single issue:
-----------------------------
The following command prints a single issue::

  ./jiracli -i PROJECT-3535
  PROJECT-3535, Prod Bug: This is a terrible bug. (Created, Low)
  created              : Thu Oct 24 09:30:35 2013, by t.bechtold
  assignee             : t.bechtold
  updated              : Fri Nov  8 15:56:27 2013
  components           : SITE:XYZ
  labels               : mylabel
  attachment           : 

You can also provide a list of issues. Then all issues will be printed. To also see the description of the issue(s), use `--issue-desc`. To list the comments, use `--issue-comments`. For a short overview (online per issue), use `--issue-oneline`.

Example: use favourite filters
------------------------------

To see the favourite filters of the currently logged in user, do::

  $ ./jiracli --filter-list-fav
  23905, t.bechtold PROJECT bugs
  Url                  : https://example.com/jira/secure/IssueNavigator.jspa?mode=hide&requestId=23905
  description          : Bugs of t.bechtold in project PROJECT
  owner                : t.bechtold
  jql                  : project = PROJECT AND asignee = t.bechtold

The number `23905` in the filter head line is the filter-id. This id is used to search the issues for this filter::

  ./jiracli --issue-search-by-filter 23905

This command simply executes the search string given by the filter.

Example: Searching with jql
---------------------------

Useing the Jira query language to search is simple::

  ./jiracli --issue-search "assignee=CurrentUser() and status='Closed'" --issue-comment

This command searches for all closed issues of the currently logged in user. The command also prints the comments for every issue.

Example: Add and remove issue watchers
--------------------------------------

To get informed if something changed on an issue, there are watchers. The following commands add and remove a watch::

  ./jiracli --issue-watch-add PROJECT-1234
  ./jiracli --issue-watch-remove PROJECT-1234

Example: Add and remove labels
------------------------------

Adding and removing labels is simple. First add a label called `testlabel` and then remove it::

  ./jiracli --issue-label-add PROJECT-3724 "testlabel"
  ./jiracli --issue-label-remove PROJECT-3724 "testlabel"

Example: Add and remove components
----------------------------------
A list of available components for a given project is available with::

  ./jiracli  --project-list-components PROJECT

Now add and remove a component from the given list to an issue::

  ./jiracli --issue-component-add PROJECT-1234 "COMP1"
  ./jiracli --issue-component-remove PROJECT-1234 "COMP1"

Example: Add a comment to an issue
----------------------------------
The following command open a text editor to insert the comment::

  ./jiracli --issue-comment-add PROJECT-3724

The short form is::

  ./jiracli --issue-comment-add PROJECT-3724 -m "another comment"
