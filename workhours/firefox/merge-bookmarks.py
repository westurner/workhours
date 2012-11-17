#!/usr/bin/env python

"""
Merge each bookmark file named into one written to <stdout>.

Duplicate lines are removed, and references are sorted within sections.
"""

USAGE = "Usage: %s bookmarks.html ... >merged-bookmarks.html\n"
OptUsage = "?"
OptLongUsage = ['help']


import getopt, os, sys
import sgmllib, string


def usage(reason=''):

	""" Argument usage message. """

	sys.stdout.flush()
	if reason: sys.stderr.write('\t%s\n\n' % reason)
	head, tail = os.path.split(sys.argv[0])
	sys.stderr.write(USAGE % tail)
	sys.stderr.write(__doc__)
	sys.exit(1)


def syserror(type, name, reason):
	sys.stderr.write("Can't %s \"%s\" - %s\n" % (type, name, reason))
	sys.exit(2)


def warn(reason):
	sys.stderr.write("%s\n" % reason)



class BookMarksFormatter:

	# Netscape bookmark files are some preamble and a nested list of DL lists.

	def __init__(self):
		self.comment, self.title, self.h1 = ('',)*3
		self.h3 = ['', '']
		self.document = []	# [[name, attrs, desc|sub_list], ...]
		self.current = None
		self.level = 0
		self.last = None
		self.push(self.document)

	def push(self, new):
		self.last = [self.current, self.level, self.last]
		self.level = self.level + 1
		self.current = new

	def pop(self):
		self.current, self.level, self.last = self.last


	def new_comment(self, data):
		self.comment = data

	def new_title(self, attrs, data):
		assert not attrs, "Unexpected TITLE attributes: %s!" % attrs
		self.title = data

	def new_h1(self, attrs, data):
		assert not attrs, "Unexpected H1 attributes: %s!" % attrs
		self.h1 = data

	def new_h3(self, attrs, data):
		self.h3 = [data, attrs]


	def start_dl(self, attrs):
		assert not attrs, "Unexpected DL attributes: %s!" % attrs
		new = []
		self.current.append(self.h3 + [new])
		self.push(new)

	def new_dt(self, attrs):
		assert not attrs, "Unexpected DL attributes: %s!" % attrs

	def end_dl(self):
		self.pop()


	def new_a(self, attrs, data):
		data = string.replace(data, "&amp;#39;", "'")	# Fix netscape bug
		data = string.replace(data, "&amp;", "&")	# Fix netscape bug
		self.current.append([data, attrs, ''])

	def new_dd(self, attrs, data):
		assert not attrs, "Unexpected DD attributes: %s!" % attrs
		if not self.current:
			# Comment for folder
			sys.stderr.write('new_dd for folder: %s' % `self.h3`)
			self.h3[1] = self.h3[1] + [('description', data)]
		else:
			assert not self.current[-1][2], "Unexpected DD: %s!" % data
			self.current[-1][2] = data



class BookMarksParser(sgmllib.SGMLParser):

	def __init__(self, formatter):
		self.formatter = formatter
		self.savedata = ''
		self.dd = 0
		sgmllib.SGMLParser.__init__(self)

	def save_bgn(self, attrs):
		self.savedata = ''
		self.attrs = attrs
	def handle_data(self, data):
		self.savedata = self.savedata + data
	def handle_entityref(self, name):	# Just pass these through unchanged
		self.savedata = self.savedata + '&' + name + ';'
	def save_end(self, join=string.join, split=string.split):
		data = join(split(self.savedata))
		self.savedata = ''
		return data

	def handle_comment(self, data):
		self.formatter.new_comment(data)

	def start_title(self, attrs):
		self.save_bgn(attrs)
	def end_title(self):
		self.formatter.new_title(self.attrs, self.save_end())

	def start_h1(self, attrs):
		self.save_bgn(attrs)
	def end_h1(self):
		self.formatter.new_h1(self.attrs, self.save_end())

	def start_h3(self, attrs):
		self.save_bgn(attrs)
	def end_h3(self):
		self.formatter.new_h3(self.attrs, self.save_end())

	def do_p(self, attrs):
		pass

	def start_dl(self, attrs):
		self.formatter.start_dl(attrs)
	def do_dt(self, attrs):
		self.end_dd()
		self.formatter.new_dt(attrs)
	def start_dd(self, attrs):
		self.save_bgn(attrs)
		self.dd = 1
	def end_dd(self):
		if self.dd:
			self.formatter.new_dd(self.attrs, self.save_end())
			self.dd = 0
	def end_dl(self):
		self.end_dd()
		self.formatter.end_dl()

	def start_a(self, attrs):
		self.attrs = attrs
		self.save_bgn(attrs)
	def end_a(self):
		self.formatter.new_a(self.attrs, self.save_end())

	def unknown_starttag(self, tag, attrs):
		warn('unknown start tag <%s>' % tag)
	def unknown_endtag(self, tag, attrs):
		warn('unknown end tag </%s>' % tag)
	def unknown_charref(self, ref):
		warn('unknown char ref &#%s;' % ref)
	def unknown_entityref(self, ref):
		warn('unknown entity ref &%s;' % ref)



class BookMarksMerge:

	def __init__(self):
		self.bookmarkfiles = []


	def addfile(self, file):
		fd = open(file, 'r')
		data = fd.read()
		fd.close()
		formatter = BookMarksFormatter()
		self.parser = BookMarksParser(formatter)
		self.parser.feed(data)
		self.parser.close()
		self.bookmarkfiles.append([formatter.comment, formatter.title, formatter.h1, formatter.document])


	def merge(self):
		c1,t1,h1,l1 = self.bookmarkfiles[0]
		self.sort_file(l1)
		for c2,t2,h2,l2 in self.bookmarkfiles[1:]:
			self.sort_file(l2)
			self.merge_files(l1, l2)


	def merge_files(self, l1, l2, list_type = type([])):

		# Merge l2 into l1

		# At each level, choose latest of two equal keys/Anchors

		i,j = 0,0
		len1,len2 = len(l1),len(l2)
		merged = []

		while i < len1:
			n1,a1,d1 = l1[i]
			while j < len2:
				n2,a2,d2 = l2[j]
				r = cmp(n1, n2)
				if r == 0:	# Same name
					if type(d1) is list_type and type(d2) is list_type:
						self.merge_files(d1, d2)
					t1 = extract_attr('last_visit', a1)
					t2 = extract_attr('last_visit', a2)
					if t1 is not None and t2 is not None and t2 > t1:
						a1 = a2	# Take latest visited attributes
					j = j+1
					break
				if r < 0:	# New in l1
					break
				# New in l2
				merged.append([n2,a2,d2])
				j = j+1
			merged.append([n1,a1,d1])
			i = i+1

		# Add tail of 2nd list

		while j < len2:
			merged.append(l2[j])
			j = j+1

		# Remove duplicates

		len1 = len(merged)
		if len1 > 1:
			dups = []; da = dups.append
			n1 = merged[0][0]
			for i in range(1, len1):
				n2 = merged[i][0]
				if n1 != n2:
					n1 = n2
					continue
				n1 = n2
				h1 = extract_attr('href', merged[i-1][1])
				h2 = extract_attr('href', merged[i][1])
				if h1 is not None and h2 is not None and h2 != h1:
					continue
				t1 = extract_attr('last_visit', merged[i-1][1])
				t2 = extract_attr('last_visit', merged[i][1])
				if t1 is not None and t2 is not None and t2 > t1:
					da(i-1)	# Remove older duplicate
				else:
					da(i)	# Remove 2nd of two equal duplicates

			dups.reverse()
			for i in dups:
				del merged[i]

		l1[:] = merged


	def sort_file(self, l, list_type = type([])):

		# Sort list and sub-lists

		l.sort()

		for name,attrs,data in l:
			if type(data) is list_type:
				self.sort_file(data)


	def write(self, fd):

		# Merge self.bookmarks list.

		self.merge()

		# Write out self.bookmarks list.

		self.write2fd = fd.write

		self.write2fd('<!DOCTYPE NETSCAPE-Bookmark-file-1>\n')

		comment, title, h1, bookmarks = self.bookmarkfiles[0]

		self.write2fd('<!--%s-->\n' % comment)
		self.write2fd('<TITLE>%s</TITLE>\n' % title)
		self.write2fd('<H1>%s</H1>\n\n' % h1)

		self.write_list(0, bookmarks)


	def write_list(self, level, l, list_type = type([])):

		# Write out elements in order

		indent = '    '*level
		write2fd = self.write2fd

		for name,attrs,data in l:
			if type(data) is list_type:	# DL
				if name:
					desc = extract_attr('description', attrs)
					if desc is not None:
						attrs = remove_attr('description', attrs)
					write2fd('%s<DT><H3%s>%s</H3>\n'
						% (indent, attrs2str(attrs), name))
					if desc:
						write2fd('%s<DD>%s\n' % (indent, desc))
				write2fd('%s<DL><p>\n' % indent)
				self.write_list(level+1, data)	# Recurse down one level
				write2fd('%s</DL><p>\n' % indent)
				continue

			# Anchor

			write2fd('%s<DT><A%s>%s</A>\n'
				% (indent, attrs2str(attrs), name))
			if data:
				write2fd('%s<DD>%s\n' % (indent, data))



def main():

	try:
		optlist, args = getopt.getopt(sys.argv[1:], OptUsage, OptLongUsage)
	except getopt.error, val:
		usage(val)

	for opt,val in optlist:
		usage()

	if len(args) < 1:
		usage()

	b = BookMarksMerge()

	for file in args:
		if not os.path.isfile(file):
			usage('%s should be the name of a bookmarks file' % file)
		b.addfile(file)

	b.write(sys.stdout)

	return 0



def attrs2str(attrs, upper=string.upper):
	l = []; a = l.append; a('')	# Ensure leading space if attrs non-null
	for name, value in attrs:
		if name == value:
			a(upper(name))
		else:
			a('%s="%s"' % (upper(name), value))
	return string.join(l)



def extract_attr(name, attrs):
	for nam,val in attrs:
		if name == nam:
			return val
	return None



def remove_attr(name, attrs):
	new = []; newa = new.append
	for nam,val in attrs:
		if name == nam:
			continue
		newa((nam, val))
	return new



if __name__ == '__main__':

	sys.exit(main() or 0)
