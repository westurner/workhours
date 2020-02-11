#!/usr/bin/env python

def main(*args, **kwargs):
    import os
    this_file='%s/bin/activate_this.py' % os.environ['VIRTUAL_ENV']
    exec(compile(open(this_file, "rb").read(), this_file, 'exec'), dict(__file__=this_file))

    from paste.script.serve import ServeCommand

    ServeCommand("serve") #.run(["development.ini"])

if __name__=="__main__":
    main()
