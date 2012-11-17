#!/usr/bin/python

def main():
    from BeautifulSoup import BeautifulSoup as BS

    b = BS(file("bookmarks.html").read())


    print '\n'.join(map(lambda x: "== %s ==\n%s\n" % (urllib.unquote_plus(x.string), urllib.unquote_plus(x.get('href'))), filter(lambda x: x.string.startswith("&quot"), b.findAll("a"))))

if __name__=="__main__":
    main()
