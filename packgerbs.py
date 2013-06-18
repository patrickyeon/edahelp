#!/usr/bin/python

import os
from zipfile import ZipFile

def fileExt(filepath):
    return filepath.rsplit(os.extsep, 1)[-1]
def fileName(filepath):
    return filepath.rsplit(os.sep, 1)[-1]
def fileBase(filepath):
    return fileName(filepath).rsplit(os.extsep, 1)[0]

class readable:
    def __init__(self, inbuff):
        self.buff = inbuff
        if type(self.buff) == str:
            self.readline = self._readline_str
        elif type(self.buff) == file:
            self.readline = self.buff.readline

    def _readline_str(self):
        if len(self.buff) > 0:
            splits = self.buff.split('\n', 1)
            ret = splits[0] + '\n'
            if len(splits) > 0:
                self.buff = splits[1]
            else:
                self.buff = ''
        return ret

class gerber:
    def __init__(self):
        self.lines = []
        self.started = False
        # TODO add in a 'prelude'?
        self.params = dict([(cmd, None) for cmd in '%FS %MO %IP %IN'.split()])

    def extend(self, string_or_file):
        if self.started:
            if self.lines[-1] == 'M02*\n':
                # this is an EOF, remove it
                del self.lines[-1]
            # end any old step-and-repeat command from the prev. file
            self.lines.append('%SRX1Y1*%\n')
            # reset level polarity to dark (also sets current point to (0,0))
            self.lines.append('%LPD*%\n')
            # reset region mode to off
            self.lines.append('G37*\n')

        buff = readable(string_or_file)
        cmd = buff.readline()
        while cmd != '':
            if not self.started:
                if cmd[:3] in self.params:
                    # keep track of params so that we can make sure the next
                    # file added has the same
                    self.params[cmd[:3]] = cmd
                # just pass through the first file
                self.lines.append(cmd)
            elif cmd[:3] in self.params:
                if self.params[cmd[:3]] != cmd:
                    raise Exception('Gerber file parameter clash')
            elif cmd.startswith('%LP'):
                raise Exception('Gerber level polarity not supported (yet)')
            else:
                self.lines.append(cmd)
            cmd = buff.readline()
        self.started = True
        if not self.lines[-1].startswith('M'):
            self.lines.append('M02*\n')

    def asString(self):
        return ''.join(self.lines)

class boardfab:
    extMap, merges = {}, {}
    def __init__(self, gerbfiles, drillfiles):
        self.infiles = gerbfiles
        self.drills = drillfiles

    def output(self, outfilename, overwrite=False):
        if not outfilename.endswith('.zip'):
            outfilename = outfilename + '.zip'
        if not overwrite and os.access(outfilename, os.F_OK):
            # file exists already
            raise Exception('will not overwrite existing file')
        outfile = ZipFile(outfilename, 'w')

        infiles = {}
        for f in self.infiles:
            ext = fileExt(f)
            if ext in infiles:
                raise Exception('File extension clash: %s' % f)
            infiles[ext] = f
        
        for ext in self.extMap:
            if ext in infiles:
                name = infiles[ext]
                outfile.write(name, fileBase(fileName(name)) + '.'
                                    + self.extMap[ext])

        for outGerb, sources in self.merges.items():
            gerb = gerber()
            name = ''
            for ext in sources:
                if ext in infiles:
                    gerb.extend(open(infiles[ext]))
                    name = fileBase(fileName(infiles[ext]))
            if name != '':
                outfile.writestr(name + '.' + outGerb, gerb.asString())
        for f in self.drills:
            outfile.write(f, fileName(f))
        outfile.close()

class sierra(boardfab):
    extMap = {'GTO': 'topSilk',
              'GBO': 'botSilk',
              'GTL': 'topCopper',
              'GBL': 'botCopper',
              'GBS': 'botSolder'}
    merges = {'topSolder': ['GTS', 'GM6']}

class oshpark(boardfab):
    extMap = dict([(ext, ext) for ext in 'GTL GBL GTS GBS GTO GBO'.split()]
                  + [('GM6', 'GKO')])

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--prefix', help='prefix for design being used')
    parser.add_argument('--drilldir', help='directory to find drill files')
    parser.add_argument('-o', '--outfile', help='file to save output to',
                        required=True)
    parser.add_argument('indir', help='directory to find the gerber files')

    args = parser.parse_args()

    def directorize(direc):
        if not direc.endswith(os.sep):
            return direc + os.sep
        return direc
    
    indir = directorize(args.indir) 

    # TODO this next bit is all shit. Make it less so.
    gerbfiles = [indir + f for f in os.listdir(indir)]
    drillfiles = []
    drilldir = args.drilldir
    if drilldir is not None:
        drilldir = directorize(args.drilldir)
        drillfiles = [drilldir + f for f in os.listdir(drilldir)
                      if f[-3:] in ('txt', 'TXT')]
    if args.prefix is not None:
        gerbfiles = [f for f in filelist
                    if fileName(f).startswith(args.prefix + '.')]
        drillfiles = [f for f in drillfiles
                    if fileName(f).startswith(args.prefix)]

    # for now, hardcode sierra as the target
    pack = sierra(gerbfiles, drillfiles)
    pack.output(args.outfile)
