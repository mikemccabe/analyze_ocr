import iabook

opts = None

def main(argv):
    import optparse
    parser = optparse.OptionParser()
    parser = optparse.OptionParser(usage='usage: %prog [options]',
                                   version='%prog 0.1',
                                   description='A visualizer for '
                                   'coordinate-annotated OCR data.')
    parser.add_option('--reduce',
                      action='store',
                      type='int',
                      metavar='n',
                      default=2,
                      help='For jp2 input images, reduce jp2 resolution '
                      'by 2 ^ n when reading '
                      'original image, for speed.  This also reduces the '
                      'output scale by 2 ^ n, unless otherwise specified '
                      'with --scale.')
    parser.add_option('--scale',
                      action='store',
                      type='int',
                      default=0,
                      help='Scale result images down from original scan '
                      'resolution.')
    parser.add_option('--last',
                      action='store',
                      type='int',
                      metavar='leaf',
                      default=0,
                      help='Stop generating output leaves '
                      'after the specified leaf')
    parser.add_option('--first',
                      action='store',
                      type='int',
                      metavar='leaf',
                      default=0,
                      help='Don\'t generate output leaves until the '
                      'specified leaf')
    parser.add_option('--leaf',
                      action='store',
                      type='int',
                      metavar='leaf',
                      default=0,
                      help='Only generate output for the specified leaf')
    parser.add_option('--text',
                      action='store_true',
                      default=False,
                      help='Generate output characters for OCRed '
                      'text in input files')
    parser.add_option('--outdir',
                      help='Output directory.  Default is source_type + \'_viz\'')
    parser.add_option('--source',
                      choices=['abbyy', 'pdftoxml', 'djvu'],
                      default='abbyy',
                      help='Which source to use for OCR data/coordinates.')
    parser.add_option('--show-opts',
                      action='store_true',
                      # help=optparse.SUPPRESS_HELP
                      help='Display parsed options/defaults and exit')
    global opts
    opts, args = parser.parse_args(argv)
    if opts.reduce < 0 or opts.reduce > 4:
        parser.error('--reduce must be between 0 and 4')
    if opts.scale == 0:
        opts.scale = 2 ** opts.reduce

    if opts.leaf != 0:
        if opts.first > 0 or opts.last > 0:
            parser.error('can\'t specify --last or --first with --leaf')
        opts.last = opts.first = opts.leaf

    if opts.source == 'djvu':
        parser.error('--source=djvu not supported at the moment')

    if opts.outdir is None:
        opts.outdir = opts.source + '_viz'

    if opts.show_opts:
        print 'Options: ' + str(opts)
        print 'Args: ' + str(args)
        sys.exit(0)

    parser.destroy()

    if not os.path.isdir('./' + opts.outdir + '/'):
        os.mkdir('./' + opts.outdir + '/')

    iabook = iarchive.Book(id, '', id)
    visualize(iabook, opts)


def visualize(iabook, opts):
    for page in iabook.get_pages_as_djvu():


if __name__ == '__main__':
    main(sys.argv[1:])
