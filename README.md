# Jira command line interface
`jiracli` is a simple command line interface based on the `jira-python` module. The module uses the REST API to communicate with the Jira instance.

## Installation
`python2.7` and `jira-python` from https://pypi.python.org/pypi/jira-python/ is needed.

## Configuration
During the first run, `jiracli` asks for username, password and Jira url. All values are stored in `~/.jiracli.ini`.

## Usage
Try the help with:

	./jiracli -h

### Example: show a single issue:

	./jiracli -i PROJECT-3535
	PROJECT-3535, Prod Bug: This is a terrible bug. (Created, Low)
	created              : Thu Oct 24 09:30:35 2013, by t.bechtold
	assignee             : t.bechtold
	updated              : Fri Nov  8 15:56:27 2013
	components           : SITE:XYZ
	labels               : mylabel
	attachment           : 

You can also provide a list of issues. Then all issues will be printed. To also see the description of the issue(s), use `--issue-desc`. To list the comments, use `--issue-comments`. For a short overview (online per issue), use `--issue-oneline`.

### Example: use favourite filters
To see the favourite filters of the currently logged in user, do:

	$ ./jiracli --filter-list-fav
	23905, t.bechtold PROJECT bugs
	Url                  : https://example.com/jira/secure/IssueNavigator.jspa?mode=hide&requestId=23905
	description          : Bugs of t.bechtold in project PROJECT
	owner                : t.bechtold
	jql                  : project = PROJECT AND asignee = t.bechtold

The number `23905` in the filter head line is the filter-id. This id is used to search the issues for this filter:

	./jiracli --issue-search-by-filter 23905

This command simply executes the search string given by the filter.

### Searching with jql
Useing the Jira query language to search is simple:

	./jiracli --issue-search "assignee=CurrentUser() and status='Closed'" --issue-comment

This command searches for all closed issues of the currently logged in user. The command also prints the comments for every issue.

